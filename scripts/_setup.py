"""Shared helpers for the pipeline scripts: makes `src/` importable and
saves model output to results/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from port_typhoon import config as cfg  # noqa: E402


def save_result(name, text):
    """Print `text` and save it to results/<name>.txt."""
    cfg.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (cfg.RESULTS_DIR / f"{name}.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"  saved results/{name}.txt")


def header(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)
