"""Step 3 (Layer 1): fixed-effects panel regression.

    TOTAL_ARRIVALS ~ WDSP + VISIB + storm fixed effects

Panel unit = storm, time = days from closest approach. Standard errors are
clustered by storm. WDSP is mean wind speed (knots), VISIB is visibility (miles).
Run 02_layer1_ols.py first (it builds the storm-window panel).
"""
import pandas as pd
from linearmodels.panel import PanelOLS

from _setup import cfg, header, save_result
from port_typhoon.weather import load_weather

if __name__ == "__main__":
    panel = pd.read_csv(cfg.LAYER1_PANEL, parse_dates=["date"])
    panel = panel.merge(load_weather()[["WDSP", "VISIB"]], left_on="date",
                        right_index=True, how="left")

    data = (panel.dropna(subset=["TOTAL_ARRIVALS", "WDSP", "VISIB"])
            .set_index(["SID", "days_from_approach"]))
    print(f"Rows dropped for missing arrivals/weather: {len(panel) - len(data)} of {len(panel)}")

    res = PanelOLS.from_formula("TOTAL_ARRIVALS ~ WDSP + VISIB + EntityEffects", data=data) \
        .fit(cov_type="clustered", cluster_entity=True)
    header("Layer 1 panel regression")
    save_result("layer1_panel", str(res))
