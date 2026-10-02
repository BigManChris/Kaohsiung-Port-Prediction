"""Step 4 (Layer 2): counterfactual "no storm" baseline of daily port calls.

See src/port_typhoon/baseline.py for the method. Saves the actual, expected
and deviation series for every day to data/processed/counterfactual_baseline.csv.
"""
from _setup import cfg, header, save_result
from port_typhoon.baseline import build_counterfactual
from port_typhoon.port import load_port_calls
from port_typhoon.storms import load_storms

if __name__ == "__main__":
    cf, resid_std, seasonal = build_counterfactual(load_port_calls(), load_storms())
    cf.to_csv(cfg.COUNTERFACTUAL)
    print(f"Saved {cfg.COUNTERFACTUAL.relative_to(cfg.REPO_ROOT)}")

    n = len(cf)
    lines = [
        f"Days in sample:                 {n}",
        f"Days with port data:            {cf['portcalls'].notna().sum()}",
        f"Days inside a storm window:     {cf['in_storm_window'].sum()} ({cf['in_storm_window'].mean():.1%})",
        f"Days used to fit the baseline:  {(cf['portcalls'].notna() & ~cf['in_storm_window']).sum()}",
        "",
        "Weekday seasonal component (median port calls, Mon=0 .. Sun=6):",
        seasonal.round(1).to_string(),
        "",
        f"Residual std on non-storm days (sigma): {resid_std:.2f} port calls/day",
    ]
    header("Layer 2 baseline")
    save_result("layer2_baseline", "\n".join(lines))
