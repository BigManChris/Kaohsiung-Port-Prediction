"""Daily port calls at Kaohsiung from IMF PortWatch.

PortWatch: https://portwatch.imf.org  (Daily Ports Data, ArcGIS feature service)

The API returns at most ~1,000-2,000 records per request, so results are paged
with `resultOffset`. The original project requested one page per year and
silently lost ~45% of days when a year was truncated; paging fixes that.
"""
import pandas as pd
import requests

from . import config as cfg

PORTWATCH_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Ports_Data/FeatureServer/0/query"
)
PAGE_SIZE = 1000


def fetch_port_calls():
    """Download the daily port-calls series and return a tidy DataFrame."""
    where = (f"portname = '{cfg.PORT_NAME}' AND year >= {cfg.START_YEAR} "
             f"AND year <= {cfg.END_YEAR}")
    records, offset = [], 0
    while True:
        params = {
            "where": where,
            "outFields": "*",
            "orderByFields": "year ASC, month ASC, day ASC",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "json",
        }
        r = requests.get(PORTWATCH_URL, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"PortWatch API error: {data['error']}")
        page = [f["attributes"] for f in data.get("features", [])]
        records.extend(page)
        print(f"  fetched {len(records)} rows")
        if not page or (len(page) < PAGE_SIZE and not data.get("exceededTransferLimit")):
            break
        offset += len(page)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    missing = [c for c in ["portcalls", *cfg.VESSEL_TYPES] if c not in df.columns]
    if missing:
        raise KeyError(f"PortWatch response is missing expected columns: {missing}. "
                       f"Columns returned: {sorted(df.columns)}")
    df = (df[["date", "portcalls", *cfg.VESSEL_TYPES]]
          .drop_duplicates("date").sort_values("date").reset_index(drop=True))
    return df


def load_port_calls(path=cfg.PORT_RAW):
    """Daily series indexed by every calendar day (missing days -> NaN)."""
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    full = pd.date_range(f"{cfg.START_YEAR}-01-01", f"{cfg.END_YEAR}-12-31", freq="D")
    df = df.reindex(full)
    df.index.name = "date"
    return df
