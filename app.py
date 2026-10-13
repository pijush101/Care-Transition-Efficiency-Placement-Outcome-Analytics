"""
app.py - UAC Care Transition Efficiency & Placement Outcome Analytics (Streamlit)
Run:  streamlit run app.py
"""
import pathlib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import analytics as an

# ── paths ────────────────────────────────────────────────────────────────────
_DEFAULT_CSV = pathlib.Path(__file__).parent.parent / "HHS_Unaccompanied_Alien_Children_Program.csv"

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UAC Care Transition Analytics",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── colour palette ───────────────────────────────────────────────────────────
NAVY   = "#0F1C3F"
BLUE   = "#3B82F6"
CYAN   = "#06B6D4"
ORANGE = "#F59E0B"
RED    = "#EF4444"
GREEN  = "#10B981"
GREY   = "#94A3B8"
PURPLE = "#8B5CF6"
BG     = "#0A0F1E"
CARD   = "#111827"
BORDER = "#1E2D4A"

# ── custom Plotly theme ───────────────────────────────────────────────────────
_LEGEND_BASE = dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER)
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.02)",
    font=dict(family="Inter, sans-serif", color="#CBD5E1", size=12),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor=BORDER, tickcolor=BORDER),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor=BORDER, tickcolor=BORDER),
    margin=dict(l=10, r=10, t=30, b=10),
    hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER, font_color="#F1F5F9"),
)

