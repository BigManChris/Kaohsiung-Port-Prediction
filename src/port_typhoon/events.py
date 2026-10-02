"""Per-storm disruption metrics.

Layer 1 (`layer1_storm_summary`): compares arrivals with a simple pre-storm
average (days -10 to -2).

Layer 2 (`detect_onset_recovery`): compares arrivals with the counterfactual
baseline. For each storm it finds

  onset_lag     first day (relative to closest approach, may be negative) when
                activity drops meaningfully below the baseline, via either
                (a) a severe single-day cliff: deviation < -Z_SEVERE * sigma, or
                (b) a sustained moderate dip: deviation < -Z_MODERATE * sigma for
                    MIN_RUN consecutive days
                whichever comes first. Kaohsiung typhoon closures are often a
                one-day stop followed by a catch-up surge, which rule (a) catches.
  recovery_lag  first day after onset where deviation is back above
                -Z_MODERATE * sigma.

sigma is the residual standard deviation on non-storm days.
"""
import numpy as np
import pandas as pd

from . import config as cfg


# ---------------------------------------------------------------------------
# Layer 1
# ---------------------------------------------------------------------------
def layer1_storm_summary(panel, value="TOTAL_ARRIVALS", baseline_days=cfg.L1_BASELINE_DAYS):
    """Trough depth and days-to-recover per storm vs the pre-storm average."""
    rows = []
    for sid, g in panel.groupby("SID", sort=False):
        g = g.sort_values("days_from_approach")
        pre = g[g["days_from_approach"].between(*baseline_days)][value]
        baseline = pre.mean()
        post = g[g["days_from_approach"] > 0]
        recovered = post[post[value] >= baseline]
        rows.append({
            "SID": sid,
            "pre_storm_avg": baseline,
            "trough": g[value].min(),
            "trough_drop": baseline - g[value].min(),
            "days_to_recover": recovered["days_from_approach"].iloc[0] if len(recovered) else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Layer 2
# ---------------------------------------------------------------------------
def _first_run_start(flags, min_run):
    """First day starting a run of >= min_run calendar-consecutive True flags."""
    run_start, run_len, prev = None, 0, None
    for day, flag in flags.items():
        if flag:
            if prev is not None and day == prev + 1 and run_len > 0:
                run_len += 1
            else:
                run_start, run_len = day, 1
            if run_len >= min_run:
                return run_start
        else:
            run_len = 0
        prev = day
    return None


def _onset(dev, thr_severe, thr_moderate, min_run):
    severe = dev.index[dev < -thr_severe]
    candidates = [severe.min() if len(severe) else None,
                  _first_run_start(dev < -thr_moderate, min_run)]
    candidates = [c for c in candidates if c is not None]
    return min(candidates) if candidates else None


def _recovery(dev, onset, thr_moderate):
    after = dev[(dev.index > onset) & (dev >= -thr_moderate)]
    return after.index.min() if len(after) else None


def detect_onset_recovery(panel, resid_std, z_severe=cfg.Z_SEVERE,
                          z_moderate=cfg.Z_MODERATE, min_run=cfg.MIN_RUN):
    """Onset/recovery lags per storm from a panel with a `deviation` column."""
    thr_severe, thr_moderate = z_severe * resid_std, z_moderate * resid_std
    window_len = cfg.PRE_DAYS + cfg.POST_DAYS + 1
    rows = []
    for sid, g in panel.groupby("SID", sort=False):
        dev = g.set_index("days_from_approach")["deviation"].dropna().sort_index()
        onset = _onset(dev, thr_severe, thr_moderate, min_run)
        recovery = _recovery(dev, onset, thr_moderate) if onset is not None else None
        rows.append({
            "SID": sid,
            "onset_lag": onset,
            "recovery_lag": recovery,
            "duration_days": recovery - onset if onset is not None and recovery is not None else None,
            "trough_deviation": dev.min() if len(dev) else None,
            "n_obs_in_window": len(dev),
            "pct_window_missing": 1 - len(dev) / window_len,
        })
    out = pd.DataFrame(rows)
    for col in ["onset_lag", "recovery_lag", "duration_days"]:
        out[col] = pd.to_numeric(out[col])
    return out
