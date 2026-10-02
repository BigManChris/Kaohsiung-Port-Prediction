"""All figures used in the report. Each function saves one PNG to figures/."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.seasonal import STL

from . import config as cfg

ACTUAL_C, EXPECTED_C = "#1f77b4", "#d62728"


def _save(fig, name, dpi=150):
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = cfg.FIGURES_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved figures/{name}")


# ---------------------------------------------------------------------------
# Data overview
# ---------------------------------------------------------------------------
def storm_classification(storms):
    counts = storms["USA_STATUS"].fillna("n/a").value_counts()
    fig, ax = plt.subplots(figsize=(6, 4))
    counts.plot(kind="bar", edgecolor="black", ax=ax)
    ax.set_title("Storm classification at closest approach")
    ax.set_xlabel("USA_STATUS")
    ax.set_ylabel("Count")
    _save(fig, "storm_classification.png")


def storms_per_year(storms):
    per_year = storms["SEASON"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    per_year.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Number of storms per year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of storms")
    _save(fig, "storms_per_year.png")


def acf_port_calls(port, lags=60):
    ts = port["portcalls"].interpolate()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    plot_acf(ts, lags=lags, ax=ax, title="")
    for wk in range(7, lags + 1, 7):
        ax.axvline(wk, color="orange", ls=":", lw=1, alpha=0.6)
    ax.set_title(f"Autocorrelation of daily port calls ({cfg.START_YEAR}-{cfg.END_YEAR}, {lags} lags)")
    ax.set_xlabel("Lag (days)")
    ax.set_ylabel("Autocorrelation")
    _save(fig, "acf_port_calls.png")


def stl_decomposition(port):
    ts = port["portcalls"].interpolate()
    res = STL(ts, period=7, robust=True).fit()
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    for ax, (title, s) in zip(axes, [("Observed", ts), ("Trend", res.trend),
                                     ("Seasonal (weekly)", res.seasonal), ("Residual", res.resid)]):
        ax.plot(s.index, s, lw=0.7)
        ax.set_title(title)
    _save(fig, "stl_decomposition.png")


# ---------------------------------------------------------------------------
# Layer 2
# ---------------------------------------------------------------------------
def full_timeline(cf, windows):
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(cf.index, cf["portcalls"], color=ACTUAL_C, lw=0.7, label="Actual port calls")
    ax.plot(cf.index, cf["expected"], color=EXPECTED_C, lw=1.2, label="Counterfactual (no-storm) baseline")
    for w in windows.itertuples():
        ax.axvspan(w.window_start, w.window_end, color="grey", alpha=0.12, lw=0)
    handles, _ = ax.get_legend_handles_labels()
    handles.append(mpatches.Patch(color="grey", alpha=0.25,
                                  label=f"Storm window (-{cfg.PRE_DAYS}/+{cfg.POST_DAYS} days)"))
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    ax.set_title(f"Kaohsiung daily port calls: actual vs. counterfactual ({cfg.START_YEAR}-{cfg.END_YEAR})")
    ax.set_ylabel("Port calls / day")
    _save(fig, "layer2_full_timeline.png", dpi=140)


def storm_example(panel, lag_row, name):
    g = panel[panel["SID"] == lag_row["SID"]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(g["days_from_approach"], g["portcalls"], marker="o", ms=3, color=ACTUAL_C, label="Actual")
    ax.plot(g["days_from_approach"], g["expected"], color=EXPECTED_C, lw=1.5, label="Expected (counterfactual)")
    ax.axvline(0, color="black", ls="--", lw=1, label="Closest approach")
    if pd.notna(lag_row["onset_lag"]):
        ax.axvline(lag_row["onset_lag"], color="orange", ls=":", lw=2, label="Onset")
    if pd.notna(lag_row["recovery_lag"]):
        ax.axvline(lag_row["recovery_lag"], color="green", ls=":", lw=2, label="Recovery")
    ax.set_title(f"{name.title()} ({lag_row['SID']}): actual vs. expected port calls")
    ax.set_xlabel("Days from closest approach")
    ax.set_ylabel("Port calls / day")
    ax.legend(fontsize=8)
    _save(fig, "layer2_storm_example.png", dpi=140)


def lag_distributions(lags):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, col, title in zip(axes, ["onset_lag", "recovery_lag"],
                              ["Onset lag", "Recovery lag"]):
        data = lags[col].dropna()
        if len(data):
            ax.hist(data, bins=range(int(data.min()) - 1, int(data.max()) + 2),
                    color="#4c72b0", edgecolor="white")
        ax.axvline(0, color="black", ls="--", lw=1)
        ax.set_title(f"{title} (days from approach)\n(n={len(data)}/{len(lags)} storms)")
        ax.set_xlabel("Days")
    _save(fig, "layer2_lag_distributions.png", dpi=140)


def pipeline_flowchart():
    fig, ax = plt.subplots(figsize=(11, 13))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 22)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eaf1fb", ec="#2f5597"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.15",
                                    fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9.5)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=14, color="#333333", lw=1.3))

    src, out, note = dict(fc="#fdebd0", ec="#b9770e"), dict(fc="#eafaf1", ec="#1e8449"), dict(fc="#f9ebea", ec="#943126")
    box(0.5, 20.2, 4, 1.3, "PortWatch daily\nport calls (2019-2024)", **src)
    box(5.5, 20.2, 4, 1.3, "IBTrACS closest-approach\nstorm characteristics\n(WIND, PRES, RMW, DIST)", **src)
    arrow(2.5, 20.2, 2.5, 19.3)
    box(0.5, 18, 4, 1.3, "Storm windows:\n-10/+30 days per storm,\nunion mask")
    arrow(4.5, 18.65, 5.9, 18.65)
    box(5.9, 18, 3.6, 1.3, "Mask port calls = NaN\ninside any storm window")
    arrow(2.5, 18, 2.5, 16.3)
    box(0.5, 15, 4, 1.3, "Baseline:\nweekday-seasonal median\n+ rolling-median trend,\nfit on non-storm days")
    arrow(2.5, 15, 2.5, 13.3)
    box(0.5, 12, 4, 1.3, "Interpolate trend across\nmasked days\n-> expected(t)")
    arrow(2.5, 12, 2.5, 10.3)
    box(0.5, 9, 4, 1.3, "deviation(t) =\nactual(t) - expected(t)", **out)
    arrow(2.2, 9, 1.2, 7.3)
    box(0.1, 6, 4.2, 1.5, "Onset / recovery lag per storm\n(severe 1-day cliff OR\nsustained moderate dip)")
    arrow(2.2, 6, 2.2, 4.3)
    box(0.1, 3, 4.2, 1.3, "OLS: onset_lag,\nrecovery_lag ~ WIND +\nPRES + RMW + DIST", **out)
    box(0.1, 1.2, 4.2, 1.3, "replaces Layer 1\ncross-sectional OLS\n(trough / recovery)", **note)
    arrow(2.8, 9, 7.4, 7.3)
    box(5.4, 6, 4.2, 1.5, "Storm-window panel of\ndeviation(t), merged with\nGSOD WDSP / VISIB by date")
    arrow(7.5, 6, 7.5, 4.3)
    box(5.4, 3, 4.2, 1.3, "Fixed-effects PanelOLS:\ndeviation ~ WDSP + VISIB\n+ EntityEffects (clustered SE)", **out)
    box(5.4, 1.2, 4.2, 1.3, "re-run of Layer 1 panel\non normalised arrivals", **note)
    ax.set_title("Layer 2 pipeline: counterfactual baseline -> deviation-based models", fontsize=12, pad=14)
    _save(fig, "layer2_flowchart.png")