# ── global CSS injection ──────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── Reset & Base ─────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: linear-gradient(135deg, #0A0F1E 0%, #0F1C3F 50%, #0A0F1E 100%);
    background-attachment: fixed;
}
/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1529 0%, #111827 100%) !important;
    border-right: 1px solid #1E2D4A !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #60A5FA !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-size: 0.68rem !important;
    margin-top: 1.2rem !important;
}
[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stDateInput > div > div {
    background: #1E2D4A !important;
    border: 1px solid #2D3D5A !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #CBD5E1 !important;
}
[data-testid="stSidebarUserContent"] {
    padding: 1.5rem 1rem !important;
}
/* sidebar logo/title area */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.5rem 0 1.5rem 0;
    border-bottom: 1px solid #1E2D4A;
    margin-bottom: 1rem;
}
.sidebar-brand-icon { font-size: 1.8rem; }
.sidebar-brand-text { font-size: 0.85rem; font-weight: 700; color: #E2E8F0; line-height: 1.2; }
.sidebar-brand-sub  { font-size: 0.65rem; color: #64748B; font-weight: 400; }
/* ── Page header ──────────────────────────────────────────── */
.page-header {
    background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(6,182,212,0.08) 100%);
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.page-header-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(59,130,246,0.2);
    border: 1px solid rgba(59,130,246,0.4);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.7rem;
    font-weight: 600;
    color: #93C5FD;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.page-header h1 {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    color: #F1F5F9 !important;
    margin: 0 0 0.4rem 0 !important;
    line-height: 1.2 !important;
    background: linear-gradient(90deg, #F1F5F9, #93C5FD);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.page-header p {
    color: #64748B !important;
    font-size: 0.875rem !important;
    margin: 0 !important;
    font-weight: 400 !important;
}
/* ── KPI Cards ────────────────────────────────────────────── */
.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1a2540 100%);
    border: 1px solid #1E2D4A;
    border-radius: 12px;
    padding: 1.2rem 1.25rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
    margin-bottom: 0;
}
.kpi-card:hover {
    border-color: rgba(59,130,246,0.5);
    box-shadow: 0 0 20px rgba(59,130,246,0.1);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 12px 12px 0 0;
}
.kpi-card.blue::before   { background: linear-gradient(90deg, #3B82F6, #06B6D4); }
.kpi-card.green::before  { background: linear-gradient(90deg, #10B981, #06B6D4); }
.kpi-card.orange::before { background: linear-gradient(90deg, #F59E0B, #EF4444); }
.kpi-card.red::before    { background: linear-gradient(90deg, #EF4444, #F59E0B); }
.kpi-card.purple::before { background: linear-gradient(90deg, #8B5CF6, #3B82F6); }
.kpi-card.cyan::before   { background: linear-gradient(90deg, #06B6D4, #3B82F6); }
.kpi-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #F1F5F9;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    margin-bottom: 0.4rem;
}
.kpi-delta { font-size: 0.72rem; font-weight: 500; }
.kpi-delta.pos { color: #10B981; }
.kpi-delta.neg { color: #EF4444; }
.kpi-delta.neu { color: #64748B; }
/* ── Alert banners ────────────────────────────────────────── */
.alert-error {
    background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.06));
    border: 1px solid rgba(239,68,68,0.35);
    border-left: 4px solid #EF4444;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    color: #FCA5A5;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 1rem;
}
.alert-success {
    background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.06));
    border: 1px solid rgba(16,185,129,0.35);
    border-left: 4px solid #10B981;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    color: #6EE7B7;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 1rem;
}
/* ── Tab styling ──────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(15,28,63,0.5) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid #1E2D4A !important;
    margin-bottom: 1.5rem !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 7px !important;
    color: #64748B !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    padding: 8px 14px !important;
    border: none !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, #1E3A6E, #1a3060) !important;
    color: #93C5FD !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.15) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: #CBD5E1 !important;
    background: rgba(30,45,74,0.5) !important;
}
/* ── Section headers ─────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 1rem 0 0.75rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #1E2D4A;
}
.section-header h3 {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #CBD5E1 !important;
    margin: 0 !important;
}
.section-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
/* ── Caption / helper text ───────────────────────────────── */
.caption-text {
    font-size: 0.75rem;
    color: #475569;
    font-style: italic;
    margin-top: 0.3rem;
    line-height: 1.5;
}
/* ── Dataframe ───────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E2D4A !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
/* ── Download button ─────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #1E3A6E, #1a3060) !important;
    color: #93C5FD !important;
    border: 1px solid rgba(59,130,246,0.35) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, #2D4E8A, #253870) !important;
    box-shadow: 0 4px 12px rgba(59,130,246,0.2) !important;
}
/* ── File uploader ───────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 1px dashed #1E2D4A !important;
    border-radius: 10px !important;
}
/* ── Metric (hide default — we use custom cards) ─────────── */
[data-testid="stMetric"] { display: none !important; }
/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0A0F1E; }
::-webkit-scrollbar-thumb { background: #1E2D4A; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2D3D5A; }
/* ── Info/warning boxes ──────────────────────────────────── */
[data-testid="stInfo"] {
    background: rgba(59,130,246,0.08) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 8px !important;
    color: #93C5FD !important;
}
[data-testid="stWarning"] {
    background: rgba(245,158,11,0.08) !important;
    border: 1px solid rgba(245,158,11,0.2) !important;
    border-radius: 8px !important;
    color: #FCD34D !important;
}
/* ── Main content area ───────────────────────────────────── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}
hr {
    border: none !important;
    border-top: 1px solid #1E2D4A !important;
    margin: 1.5rem 0 !important;
}
/* ── Streamlit toolbar / deploy bar ──────────────────── */
[data-testid="stHeader"] {
    background: #0A0F1E !important;
    border-bottom: 1px solid #1E2D4A !important;
}
[data-testid="stToolbar"] {
    background: #0A0F1E !important;
}
[data-testid="stDecoration"] {
    background: #0A0F1E !important;
    display: none !important;
}
[data-testid="stAppDeployButton"] > button,
[data-testid="stAppDeployButton"] > div {
    background: #111827 !important;
    color: #64748B !important;
    border: 1px solid #1E2D4A !important;
    border-radius: 8px !important;
}
[data-testid="stAppDeployButton"] > button:hover {
    background: #1E2D4A !important;
    color: #93C5FD !important;
}
[data-testid="stMainMenu"] > button {
    background: transparent !important;
    color: #64748B !important;
}
[data-testid="stMainMenu"] > button:hover {
    background: #1E2D4A !important;
    color: #93C5FD !important;
}
[data-testid="stStatusWidget"] {
    background: #0A0F1E !important;
    color: #64748B !important;
}
/* top rainbow decoration stripe */
header[data-testid="stHeader"]::before {
    display: none !important;
}
/* Make header icons match dark theme */
header svg { color: #64748B !important; fill: #64748B !important; }
header button { color: #64748B !important; }
header button:hover { color: #93C5FD !important; background: #1E2D4A !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def apply_theme(fig, height=340, legend_y=1.08):
    fig.update_layout(**PLOT_LAYOUT, height=height,
                      legend=dict(**_LEGEND_BASE, orientation="h", y=legend_y))
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)
    return fig


def section_header(title: str, color: str = BLUE, icon: str = ""):
    st.markdown(
        f"""<div class="section-header">
              <div class="section-dot" style="background:{color};box-shadow:0 0 6px {color}44;"></div>
              <h3>{icon} {title}</h3>
            </div>""",
        unsafe_allow_html=True,
    )


def kpi_card(label, value, delta=None, color_cls="blue"):
    if delta is not None:
        stripped = delta.lstrip()
        sign = "pos" if stripped.startswith("+") else ("neg" if stripped.startswith("-") else "neu")
        delta_html = f'<div class="kpi-delta {sign}">{delta}</div>'
    else:
        delta_html = '<div class="kpi-delta neu" style="visibility:hidden">—</div>'
    st.markdown(
        f'<div class="kpi-card {color_cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def get_data(src) -> pd.DataFrame:
    return an.add_metrics(an.load_data(src))


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <div class="sidebar-brand-icon">🧭</div>
      <div>
        <div class="sidebar-brand-text">UAC Analytics</div>
        <div class="sidebar-brand-sub">Care Transition Dashboard</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📂 Data Source")
    upload = st.file_uploader("Upload CSV (optional)", type="csv",
                              help="Defaults to HHS_Unaccompanied_Alien_Children_Program.csv in the project root.")
    full = get_data(upload if upload else str(_DEFAULT_CSV))

    lo, hi = full["date"].min().date(), full["date"].max().date()
    st.markdown("### 📅 Date Range")
    start, end = st.date_input("Select range", value=(lo, hi), min_value=lo, max_value=hi,
                               label_visibility="collapsed")
    d = full[(full["date"].dt.date >= start) & (full["date"].dt.date <= end)].copy()

    st.markdown("### 📊 Metric View")
    ratio_mode = st.radio("Efficiency display", ["Daily ratio (%)", "Implied days (Little's Law)"],
                          help="Show TER/DEI as a % per day, or as implied dwell / length of stay in days.")
    smooth = st.slider("Smoothing window (records)", 1, 28, 7)
    group_by = st.selectbox("Aggregate trends by", ["month", "quarter"])

    st.markdown("### 🚨 Alert Thresholds")
    ter_min     = st.slider("Min Transfer Efficiency", 0.0, 1.0, 0.50, 0.05)
    dei_min     = st.slider("Min Discharge Effectiveness (%/day)", 0.0, 5.0, 1.0, 0.1) / 100
    backlog_max = st.slider("Max HHS census growth (14 rec., %)", 0.0, 20.0, 5.0, 0.5) / 100
    oss_min     = st.slider("Min Outcome Stability Score", 40, 90, 65)

    st.markdown("---")
    dq_info = an.data_quality(full)
    st.markdown(f"""<div style="font-size:0.7rem;color:#475569;line-height:1.9">
        <b style="color:#64748B">Dataset info</b><br>
        📋 {dq_info['records']} records<br>
        📆 {dq_info['start']:%d %b %Y} → {dq_info['end']:%d %b %Y}<br>
        ⚠ {dq_info['unreported_days']} unreported days
    </div>""", unsafe_allow_html=True)

# ── guard ─────────────────────────────────────────────────────────────────────
if d.empty:
    st.warning("No records in the selected date range.")
    st.stop()

sm = d.set_index("date").rolling(smooth, min_periods=1).mean(numeric_only=True)

# ── page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-header-badge">🏛 HHS · UAC Program · Process Intelligence</div>
  <h1>Care Transition Efficiency &amp; Placement Outcome Analytics</h1>
  <p>UAC pipeline: CBP custody → HHS care → sponsor discharge &nbsp;·&nbsp; Process-efficiency lens focused on throughput, backlogs, and outcome stability.</p>
</div>
""", unsafe_allow_html=True)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
last30 = d.tail(30).mean(numeric_only=True)
prev30 = d.iloc[:30].mean(numeric_only=True)

ter_delta = last30["ter"] - prev30["ter"]
dei_delta = (last30["dei"] - prev30["dei"]) * 100
e2e_delta = last30["e2e_throughput"] - prev30["e2e_throughput"]
oss_delta = last30["oss"] - prev30["oss"]

cols = st.columns(5)
with cols[0]:
    kpi_card("Transfer Efficiency (TER)", f"{last30['ter']:.2f}",
             f"{ter_delta:+.2f} vs period start", "blue")
with cols[1]:
    kpi_card("Discharge Effectiveness", f"{last30['dei']*100:.2f}%",
             f"{dei_delta:+.2f} pts", "green")
with cols[2]:
    kpi_card("End-to-end Throughput", f"{last30['e2e_throughput']:.2f}",
             f"{e2e_delta:+.2f}", "cyan" if e2e_delta >= 0 else "orange")
with cols[3]:
    backlog_cls = "red" if last30["hhs_backlog_rate"] > backlog_max else "green"
    kpi_card("HHS Backlog Rate", f"{last30['hhs_backlog_rate']*100:+.1f}%",
             color_cls=backlog_cls)
with cols[4]:
    kpi_card("Outcome Stability (OSS)", f"{last30['oss']:.0f}/100",
             f"{oss_delta:+.0f} pts", "purple")

st.markdown('<p class="caption-text" style="margin-bottom:1rem">KPI tiles show the mean of the last 30 records in range · Deltas compare with the first 30 records in range.</p>',
            unsafe_allow_html=True)

# ── alert banner ──────────────────────────────────────────────────────────────
al = an.alerts(d.tail(30), ter_min, dei_min, backlog_max, oss_min).drop(columns="date").mean()
breaches = [f"<b>{n}</b> ({v:.0%} of last 30 records)" for n, v in al.items() if v >= 0.5]
if breaches:
    st.markdown(f'<div class="alert-error">⚠&nbsp; Threshold alerts: &nbsp;{"&nbsp; · &nbsp;".join(breaches)}</div>',
                unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-success">✓&nbsp; No sustained threshold breaches in the last 30 records.</div>',
                unsafe_allow_html=True)

# ── tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["🔄  Pipeline Flow", "⚡  Efficiency", "🚧  Bottlenecks",
                "📈  Outcomes", "🔍  Data Quality"])

# ══════════════════════════════════════════════════════ TAB 1 – Pipeline ══════
with tabs[0]:
    c1, c2 = st.columns([1.1, 1], gap="medium")
    with c1:
        section_header("Care Pipeline: Average Daily Flows", BLUE, "🔄")
        a, t, dis = d["apprehended"].mean(), d["transferred"].mean(), d["discharged"].mean()
        fig = go.Figure(go.Sankey(
            node=dict(
                label=["Apprehended (CBP intake)", "CBP Custody", "Transferred to HHS",
                       "HHS Care", "Discharged to Sponsor"],
                color=[GREY, BLUE, ORANGE, NAVY, GREEN], pad=24, thickness=18,
                line=dict(color=BORDER, width=0.5)),
            link=dict(
                source=[0, 1, 2, 3], target=[1, 2, 3, 4], value=[a, t, t, dis],
                color=["rgba(148,163,184,.25)", "rgba(59,130,246,.3)",
                       "rgba(245,158,11,.3)", "rgba(16,185,129,.3)"])))
        apply_theme(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<p class="caption-text">Intake {a:,.0f}/day · Transfers {t:,.0f}/day · Discharges {dis:,.0f}/day. Link widths reflect daily flow volumes.</p>',
                    unsafe_allow_html=True)

    with c2:
        section_header("Stage Census Load", ORANGE, "📊")
        f2 = make_subplots(specs=[[{"secondary_y": True}]])
        f2.add_trace(go.Scatter(x=sm.index, y=sm["hhs_care"], name="HHS Care",
                                line=dict(color=BLUE, width=2),
                                fill="tozeroy", fillcolor="rgba(59,130,246,0.05)"), secondary_y=False)
        f2.add_trace(go.Scatter(x=sm.index, y=sm["cbp_custody"], name="CBP Custody",
                                line=dict(color=ORANGE, width=2, dash="dot")), secondary_y=True)
        f2.update_yaxes(title_text="HHS Care", secondary_y=False, title_font_color=BLUE)
        f2.update_yaxes(title_text="CBP Custody", secondary_y=True, title_font_color=ORANGE)
        apply_theme(f2, height=340)
        st.plotly_chart(f2, use_container_width=True)

    st.markdown("---")
    section_header("Daily Movement Between Stages (Smoothed)", CYAN, "📉")
    f3 = go.Figure()
    for col, name, color, fillcolor in [
        ("apprehended", "Apprehended (CBP intake)", GREY,  "rgba(148,163,184,0.06)"),
        ("transferred", "Transferred CBP→HHS",      BLUE,  "rgba(59,130,246,0.07)"),
        ("discharged",  "Discharged from HHS",      GREEN, "rgba(16,185,129,0.07)"),
    ]:
        f3.add_trace(go.Scatter(x=sm.index, y=sm[col], name=name,
                                line=dict(color=color, width=2),
                                fill="tozeroy", fillcolor=fillcolor))
    f3.update_layout(yaxis_title="Children / day")
    apply_theme(f3, height=320)
    st.plotly_chart(f3, use_container_width=True)

# ═══════════════════════════════════════════════════ TAB 2 – Efficiency ══════
with tabs[1]:
    use_days = ratio_mode.startswith("Implied")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        section_header("CBP → HHS Transfer Efficiency", BLUE, "🔁")
        f = go.Figure()
        if use_days:
            f.add_trace(go.Scatter(x=sm.index, y=sm["cbp_dwell_days"],
                                   line=dict(color=BLUE, width=2),
                                   name="Implied CBP Dwell (days)",
                                   fill="tozeroy", fillcolor="rgba(59,130,246,0.07)"))
            f.add_hline(y=3, line_dash="dash", line_color=RED,
                        annotation_text="72-hr benchmark", annotation_font_color=RED)
            f.update_layout(yaxis_title="Days")
        else:
            f.add_trace(go.Scatter(x=sm.index, y=sm["ter"],
                                   line=dict(color=BLUE, width=2), name="TER",
                                   fill="tozeroy", fillcolor="rgba(59,130,246,0.07)"))
            f.add_hline(y=ter_min, line_dash="dash", line_color=RED,
                        annotation_text="Alert threshold", annotation_font_color=RED)
            f.update_layout(yaxis_title="Transfers ÷ CBP Custody")
        apply_theme(f, height=320)
        st.plotly_chart(f, use_container_width=True)

    with c2:
        section_header("HHS Discharge Effectiveness", GREEN, "✅")
        f = go.Figure()
        if use_days:
            f.add_trace(go.Scatter(x=sm.index, y=sm["hhs_los_days"],
                                   line=dict(color=GREEN, width=2),
                                   name="Implied HHS Length of Stay (days)"))
            f.update_layout(yaxis_title="Days", yaxis_type="log")
        else:
            f.add_trace(go.Scatter(x=sm.index, y=sm["dei"] * 100,
                                   line=dict(color=GREEN, width=2), name="DEI",
                                   fill="tozeroy", fillcolor="rgba(16,185,129,0.07)"))
            f.add_hline(y=dei_min * 100, line_dash="dash", line_color=RED,
                        annotation_text="Alert threshold", annotation_font_color=RED)
            f.update_layout(yaxis_title="Discharges ÷ HHS Care (%/day)")
        apply_theme(f, height=320)
        st.plotly_chart(f, use_container_width=True)

    st.markdown("---")
    section_header("Stage Throughput (Exits ÷ Entries, Rolling Mean)", NAVY, "⚖️")
    f = go.Figure()
    for col, name, color in [
        ("cbp_throughput", "CBP: Transfers ÷ Apprehensions",       BLUE),
        ("hhs_throughput", "HHS: Discharges ÷ Transfers",          GREEN),
        ("e2e_throughput", "End-to-end: Discharges ÷ Apprehensions", PURPLE),
    ]:
        f.add_trace(go.Scatter(x=sm.index, y=sm[col].clip(upper=6), name=name,
                               line=dict(color=color, width=2)))
    f.add_hline(y=1, line_dash="dot", line_color=GREY,
                annotation_text="1.0 = exits match entries", annotation_font_color=GREY)
    f.update_layout(yaxis_title="Throughput ratio")
    apply_theme(f, height=300, legend_y=1.12)
    st.plotly_chart(f, use_container_width=True)
    st.markdown('<p class="caption-text">Above 1.0 → stage draining faster than receiving · Below 1.0 → queue building. Values capped at 6 for readability.</p>',
                unsafe_allow_html=True)

    st.markdown("---")
    section_header("Reporting-Day Pattern", ORANGE, "📅")
    dp = an.dow_profile(d[d["dow"].isin([0, 1, 2, 3, 6])])
    f = go.Figure([
        go.Bar(x=dp.index, y=dp["discharged"], name="Avg Discharged",
               marker=dict(color=GREEN, opacity=0.85, line=dict(color="rgba(0,0,0,0)", width=0))),
        go.Bar(x=dp.index, y=dp["transferred"], name="Avg Transferred",
               marker=dict(color=BLUE, opacity=0.85, line=dict(color="rgba(0,0,0,0)", width=0))),
    ])
    f.update_layout(barmode="group", yaxis_title="Children / record")
    apply_theme(f, height=280)
    st.plotly_chart(f, use_container_width=True)
    st.markdown('<p class="caption-text">File reports Sun–Thu only (Fri/Sat absent). This reflects a reporting-calendar pattern, not a true weekend effect.</p>',
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════ TAB 3 – Bottlenecks ════
with tabs[2]:
    section_header("Backlog Accumulation", RED, "📦")
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_trace(go.Scatter(x=sm.index, y=sm["hhs_backlog_rate"] * 100,
                           name="HHS Census Change over 14 rec. (%)",
                           line=dict(color=RED, width=2),
                           fill="tozeroy", fillcolor="rgba(239,68,68,0.06)"), secondary_y=False)
    f.add_trace(go.Bar(x=sm.index, y=sm["hhs_net_flow"],
                       name="Net Flow (transfers − discharges)",
                       marker=dict(color="rgba(245,158,11,0.4)")), secondary_y=True)
    f.add_hline(y=backlog_max * 100, line_dash="dash", line_color=RED,
                annotation_text="Alert threshold", annotation_font_color=RED, secondary_y=False)
    f.update_yaxes(title_text="% Change", secondary_y=False, title_font_color=RED)
    f.update_yaxes(title_text="Children / day", secondary_y=True, title_font_color=ORANGE)
    apply_theme(f, height=340, legend_y=1.1)
    st.plotly_chart(f, use_container_width=True)
    st.markdown('<p class="caption-text">Census change is the primary backlog measure. Net flow is for context only — flows do not fully reconcile to census movements in this dataset.</p>',
                unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        section_header("Sustained Inflow > Outflow Episodes (HHS)", ORANGE, "⚠️")
        min_len = st.slider("Minimum episode length (records)", 7, 45, 14, key="min_len_slider")
        ep = an.sustained_imbalance(d, "hhs", min_len=min_len)
        if ep.empty:
            st.info("✓ No sustained imbalance episodes in the selected range.")
        else:
            ep = ep.assign(start=ep["start"].dt.date, end=ep["end"].dt.date).round(1)
            st.dataframe(ep, hide_index=True, use_container_width=True)

    with c2:
        section_header("Prolonged Stagnation Periods", PURPLE, "🐌")
        sp = an.stagnation_periods(full)
        sp = sp[(sp["end"].dt.date >= start) & (sp["start"].dt.date <= end)]
        if sp.empty:
            st.info("✓ No stagnation periods in the selected range.")
        else:
            sp = sp.assign(start=sp["start"].dt.date, end=sp["end"].dt.date)
            st.dataframe(
                sp.round({"avg_dei": 4, "avg_hhs_care": 0, "avg_discharged": 1}),
                hide_index=True, use_container_width=True)

    st.markdown("---")
    section_header("Alert Timeline Heatmap", RED, "🗓️")
    a_df = an.alerts(d, ter_min, dei_min, backlog_max, oss_min).set_index("date").astype(int)
    f = go.Figure(go.Heatmap(
        z=a_df.T.values, x=a_df.index, y=a_df.columns,
        colorscale=[[0, "rgba(30,45,74,0.5)"], [1, RED]],
        showscale=False, xgap=1, ygap=1))
    apply_theme(f, height=200)
    st.plotly_chart(f, use_container_width=True)
    st.markdown('<p class="caption-text">Red = threshold breached · Adjust thresholds in the sidebar.</p>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════ TAB 4 – Outcomes ══════
with tabs[3]:
    m = an.period_summary(d, group_by)
    m.index = m.index.astype(str)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        section_header(f"Discharges per Day by {group_by.title()}", GREEN, "📤")
        f = go.Figure(go.Bar(
            x=m.index, y=m["avg_discharged"],
            marker=dict(
                color=m["avg_discharged"],
                colorscale=[[0, "rgba(16,185,129,0.5)"], [1, GREEN]],
                line=dict(color="rgba(0,0,0,0)", width=0))))
        f.update_layout(yaxis_title="Avg discharges / day")
        apply_theme(f, height=300)
        st.plotly_chart(f, use_container_width=True)

    with c2:
        section_header(f"Outcome Stability Score by {group_by.title()}", PURPLE, "🎯")
        f = go.Figure(go.Scatter(
            x=m.index, y=m["oss"], mode="lines+markers",
            line=dict(color=PURPLE, width=2),
            marker=dict(size=7, color=PURPLE, line=dict(color=BG, width=2)),
            fill="tozeroy", fillcolor="rgba(139,92,246,0.07)"))
        f.add_hline(y=oss_min, line_dash="dash", line_color=RED,
                    annotation_text="Alert threshold", annotation_font_color=RED)
        f.update_layout(yaxis_title="OSS (100 = perfectly steady)", yaxis_range=[40, 100])
        apply_theme(f, height=300)
        st.plotly_chart(f, use_container_width=True)

    st.markdown("---")
    section_header("Month-over-Month Placement Change", CYAN, "📊")
    mm = an.monthly_trends(d)
    mm.index = mm.index.strftime("%Y-%m")
    bar_colors = [GREEN if (v or 0) >= 0 else RED for v in mm["mom_discharge_pct"]]
    f = go.Figure(go.Bar(
        x=mm.index, y=mm["mom_discharge_pct"],
        marker=dict(color=bar_colors, opacity=0.85, line=dict(color="rgba(0,0,0,0)", width=0))))
    f.add_hline(y=0, line_color=GREY, line_width=1)
    f.update_layout(yaxis_title="MoM change in avg discharges (%)")
    apply_theme(f, height=280)
    st.plotly_chart(f, use_container_width=True)

    st.markdown("---")
    section_header("Sudden Drops in Discharge Performance", RED, "📉")
    sd_ = an.sudden_drops(full)
    sd_ = sd_[(sd_["date"].dt.date >= start) & (sd_["date"].dt.date <= end)]
    if sd_.empty:
        st.info("✓ No sudden drops detected in the selected range.")
    else:
        sd_ = sd_.assign(
            date=sd_["date"].dt.date,
            drop_vs_prior_28=(sd_["drop_vs_prior_28"] * 100).round(0).astype(int).astype(str) + "%")
        st.dataframe(
            sd_.rename(columns={"drop_vs_prior_28": "7-rec. mean vs prior 28-rec."}),
            hide_index=True, use_container_width=True)
    st.markdown('<p class="caption-text">Drops at very low volumes (&lt;20/day) may reflect count noise. Interpret alongside the quarterly CV-over-Poisson ratio below.</p>',
                unsafe_allow_html=True)

    st.markdown("---")
    section_header("Period Summary Table", GREY, "📋")
    show = m[["avg_apprehended", "avg_transferred", "avg_discharged", "avg_hhs_care",
              "ter", "dei", "cbp_dwell_days", "hhs_los_days", "oss", "cv_over_poisson"]].round(3)
    st.dataframe(show, use_container_width=True)
    st.download_button(
        f"⬇ Download {group_by.title()} Summary (CSV)",
        show.to_csv().encode(),
        file_name=f"uac_{group_by}_summary.csv",
        mime="text/csv")

# ═══════════════════════════════════════════════ TAB 5 – Data Quality ══════
with tabs[4]:
    dq, rc = an.data_quality(full), an.reconciliation(full)

    section_header("Dataset Diagnostics", BLUE, "🔬")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""<div class="kpi-card blue">
            <div class="kpi-label">Total Records</div>
            <div class="kpi-value" style="font-size:1.4rem">{dq['records']}</div>
            <div class="kpi-delta neu">{dq['start']:%d %b %Y} → {dq['end']:%d %b %Y}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card orange">
            <div class="kpi-label">Unreported Days</div>
            <div class="kpi-value" style="font-size:1.4rem">{dq['unreported_days']}</div>
            <div class="kpi-delta neu">of {dq['calendar_days']} calendar days</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card purple">
            <div class="kpi-label">HHS Flow Correlation</div>
            <div class="kpi-value" style="font-size:1.4rem">{rc['hhs_corr']:.2f}</div>
            <div class="kpi-delta neu">CBP corr: {rc['cbp_corr']:.2f} · n={rc['pairs']} pairs</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    section_header("After-Gap Reporting Effect", ORANGE, "🔎")
    st.dataframe(an.after_gap_effect(full).round(1), use_container_width=True)

    st.markdown("---")
    st.warning(
        "**Methodology note:** Metrics dividing flows by census (TER, DEI) and implied dwell/LoS "
        "(stock ÷ outflow) are population-level approximations — not child-level durations. "
        "Discharge counts do not distinguish sponsor placements from other exit types.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Enriched Dataset (CSV)",
        d.to_csv(index=False).encode(),
        file_name="uac_enriched.csv",
        mime="text/csv")
