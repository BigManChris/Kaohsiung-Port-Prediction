"""Daily weather at the port from NOAA's Global Surface Summary of the Day
(GSOD), which is the daily summary of the Integrated Surface Database (ISD).

Station list: https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv
Daily data:   https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/<year>/<station>.csv

Units (GSOD): WDSP / MXSPD / GUST in knots, VISIB in miles, SLP / STP in hPa,
PRCP in inches.
"""
import pandas as pd

from . import config as cfg
from .geo import haversine_km

ISD_HISTORY_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
GSOD_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/{station}.csv"

KEEP_COLS = ["STATION", "DATE", "FRSHTT", "GUST", "MXSPD", "PRCP", "SLP", "STP", "VISIB", "WDSP"]

# GSOD placeholders for "no data"
MISSING_CODES = {
    "GUST": 999.9, "MXSPD": 999.9, "SLP": 9999.9, "STP": 9999.9,
    "VISIB": 999.9, "WDSP": 999.9, "PRCP": 99.99,
}


def nearest_station(n=5):
    """Nearest Taiwanese ISD stations that cover the whole study period."""
    st = pd.read_csv(ISD_HISTORY_URL, dtype={"USAF": str, "WBAN": str})
    st = st[(st["CTRY"] == "TW")
            & (st["BEGIN"] <= cfg.START_YEAR * 10000 + 101)
            & (st["END"] >= cfg.END_YEAR * 10000 + 1231)].copy()
    st["station_id"] = st["USAF"].str.zfill(6) + st["WBAN"].str.zfill(5)
    st["dist_to_port_km"] = haversine_km(st["LAT"], st["LON"], cfg.PORT_LAT, cfg.PORT_LON)
    return st.sort_values("dist_to_port_km").head(n)[
        ["station_id", "STATION NAME", "LAT", "LON", "dist_to_port_km"]]


def fetch_gsod(station_id):
    frames = []
    for year in range(cfg.START_YEAR, cfg.END_YEAR + 1):
        url = GSOD_URL.format(year=year, station=station_id)
        yearly = pd.read_csv(url, dtype={"STATION": str})
        frames.append(yearly[KEEP_COLS])
        print(f"  {year}: {len(yearly)} days")
    return pd.concat(frames, ignore_index=True)


def load_weather(path=cfg.WEATHER_RAW):
    """Daily weather indexed by date, with GSOD missing-value codes set to NaN."""
    w = pd.read_csv(path, dtype={"STATION": str, "FRSHTT": str})
    w.columns = [c.strip() for c in w.columns]
    w["DATE"] = pd.to_datetime(w["DATE"])
    for col, code in MISSING_CODES.items():
        w[col] = pd.to_numeric(w[col], errors="coerce").mask(lambda s: s == code)
    return w.drop(columns="STATION").set_index("DATE").rename_axis("date")
