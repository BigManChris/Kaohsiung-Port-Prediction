"""Step 2 (Layer 1): cross-sectional OLS across storms.

For each storm, measure disruption against a simple pre-storm average
(mean arrivals on days -10 to -2):
    trough_drop      = pre-storm average - minimum arrivals in the window
    days_to_recover  = first day after approach with arrivals >= pre-storm average
then regress each on storm characteristics at closest approach.
"""
import statsmodels.formula.api as smf

from _setup import cfg, header, save_result
from port_typhoon.events import layer1_storm_summary
from port_typhoon.port import load_port_calls
from port_typhoon.storms import load_storms, storm_panel


def build_layer1_panel():
    port = load_port_calls()
    daily = port[cfg.VESSEL_TYPES].copy()
    daily["TOTAL_ARRIVALS"] = port["portcalls"]
    return storm_panel(daily, load_storms())


if __name__ == "__main__":
    storms = load_storms()
    panel = build_layer1_panel()
    panel.to_csv(cfg.LAYER1_PANEL, index=False)
    print(f"Saved {cfg.LAYER1_PANEL.relative_to(cfg.REPO_ROOT)} "
          f"({len(panel)} storm-days, {panel['SID'].nunique()} storms)")

    summary = layer1_storm_summary(panel).merge(
        storms[["SID", "NAME", *cfg.STORM_VARS]], on="SID", how="left")
    summary.to_csv(cfg.LAYER1_SUMMARY, index=False)
    header("Per-storm summary")
    print(summary.round(2).to_string(index=False))

    rhs = " + ".join(cfg.STORM_VARS)
    out = []
    for target in ["trough_drop", "days_to_recover"]:
        data = summary.dropna(subset=[target, *cfg.STORM_VARS])
        model = smf.ols(f"{target} ~ {rhs}", data=data).fit()
        out.append(f"===== Layer 1 OLS: {target} ~ {rhs}  (N={len(data)}) =====\n{model.summary()}\n")
    header("Layer 1 cross-sectional OLS")
    save_result("layer1_ols", "\n".join(out))
