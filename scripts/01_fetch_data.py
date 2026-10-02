"""Step 1: download all raw data directly from the source.

  * IBTrACS (NOAA NCEI)  -> storm tracks near the port + closest approach
  * PortWatch (IMF)      -> daily port calls at Kaohsiung
  * GSOD / ISD (NOAA)    -> daily weather at the nearest station

Usage:
    python scripts/01_fetch_data.py            # fetch anything not yet downloaded
    python scripts/01_fetch_data.py --force    # re-download everything
    python scripts/01_fetch_data.py --only storms port weather
"""
import argparse

from _setup import cfg, header
from port_typhoon import port, storms, weather


def fetch_storms(force):
    header("IBTrACS storm tracks")
    storms.download_ibtracs(force=force)
    tracks, closest = storms.build_storm_tables()
    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    tracks.to_csv(cfg.STORM_TRACKS, index=False)
    closest.to_csv(cfg.CLOSEST_APPROACH, index=False)
    print(f"  {closest['SID'].nunique()} storms passed within {cfg.STORM_BOX_DEG} deg of the port "
          f"({cfg.START_YEAR}-{cfg.END_YEAR})")
    print(f"  saved {cfg.CLOSEST_APPROACH.relative_to(cfg.REPO_ROOT)}")


def fetch_port(force):
    header("PortWatch daily port calls")
    if cfg.PORT_RAW.exists() and not force:
        print(f"  already have {cfg.PORT_RAW.name}, skipping (use --force to refresh)")
        return
    df = port.fetch_port_calls()
    df.to_csv(cfg.PORT_RAW, index=False)
    n_days = (cfg.END_YEAR - cfg.START_YEAR + 1) * 365.25
    print(f"  {len(df)} days ({len(df) / n_days:.0%} coverage), saved {cfg.PORT_RAW.name}")


def fetch_weather(force):
    header("GSOD daily weather")
    if cfg.WEATHER_RAW.exists() and not force:
        print(f"  already have {cfg.WEATHER_RAW.name}, skipping (use --force to refresh)")
        return
    station_id = cfg.WEATHER_STATION_ID
    if station_id is None:
        nearest = weather.nearest_station()
        print(nearest.to_string(index=False))
        station_id = nearest.iloc[0]["station_id"]
    print(f"  using station {station_id}")
    df = weather.fetch_gsod(station_id)
    df.to_csv(cfg.WEATHER_RAW, index=False)
    print(f"  saved {cfg.WEATHER_RAW.name}")


STEPS = {"storms": fetch_storms, "port": fetch_port, "weather": fetch_weather}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="re-download even if files exist")
    parser.add_argument("--only", nargs="+", choices=STEPS, default=list(STEPS))
    args = parser.parse_args()
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in args.only:
        STEPS[name](args.force)
