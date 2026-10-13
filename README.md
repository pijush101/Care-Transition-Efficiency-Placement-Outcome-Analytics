# Care Transition Efficiency & Placement Outcome Analytics

Process-efficiency analytics for the UAC Program pipeline (CBP custody -> HHS care -> sponsor discharge).

## Files
| File | Purpose |
|---|---|
| `analytics.py` | Analytics engine: cleaning, KPIs, bottleneck / stagnation / drop detection, diagnostics |
| `app.py` | Streamlit dashboard (4 core modules + data-quality tab) |
| `generate_report_assets.py` | Regenerates every figure and table used in the research paper |
| `HHS_Unaccompanied_Alien_Children_Program.csv` | Source data |
| `figures/` | PNG figures, summary tables, enriched dataset |

## Run
```bash
pip install -r requirements.txt
streamlit run app.py                 # dashboard
python generate_report_assets.py     # figures + tables
```

## KPI definitions
| KPI | Formula |
|---|---|
| Transfer Efficiency Ratio (TER) | transferred / CBP custody (daily); 1/TER ~ implied CBP dwell in days |
| Discharge Effectiveness Index (DEI) | discharged / HHS care (daily); 1/DEI ~ implied length of stay in days |
| Pipeline Throughput | exits / entries: CBP stage = transfers / apprehensions; HHS stage = discharges / transfers; end-to-end = 14-record mean discharges / apprehensions |
| Backlog Accumulation Rate | % change in stage census over 14 records (primary); net flow (in - out) shown for context |
| Outcome Stability Score (OSS) | 100 / (1 + CV of discharges over 28 records); 100 = perfectly steady |

## Caveats
* The file reports Sunday-Thursday only; "weekday vs weekend" is a reporting-calendar effect.
* Flows do not fully reconcile with census movements; census is the primary backlog measure.
* Implied dwell / length of stay (stock / outflow, Little's Law) are population averages, not child-level durations.
* "Discharged" is not split by sponsor vs other exit type.
