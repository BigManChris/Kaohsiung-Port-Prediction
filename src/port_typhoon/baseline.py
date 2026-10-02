"""Counterfactual ("no storm") baseline for daily port calls (Layer 2).

Method: weekday-seasonal + smoothed-trend decomposition, fitted only on days
outside every storm window, then interpolated across the masked days.

  1. Mask every day inside any storm's -10/+30 day window as missing.
  2. Seasonal component: median port calls for each day of the week, using
     only unmasked days.
  3. Trend: deseasonalise the unmasked data, take a centred 29-day rolling
     median, and linearly interpolate it across masked or missing days
     (flat at the ends of the series).
  4. expected(t) = trend(t) + seasonal[weekday(t)]
     deviation(t) = actual(t) - expected(t)

Why not SARIMAX: with around half of all days masked (44 overlapping storm
windows), the AR terms extrapolate through long gaps and drift the expected
level downward across a storm window. The rolling-median approach has no
autoregressive memory, so it holds a stable baseline instead.
"""
import pandas as pd

from . import config as cfg
from .storms import storm_mask, storm_windows


def fit_baseline(series, mask, trend_window=cfg.TREND_WINDOW):
    """Fit the baseline to `series` with `mask`ed days excluded.

    Returns a DataFrame with expected, trend and seasonal columns, and the
    weekday seasonal profile (Mon=0 .. Sun=6).
    """
    masked = series.where(~mask)
    weekday = pd.Series(series.index.dayofweek, index=series.index, name="weekday")

    seasonal_profile = masked.groupby(weekday).median()
    seasonal = weekday.map(seasonal_profile)

    trend = ((masked - seasonal)
             .rolling(trend_window, center=True, min_periods=7).median()
             .interpolate(limit_direction="both"))

    fitted = pd.DataFrame({"expected": trend + seasonal, "trend": trend, "seasonal": seasonal})
    return fitted, seasonal_profile


def build_counterfactual(port, storms):
    """Actual vs expected port calls for every day, plus storm-window flag.

    Returns (df, resid_std) where resid_std is the standard deviation of the
    deviation on non-storm days, used to scale the Layer 2 thresholds.
    """
    actual = port["portcalls"]
    mask = storm_mask(actual.index, storm_windows(storms))
    fitted, seasonal_profile = fit_baseline(actual, mask)

    df = pd.DataFrame({"portcalls": actual}).join(fitted)
    df["deviation"] = df["portcalls"] - df["expected"]
    df["in_storm_window"] = mask

    resid_std = df.loc[~df["in_storm_window"], "deviation"].std()
    return df, resid_std, seasonal_profile
