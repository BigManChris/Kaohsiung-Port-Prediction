"""Step 5 (Layer 2): onset / recovery lags per storm, and OLS on storm
characteristics. Replaces Layer 1's trough / days-to-recover regression.

Run 04_layer2_baseline.py first.
"""
import pandas as pd
import statsmodels.formula.api as smf

from _setup import cfg, header, save_result
from port_typhoon.events import detect_onset_recovery
from port_typhoon.storms import load_storms, storm_panel


def load_counterfactual():
    cf = pd.read_csv(cfg.COUNTERFACTUAL, parse_dates=["date"], index_col="date")
    resid_std = cf.loc[~cf["in_storm_window"], "deviation"].std()
    return cf, resid_std


if __name__ == "__main__":
    storms = load_storms()
    cf, resid_std = load_counterfactual()
    panel = storm_panel(cf[["portcalls", "expected", "deviation"]], storms)

    lags = detect_onset_recovery(panel, resid_std).merge(
        storms[["SID", "NAME", *cfg.STORM_VARS]], on="SID", how="left")
    lags.to_csv(cfg.DEVIATION_LAGS, index=False)
    header("Per-storm onset / recovery")
    print(lags.round(2).to_string(index=False))

    rhs = " + ".join(cfg.STORM_VARS)
    out = [
        f"Thresholds: sigma = {resid_std:.2f} port calls/day; "
        f"severe = {cfg.Z_SEVERE} sigma = {cfg.Z_SEVERE * resid_std:.2f}; "
        f"moderate = {cfg.Z_MODERATE} sigma = {cfg.Z_MODERATE * resid_std:.2f} "
        f"for {cfg.MIN_RUN}+ days",
        f"Onset detected for {lags['onset_lag'].notna().sum()}/{len(lags)} storms; "
        f"recovery for {lags['recovery_lag'].notna().sum()}/{len(lags)}",
        "",
    ]
    for target in ["onset_lag", "recovery_lag", "duration_days"]:
        data = lags.dropna(subset=[target, *cfg.STORM_VARS])
        if len(data) < len(cfg.STORM_VARS) + 2:
            out.append(f"Skipping {target}: only {len(data)} usable storms\n")
            continue
        model = smf.ols(f"{target} ~ {rhs}", data=data).fit()
        out.append(f"===== Layer 2 OLS: {target} ~ {rhs}  (N={len(data)}) =====\n{model.summary()}\n")
    header("Layer 2 lag regressions")
    save_result("layer2_lags_ols", "\n".join(out))
