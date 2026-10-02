"""Run the whole analysis (steps 02-07) in order.

Data is fetched separately with 01_fetch_data.py, so the analysis can be
re-run offline from the files in data/raw/.
"""
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["02_layer1_ols.py", "03_layer1_panel.py", "04_layer2_baseline.py",
         "05_layer2_lags_ols.py", "06_layer2_panel.py", "07_figures.py"]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n\n########## {step} ##########")
        runpy.run_path(str(HERE / step), run_name="__main__")
    print("\nAll steps finished. See results/ and figures/.")
