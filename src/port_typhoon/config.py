"""Project-wide settings: paths, study area, study period and model parameters.

Change values here rather than inside individual scripts, so every stage of the
pipeline stays consistent.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = REPO_ROOT / "figures"
RESULTS_DIR = REPO_ROOT / "results"

# Raw inputs (written by scripts/01_fetch_data.py)
IBTRACS_RAW = RAW_DIR / "ibtracs.WP.list.v04r01.csv"        # large, git-ignored
PORT_RAW = RAW_DIR / "portwatch_kaohsiung_daily.csv"
WEATHER_RAW = RAW_DIR / "gsod_kaohsiung.csv"

# Processed outputs
STORM_TRACKS = PROCESSED_DIR / "storm_tracks_near_port.csv"
CLOSEST_APPROACH = PROCESSED_DIR / "closest_approach_storms.csv"
LAYER1_PANEL = PROCESSED_DIR / "layer1_storm_panel.csv"
LAYER1_SUMMARY = PROCESSED_DIR / "layer1_storm_summary.csv"
COUNTERFACTUAL = PROCESSED_DIR / "counterfactual_baseline.csv"
DEVIATION_LAGS = PROCESSED_DIR / "layer2_deviation_lags.csv"
LAYER2_PANEL = PROCESSED_DIR / "layer2_normalised_panel.csv"

# ---------------------------------------------------------------------------
# Study area and period
# ---------------------------------------------------------------------------
PORT_NAME = "Kaohsiung"
PORT_LAT, PORT_LON = 22.60, 120.28
START_YEAR, END_YEAR = 2019, 2024

# Storm track points within +/- this many degrees of the port are kept
STORM_BOX_DEG = 4.0

# Storm window, in days relative to the day of closest approach
PRE_DAYS = 10
POST_DAYS = 30

# Weather station: None = pick the nearest Taiwanese ISD station with full
# coverage of the study period (Kaohsiung International Airport, 46740099999).
WEATHER_STATION_ID = None

# Storm-level characteristics used as regressors
STORM_VARS = ["USA_WIND", "USA_PRES", "USA_RMW", "DIST_FROM_PORT"]

# PortWatch vessel-type columns (their sum equals total port calls)
VESSEL_TYPES = [
    "portcalls_container",
    "portcalls_dry_bulk",
    "portcalls_general_cargo",
    "portcalls_roro",
    "portcalls_tanker",
]

# ---------------------------------------------------------------------------
# Layer 1
# ---------------------------------------------------------------------------
# Pre-storm reference period for the simple baseline (days from approach)
L1_BASELINE_DAYS = (-10, -2)

# ---------------------------------------------------------------------------
# Layer 2
# ---------------------------------------------------------------------------
TREND_WINDOW = 29      # days, centred rolling median for the baseline trend
Z_SEVERE = 3.0         # single-day cliff threshold (x residual std)
Z_MODERATE = 1.5       # sustained-dip / recovery threshold (x residual std)
MIN_RUN = 2            # consecutive days required for the moderate rule

# Storm shown in figures/layer2_storm_example.png (Krathon made landfall at
# Kaohsiung in Oct 2024)
EXAMPLE_STORM = "KRATHON"
