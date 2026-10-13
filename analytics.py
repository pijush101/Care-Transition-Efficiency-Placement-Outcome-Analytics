"""
analytics.py - Care Transition Efficiency & Placement Outcome Analytics
Shared engine for the UAC pipeline project (CBP custody -> HHS care -> sponsor discharge).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

RAW_COLS = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "apprehended",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "transferred",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "discharged",
}
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# --------------------------------------------------------------------------- #
# 1. Load & clean
# --------------------------------------------------------------------------- #
def load_data(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df = df.dropna(how="all").rename(columns=RAW_COLS)
    df["date"] = pd.to_datetime(df["date"])
    for c in ["apprehended", "cbp_custody", "transferred", "hhs_care", "discharged"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["date"]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df["gap_days"] = df["date"].diff().dt.days
    df["dow"] = df["date"].dt.dayofweek
    df["dow_name"] = df["dow"].map(dict(enumerate(DAY_NAMES)))
    df["after_gap"] = df["gap_days"] > 1          # record follows an unreported day(s)
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    return df


# --------------------------------------------------------------------------- #
# 2. Derived process metrics (record level)
# --------------------------------------------------------------------------- #
def add_metrics(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    d = df.copy()
    eps = 1e-9
    # Transfer Efficiency Ratio: share of CBP load moved out per day
    d["ter"] = d["transferred"] / d["cbp_custody"].clip(lower=1)
    # Discharge Effectiveness Index: share of HHS load discharged per day
    d["dei"] = d["discharged"] / d["hhs_care"].clip(lower=1)
    # Stage throughput
    d["cbp_throughput"] = d["transferred"] / d["apprehended"].clip(lower=1)
    d["hhs_throughput"] = d["discharged"] / d["transferred"].clip(lower=1)
    # Net flows = backlog accumulation (positive = backlog building)
    d["cbp_net_flow"] = d["apprehended"] - d["transferred"]
    d["hhs_net_flow"] = d["transferred"] - d["discharged"]
    # Implied dwell / length of stay via Little's Law (stock / daily outflow), rolling
    roll = lambda s: s.rolling(window, min_periods=max(5, window // 2)).mean()
    d["cbp_dwell_days"] = roll(d["cbp_custody"]) / roll(d["transferred"]).clip(lower=1)
    d["hhs_los_days"] = roll(d["hhs_care"]) / roll(d["discharged"]).clip(lower=1)
    # Rolling flow sums for end-to-end throughput
    d["e2e_throughput"] = roll(d["discharged"]) / roll(d["apprehended"]).clip(lower=1)
    # Backlog accumulation rate: % change in HHS census over a trailing window
    d["hhs_backlog_rate"] = d["hhs_care"].pct_change(window)
    d["cbp_backlog_rate"] = d["cbp_custody"].pct_change(window)
    # Outcome Stability Score: 100 / (1 + CV) of rolling discharge rate, so 100 = perfectly steady
    mu = d["discharged"].rolling(28, min_periods=14).mean()
    sd = d["discharged"].rolling(28, min_periods=14).std()
    d["oss"] = 100.0 / (1.0 + sd / (mu + eps))
    return d


# --------------------------------------------------------------------------- #
# 3. Period summaries
# --------------------------------------------------------------------------- #
def period_summary(d: pd.DataFrame, by: str = "quarter") -> pd.DataFrame:
    g = d.groupby(by)
    out = pd.DataFrame({
        "records": g.size(),
        "avg_apprehended": g["apprehended"].mean(),
        "avg_transferred": g["transferred"].mean(),
        "avg_discharged": g["discharged"].mean(),
        "avg_cbp_custody": g["cbp_custody"].mean(),
        "avg_hhs_care": g["hhs_care"].mean(),
    })
    out["ter"] = out["avg_transferred"] / out["avg_cbp_custody"]
    out["dei"] = out["avg_discharged"] / out["avg_hhs_care"]
    out["cbp_throughput"] = out["avg_transferred"] / out["avg_apprehended"]
    out["hhs_throughput"] = out["avg_discharged"] / out["avg_transferred"]
    out["cbp_dwell_days"] = out["avg_cbp_custody"] / out["avg_transferred"]
    out["hhs_los_days"] = out["avg_hhs_care"] / out["avg_discharged"]
    out["net_hhs_flow"] = out["avg_transferred"] - out["avg_discharged"]
    out["discharge_cv"] = g["discharged"].std() / g["discharged"].mean()
    out["oss"] = 100 / (1 + out["discharge_cv"])
    # Count-noise benchmark: a pure Poisson process has CV = 1/sqrt(mean). Ratio > 1 = excess volatility.
    out["cv_over_poisson"] = out["discharge_cv"] * np.sqrt(out["avg_discharged"])
    return out.replace([np.inf, -np.inf], np.nan)


def monthly_trends(d: pd.DataFrame) -> pd.DataFrame:
    m = period_summary(d, "month")
    m["discharged_total_est"] = m["avg_discharged"] * m.index.days_in_month  # run-rate estimate
    m["mom_discharge_pct"] = m["avg_discharged"].pct_change() * 100
    m["mom_dei_pct"] = m["dei"].pct_change() * 100
    return m


# --------------------------------------------------------------------------- #
# 4. Temporal patterns
# --------------------------------------------------------------------------- #
def dow_profile(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("dow_name")
    out = g[["apprehended", "transferred", "discharged", "ter", "dei"]].mean()
    out["n"] = g.size()
    return out.reindex([x for x in DAY_NAMES if x in out.index])


def after_gap_effect(d: pd.DataFrame) -> pd.DataFrame:
    """Do records following an unreported day carry larger flows (batch reporting)?"""
    g = d.groupby("after_gap")[["apprehended", "transferred", "discharged"]].mean()
    g.index = g.index.map({False: "Consecutive day", True: "After unreported day(s)"})
    return g


# --------------------------------------------------------------------------- #
# 5. Bottleneck & stagnation detection
# --------------------------------------------------------------------------- #
def _episodes(mask: pd.Series, dates: pd.Series, min_len: int) -> list[tuple]:
    eps, start = [], None
    m = mask.fillna(False).to_numpy()
    for i, flag in enumerate(m):
        if flag and start is None:
            start = i
        if (not flag or i == len(m) - 1) and start is not None:
            end = i if flag else i - 1
            if end - start + 1 >= min_len:
                eps.append((dates.iloc[start], dates.iloc[end], end - start + 1))
            start = None
    return eps


def sustained_imbalance(d: pd.DataFrame, stage: str = "hhs", window: int = 14,
                        min_len: int = 14, tol: float = 0.0) -> pd.DataFrame:
    """Periods where rolling inflow exceeds rolling outflow for >= min_len consecutive records."""
    if stage == "hhs":
        inflow, outflow = d["transferred"], d["discharged"]
    else:
        inflow, outflow = d["apprehended"], d["transferred"]
    net = inflow.rolling(window, min_periods=window).mean() - outflow.rolling(window, min_periods=window).mean()
    eps = _episodes(net > tol, d["date"], min_len)
    rows = []
    for s, e, n in eps:
        seg = d[(d["date"] >= s) & (d["date"] <= e)]
        census_col = "hhs_care" if stage == "hhs" else "cbp_custody"
        rows.append({"start": s, "end": e, "records": n,
                     "avg_net_inflow": (seg["transferred"] - seg["discharged"]).mean() if stage == "hhs"
                     else (seg["apprehended"] - seg["transferred"]).mean(),
                     "census_start": seg[census_col].iloc[0], "census_end": seg[census_col].iloc[-1]})
    return pd.DataFrame(rows)


def stagnation_periods(d: pd.DataFrame, dei_pctile: float = 0.25, min_len: int = 14) -> pd.DataFrame:
    """Prolonged periods where the discharge rate sits in the bottom quartile of history."""
    thr = d["dei"].quantile(dei_pctile)
    smooth = d["dei"].rolling(7, min_periods=4).mean()
    eps = _episodes(smooth < thr, d["date"], min_len)
    rows = []
    for s, e, n in eps:
        seg = d[(d["date"] >= s) & (d["date"] <= e)]
        rows.append({"start": s, "end": e, "records": n, "avg_dei": seg["dei"].mean(),
                     "avg_hhs_care": seg["hhs_care"].mean(), "avg_discharged": seg["discharged"].mean()})
    return pd.DataFrame(rows)


def sudden_drops(d: pd.DataFrame, short: int = 7, long: int = 28, drop_pct: float = 0.35) -> pd.DataFrame:
    """Flag records where the 7-record mean discharge falls >drop_pct below the prior 28-record mean."""
    s = d["discharged"].rolling(short, min_periods=short).mean()
    base = d["discharged"].shift(short).rolling(long, min_periods=long).mean()
    chg = s / base - 1
    flag = chg < -drop_pct
    # collapse consecutive flags to the first date of each episode
    first = flag & ~flag.shift(fill_value=False)
    out = d.loc[first, ["date", "discharged", "hhs_care"]].copy()
    out["drop_vs_prior_28"] = chg[first]
    return out.reset_index(drop=True)


def regime_table(d: pd.DataFrame) -> pd.DataFrame:
    """Operating regimes by apprehension intensity (rolling 28-record mean)."""
    a = d["apprehended"].rolling(28, min_periods=14).mean()
    labels = pd.cut(a, bins=[-1, 20, 75, 1e9], labels=["Low (<20/day)", "Moderate (20-75/day)", "High (>75/day)"])
    out = d.assign(regime=labels).groupby("regime", observed=True).agg(
        records=("date", "size"), avg_apprehended=("apprehended", "mean"),
        avg_cbp_custody=("cbp_custody", "mean"), avg_hhs_care=("hhs_care", "mean"),
        avg_transferred=("transferred", "mean"), avg_discharged=("discharged", "mean"))
    out["ter"] = out["avg_transferred"] / out["avg_cbp_custody"]
    out["dei"] = out["avg_discharged"] / out["avg_hhs_care"]
    out["hhs_los_days"] = out["avg_hhs_care"] / out["avg_discharged"]
    return out


# --------------------------------------------------------------------------- #
# 6. Data-quality diagnostics
# --------------------------------------------------------------------------- #
def reconciliation(d: pd.DataFrame) -> dict:
    """How well do flows explain day-to-day stock changes? (consecutive-day pairs only)"""
    c = d[d["gap_days"] == 1].copy()
    c["d_hhs"] = d["hhs_care"].diff().loc[c.index]
    c["d_cbp"] = d["cbp_custody"].diff().loc[c.index]
    return {
        "pairs": len(c),
        "hhs_corr": float(c["d_hhs"].corr(c["transferred"] - c["discharged"])),
        "cbp_corr": float(c["d_cbp"].corr(c["apprehended"] - c["transferred"])),
        "hhs_residual_mean": float((c["d_hhs"] - (c["transferred"] - c["discharged"])).mean()),
    }


def data_quality(d: pd.DataFrame) -> dict:
    full = pd.date_range(d["date"].min(), d["date"].max(), freq="D")
    return {"records": len(d), "start": d["date"].min(), "end": d["date"].max(),
            "calendar_days": len(full), "unreported_days": len(full) - len(d),
            "friday_saturday_records": int(d["dow"].isin([4, 5]).sum())}


def alerts(d: pd.DataFrame, ter_min: float, dei_min: float, backlog_max: float, oss_min: float) -> pd.DataFrame:
    """Row-level threshold breaches for the dashboard alert layer."""
    a = pd.DataFrame({"date": d["date"]})
    a["Low transfer efficiency"] = d["ter"] < ter_min
    a["Low discharge effectiveness"] = d["dei"] < dei_min
    a["HHS backlog growing"] = d["hhs_backlog_rate"] > backlog_max
    a["Unstable outcomes"] = d["oss"] < oss_min
    return a
