"""Step 7: generate every figure in figures/. Run steps 02-06 first."""
import pandas as pd

from _setup import cfg, header
from port_typhoon import plots
from port_typhoon.port import load_port_calls
from port_typhoon.storms import load_storms, storm_panel, storm_windows

if __name__ == "__main__":
    storms = load_storms()
    port = load_port_calls()
    cf = pd.read_csv(cfg.COUNTERFACTUAL, parse_dates=["date"], index_col="date")
    lags = pd.read_csv(cfg.DEVIATION_LAGS)

    header("Data overview")
    plots.storm_classification(storms)
    plots.storms_per_year(storms)
    plots.acf_port_calls(port)
    plots.stl_decomposition(port)

    header("Layer 2")
    plots.full_timeline(cf, storm_windows(storms))
    plots.lag_distributions(lags)
    plots.pipeline_flowchart()

    example = lags[lags["NAME"] == cfg.EXAMPLE_STORM]
    if len(example):
        panel = storm_panel(cf[["portcalls", "expected"]], storms)
        plots.storm_example(panel, example.iloc[0], cfg.EXAMPLE_STORM)
    else:
        print(f"  EXAMPLE_STORM {cfg.EXAMPLE_STORM!r} not found, skipping example figure")
