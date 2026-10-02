# Effect of Tropical Typhoons on Port Activity: Kaohsiung, Taiwan

This project models how tropical typhoons disrupt daily port calls at Kaohsiung Port (2019–2024). It combines three public datasets:

- storm tracks from IBTrACS
- daily port calls from IMF PortWatch
- daily weather from NOAA GSOD/ISD

The analysis has two layers:

- **Layer 1:** a first pass using the raw arrival counts.
  - Cross-sectional OLS of the trough depth and recovery time on storm characteristics.
  - A fixed-effects panel regression of daily arrivals on local wind speed and visibility.
- **Layer 2:** the same questions, measured against a counterfactual "no-storm" baseline.
  - Remove the trend and the weekly seasonality first.
  - Then measure the onset and recovery of each storm's disruption relative to that baseline.
  - Re-run the panel on the normalised activity.

## Repository layout

```
├── report.ipynb              the full report as a notebook
├── data/
│   ├── raw/                  downloaded inputs (01_fetch_data.py)
│   └── processed/            intermediate tables produced by the pipeline
├── figures/                  every figure used in the report
├── results/                  model output (regression tables) as .txt
├── scripts/                  the pipeline, run in numbered order
│   ├── 01_fetch_data.py
│   ├── 02_layer1_ols.py
│   ├── 03_layer1_panel.py
│   ├── 04_layer2_baseline.py
│   ├── 05_layer2_lags_ols.py
│   ├── 06_layer2_panel.py
│   ├── 07_figures.py
│   └── run_all.py            runs steps 02–07
└── src/port_typhoon/         shared code used by the scripts
    ├── config.py             port location, years, window, thresholds, paths
    ├── storms.py             IBTrACS loading, closest approach, storm windows
    ├── port.py               PortWatch download and loading
    ├── weather.py            GSOD station lookup, download, cleaning
    ├── baseline.py           Layer 2 counterfactual baseline
    ├── events.py             Layer 1 trough/recovery, Layer 2 onset/recovery
    ├── plots.py              all figures
    ├── geo.py                haversine distance
    └── download.py           file download helper
```

All settings, such as the storm window (−10/+30 days), the 4° search box, the years and the thresholds, are in `src/port_typhoon/config.py`.

## The report

**`report.ipynb`** is the full write-up as a Jupyter notebook. It covers the aims, datasets, methods, equations, results tables, figures and conclusions, and every number is computed live from `data/`. Open it in VS Code or Jupyter and choose **Run All**.

## Getting started

```bash
pip install -r requirements.txt

python scripts/01_fetch_data.py   # download data from IBTrACS, PortWatch and NOAA
python scripts/run_all.py         # run the full analysis (steps 02–07)
```

The small raw files are committed, so `run_all.py` works straight after cloning, without downloading anything. The IBTrACS file (~100 MB) is too big for GitHub and is git-ignored. `01_fetch_data.py` downloads it and rebuilds `data/processed/closest_approach_storms.csv` from it. Use `--force` to re-download everything, or `--only storms|port|weather` to refresh one source.

## Data sources

| Data | Source | File |
|---|---|---|
| Storm tracks (3-hourly), WP basin | [IBTrACS v04r01](https://www.ncei.noaa.gov/products/international-best-track-archive), NOAA NCEI | `data/raw/ibtracs.WP.list.v04r01.csv` (ignored) |
| Daily port calls by vessel type | [IMF PortWatch](https://portwatch.imf.org) Daily Ports Data API | `data/raw/portwatch_kaohsiung_daily.csv` |
| Daily weather (wind speed in knots, visibility in miles) | [NOAA GSOD](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00516), station 46740099999 (Kaohsiung Intl Airport) | `data/raw/gsod_kaohsiung.csv` |

Storms are included if any track point in 2019–2024 lies within ±4° of the port (22.60°N, 120.28°E). This gives 44 storms. Each storm is characterised at its closest approach by maximum wind (`USA_WIND`), central pressure (`USA_PRES`), radius of maximum wind (`USA_RMW`) and distance from the port.

## Method

**Layer 1**

- `02_layer1_ols.py` computes, for each storm:
  - `trough_drop`: the mean arrivals on days −10 to −2 minus the minimum arrivals in the window.
  - `days_to_recover`: the first day after closest approach when arrivals get back to that pre-storm mean.

  Both are then regressed on the storm characteristics.
- `03_layer1_panel.py` fits `TOTAL_ARRIVALS ~ WDSP + VISIB + storm fixed effects`, with standard errors clustered by storm.

**Layer 2**

- `04_layer2_baseline.py` builds the counterfactual baseline:
  - Mask every day that falls inside any storm window.
  - Fit a weekday-median seasonal component plus a 29-day rolling-median trend on the remaining days.
  - Interpolate across the masked days.
  - Deviation = actual − expected.
- `05_layer2_lags_ols.py` finds each storm's `onset_lag`: the first day with either a single-day drop below −3σ or at least 2 consecutive days below −1.5σ. It finds `recovery_lag` as the first day after onset back above −1.5σ. It then regresses both, plus the duration, on the storm characteristics.
- `06_layer2_panel.py` fits `deviation ~ WDSP + VISIB + storm fixed effects`.

Figure `figures/layer2_flowchart.png` summarises the Layer 2 pipeline.

## Changes from the original analysis

This repo is a clean rewrite of the original project code, with these fixes. Some results differ from the first draft of the report.

1. **Complete port series in the code.** The PortWatch download in the original code asked for one page per year and was silently truncated. It returned only 1,192 of 2,192 days (2021 had just 28 days). The final Layer 2 results in the report already used the full arrivals feed, but the code still read the truncated file. The download now pages through the API, and both layers use the same complete series.
2. **Storm windows aligned to calendar days.** Layer 1 measured "days from approach" from the exact approach time (e.g. 21:00). As a result, the approach day itself was labelled −1, and the first day of some windows was dropped. Both layers now align on the calendar day of closest approach. The Layer 1 panel grows from 1,739 to 1,779 usable storm-days.
3. **Sustained-dip rule in onset detection.** In the original code, a run of low days that started right after a normal day never got a start date. The "moderate sustained dip" rule therefore almost never triggered. With this fixed, onset is detected for 29/44 storms (the report says 23).
4. **Weather download.** The original ISD script downloaded hourly data and skipped 2024 (`range(2019, 2024)`). The fetch step now downloads GSOD daily summaries for 2019–2024 from the nearest station with full coverage. That is the file the analysis actually used.
5. **Pre-storm baseline formula.** The report writes the Layer 1 baseline as $\frac{1}{7}\sum_{t=-10}^{-2}$. Days −10 to −2 are 9 days, and the code takes their mean, so the notebook uses $\frac{1}{9}$.
6. **Single source of truth.** The haversine function, missing-value codes, window lengths and file paths were duplicated across scripts. Each now lives in one place.

### Open issues to consider

- **Overlapping storm windows.** Back-to-back storms share days. For example, Krathon, Kong-rey, Yinxing, Toraji, Man-yi and Usagi all fall between October and November 2024. The same drop in arrivals can then be counted as the onset for several storms, sometimes at the edge of a window (onset = −10). Options include limiting the onset search to a narrower range (e.g. −3 to +7 days), or giving each day only to its nearest storm.
- **Weather station ID.** The report cites ISD station 466920 99999, but the weather data used is from 467400 99999 (Kaohsiung International Airport).
- **Small sample.** With 26–38 storms that have complete characteristics and four regressors, the storm-level OLS models have little power. None of the Layer 2 lag regressions are significant.
