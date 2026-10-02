from pathlib import Path

import requests


def download_file(url, dest, force=False, chunk_size=1 << 20):
    """Stream `url` to `dest`. Skips the download if the file already exists."""
    dest = Path(dest)
    if dest.exists() and not force:
        print(f"  already have {dest.name}, skipping download")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size):
                f.write(chunk)
    tmp.replace(dest)
    print(f"  saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest
