"""Step 6 (Layer 2): Layer 1's panel regression re-run on normalised activity.

    deviation ~ WDSP + VISIB + storm fixed effects

deviation = actual - counterfactual, so trend and weekly seasonality are
removed before the regression, and the WDSP / VISIB coefficients read as
port calls relative to normal. Run 04_layer2_baseline.py first.
"""
import pandas as pd
from linearmodels.panel import PanelOLS

from _setup import cfg, header, save_result
from port_typhoon.storms import load_storms, storm_panel
from port_typhoon.weather import load_weather

if __name__ == "__main__":
    cf = pd.read_csv(cfg.COUNTERFACTUAL, parse_dates=["date"], index_col="date")
    daily = cf[["portcalls", "expected", "deviation"]].join(load_weather()[["WDSP", "VISIB"]])
    panel = storm_panel(daily, load_storms())
    panel.to_csv(cfg.LAYER2_PANEL, index=False)
    print(f"Saved {cfg.LAYER2_PANEL.relative_to(cfg.REPO_ROOT)}")

    data = (panel.dropna(subset=["deviation", "WDSP", "VISIB"])
            .set_index(["SID", "days_from_approach"]))
    print(f"Rows dropped for missing data: {len(panel) - len(data)} of {len(panel)}")

    res = PanelOLS.from_formula("deviation ~ WDSP + VISIB + EntityEffects", data=data) \
        .fit(cov_type="clustered", cluster_entity=True)
    header("Layer 2 panel regression (normalised)")
    save_result("layer2_panel", str(res))
