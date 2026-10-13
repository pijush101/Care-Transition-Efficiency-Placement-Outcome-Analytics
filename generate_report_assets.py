"""generate_report_assets.py - builds figures + tables used in the research paper.  Run: python generate_report_assets.py"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import analytics as an

OUT = "figures"; os.makedirs(OUT, exist_ok=True)
NAVY, BLUE, ORANGE, RED, GREEN, GREY = "#1B2A49", "#2E75B6", "#E8833A", "#C0392B", "#2E8B57", "#8A94A6"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

d = an.add_metrics(an.load_data("HHS_Unaccompanied_Alien_Children_Program.csv")).set_index("date", drop=False)
r = lambda s, n=14: s.rolling(n, min_periods=5).mean()
shift = pd.Timestamp("2025-02-11")

# Fig 1 - pipeline flows & census
fig, ax = plt.subplots(2, 1, figsize=(8, 5.4), sharex=True)
for c, n, col in [("apprehended", "Apprehended", GREY), ("transferred", "Transferred CBP→HHS", BLUE), ("discharged", "Discharged from HHS", GREEN)]:
    ax[0].plot(d.index, r(d[c]), label=n, color=col, lw=1.4)
ax[0].set_ylabel("children / day (14-rec. mean)"); ax[0].legend(frameon=False, ncol=3, loc="upper left")
ax[1].plot(d.index, d["hhs_care"], color=NAVY, lw=1.2, label="HHS care"); ax[1].plot(d.index, d["cbp_custody"], color=ORANGE, lw=1.2, label="CBP custody")
ax[1].set_ylabel("census"); ax[1].legend(frameon=False)
for a in ax: a.axvline(shift, color=RED, ls="--", lw=.8)
ax[0].text(shift, ax[0].get_ylim()[1] * .62, " Feb 2025\n regime shift", color=RED, fontsize=8)
fig.tight_layout(); fig.savefig(f"{OUT}/fig1_pipeline_flows.png"); plt.close()

# Fig 2 - implied dwell / LOS
fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
ax[0].plot(d.index, d["cbp_dwell_days"], color=BLUE, lw=1.2); ax[0].axhline(3, color=RED, ls="--", lw=.8)
ax[0].text(d.index[5], 3.1, "72-hour benchmark", color=RED, fontsize=7); ax[0].set_title("Implied CBP dwell (days)")
ax[1].plot(d.index, d["hhs_los_days"], color=GREEN, lw=1.2); ax[1].set_yscale("log"); ax[1].set_title("Implied HHS length of stay (days, log)")
for a in ax: a.tick_params(axis="x", rotation=30)
fig.tight_layout(); fig.savefig(f"{OUT}/fig2_dwell_los.png"); plt.close()

# Fig 3 - efficiency ratios
fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
ax[0].plot(d.index, r(d["ter"]), color=BLUE); ax[0].set_title("Transfer Efficiency Ratio (14-rec. mean)")
ax[1].plot(d.index, r(d["dei"]) * 100, color=GREEN); ax[1].set_title("Discharge Effectiveness (% of HHS census / day)")
for a in ax: a.tick_params(axis="x", rotation=30); a.axvline(shift, color=RED, ls="--", lw=.8)
fig.tight_layout(); fig.savefig(f"{OUT}/fig3_efficiency_ratios.png"); plt.close()

# Fig 4 - reporting-day pattern (high-volume regime)
hv = d[d["apprehended"].rolling(28, min_periods=14).mean() > 75]
dp = an.dow_profile(hv[hv["dow"].isin([0, 1, 2, 3, 6])])
fig, ax = plt.subplots(figsize=(5.5, 3))
x = range(len(dp)); ax.bar([i - .2 for i in x], dp["discharged"], .4, color=GREEN, label="Discharged")
ax.bar([i + .2 for i in x], dp["transferred"], .4, color=BLUE, label="Transferred")
ax.set_xticks(list(x)); ax.set_xticklabels(dp.index); ax.set_ylabel("avg children / record"); ax.legend(frameon=False)
ax.set_title("Reporting-day pattern, high-volume period (2023-Jan 2025)")
fig.tight_layout(); fig.savefig(f"{OUT}/fig4_reporting_day.png"); plt.close()

# Fig 5 - HHS backlog episodes on census
ep = an.sustained_imbalance(d, "hhs")
fig, ax = plt.subplots(figsize=(8, 3.2)); ax.plot(d.index, d["hhs_care"], color=NAVY, lw=1.2)
for _, e in ep.iterrows(): ax.axvspan(e["start"], e["end"], color=ORANGE, alpha=.3)
ax.set_title("HHS census with sustained inflow > outflow episodes (shaded, ≥14 records)"); ax.set_ylabel("children in HHS care")
fig.tight_layout(); fig.savefig(f"{OUT}/fig5_backlog_episodes.png"); plt.close()

# Fig 6 - outcome stability
m = an.monthly_trends(d)
fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
ax[0].bar(m.index, m["avg_discharged"], width=20, color=GREEN); ax[0].set_title("Avg discharges per day, by month")
ax[1].plot(m.index, m["oss"], color=NAVY, marker="o", ms=3); ax[1].set_title("Outcome Stability Score, by month"); ax[1].set_ylim(40, 90)
for a in ax: a.tick_params(axis="x", rotation=30)
fig.tight_layout(); fig.savefig(f"{OUT}/fig6_outcomes.png"); plt.close()

# Tables
q = an.period_summary(d, "quarter"); q.round(3).to_csv(f"{OUT}/table_quarterly_summary.csv")
an.regime_table(d).round(3).to_csv(f"{OUT}/table_regimes.csv")
ep.to_csv(f"{OUT}/table_hhs_imbalance_episodes.csv", index=False)
an.stagnation_periods(d).to_csv(f"{OUT}/table_stagnation_periods.csv", index=False)
an.sudden_drops(d).to_csv(f"{OUT}/table_sudden_drops.csv", index=False)
m.round(3).to_csv(f"{OUT}/table_monthly_trends.csv")
d.drop(columns=["month"]).to_csv(f"{OUT}/enriched_dataset.csv", index=False)
print("done:", sorted(os.listdir(OUT)))
