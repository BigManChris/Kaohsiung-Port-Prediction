"""Tropical cyclone data from IBTrACS (NOAA NCEI), and storm windows.

IBTrACS: https://www.ncei.noaa.gov/products/international-best-track-archive
We use the Western Pacific basin file, which covers every storm that can
reach Taiwan.
"""
import pandas as pd

from . import config as cfg
from .download import download_file
from .geo import haversine_km

IBTRACS_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.WP.list.v04r01.csv"
)

TRACK_COLS = [
    "SID", "SEASON", "NAME", "ISO_TIME", "LAT", "LON", "NATURE",
    "USA_STATUS", "USA_WIND", "USA_PRES", "USA_SSHS", "USA_RMW",
    "STORM_SPEED", "STORM_DIR",
]
NUMERIC_COLS = ["SEASON", "LAT", "LON", "USA_WIND", "USA_PRES", "USA_SSHS",
                "USA_RMW", "STORM_SPEED", "STORM_DIR"]


def download_ibtracs(force=False):
    return download_file(IBTRACS_URL, cfg.IBTRACS_RAW, force=force)


def build_storm_tables(ibtracs_path=cfg.IBTRACS_RAW):
    """Filter IBTrACS to storms passing near the port in the study period.

    Returns (tracks, closest): every 3-hourly track point inside the box, and
    one row per storm at its closest approach to the port.
    """
    # Row 1 of the IBTrACS CSV holds units, not data.
    df = pd.read_csv(ibtracs_path, skiprows=[1], usecols=TRACK_COLS,
                     keep_default_na=False, low_memory=False)
    for col in NUMERIC_COLS:
        # IBTrACS uses blank strings for missing values
        df[col] = pd.to_numeric(df[col].replace(r"^\s*$", pd.NA, regex=True), errors="coerce")
    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"])

    box = cfg.STORM_BOX_DEG
    tracks = df[
        df["LAT"].between(cfg.PORT_LAT - box, cfg.PORT_LAT + box)
        & df["LON"].between(cfg.PORT_LON - box, cfg.PORT_LON + box)
        & df["SEASON"].between(cfg.START_YEAR, cfg.END_YEAR)
    ].copy()
    tracks["DIST_FROM_PORT"] = haversine_km(tracks["LAT"], tracks["LON"],
                                            cfg.PORT_LAT, cfg.PORT_LON)

    closest = (tracks.loc[tracks.groupby("SID")["DIST_FROM_PORT"].idxmin()]
               .sort_values("ISO_TIME").reset_index(drop=True))
    return tracks, closest


def load_storms(path=cfg.CLOSEST_APPROACH):
    """One row per storm at closest approach, with an `approach_date` column
    (the calendar day of closest approach, used to align storm windows)."""
    storms = pd.read_csv(path)
    storms["ISO_TIME"] = pd.to_datetime(storms["ISO_TIME"])
    storms["approach_date"] = storms["ISO_TIME"].dt.normalize()
    for col in cfg.STORM_VARS:
        storms[col] = pd.to_numeric(storms[col], errors="coerce")
    return storms


def storm_windows(storms, pre=cfg.PRE_DAYS, post=cfg.POST_DAYS):
    """SID, approach_date, window_start, window_end for each storm."""
    out = storms[["SID", "NAME", "approach_date"]].copy()
    out["window_start"] = out["approach_date"] - pd.Timedelta(days=pre)
    out["window_end"] = out["approach_date"] + pd.Timedelta(days=post)
    return out


def storm_mask(dates, windows):
    """Boolean Series over `dates`: True if the day is inside ANY storm window.

    Windows overlap for back-to-back storms, so this is the union of windows.
    """
    dates = pd.DatetimeIndex(dates)
    mask = pd.Series(False, index=dates)
    for row in windows.itertuples():
        mask |= (dates >= row.window_start) & (dates <= row.window_end)
    return mask


def storm_panel(daily, storms, pre=cfg.PRE_DAYS, post=cfg.POST_DAYS):
    """Stack each storm's window of a daily DataFrame (indexed by date) into a
    long panel with SID and days_from_approach columns.

    Note: a day covered by two overlapping windows appears once per storm.
    """
    pieces = []
    for s in storms.itertuples():
        w = daily.loc[s.approach_date - pd.Timedelta(days=pre):
                      s.approach_date + pd.Timedelta(days=post)].copy()
        w.insert(0, "days_from_approach", (w.index - s.approach_date).days)
        w.insert(0, "SID", s.SID)
        pieces.append(w)
    panel = pd.concat(pieces)
    panel.index.name = "date"
    return panel.reset_index()
