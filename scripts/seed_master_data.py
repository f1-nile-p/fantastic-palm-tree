#!/usr/bin/env python3
"""Seed master data by uploading template CSVs to the running backend."""

import os
import sys
import pathlib
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"


def upload_csv(endpoint: str, filepath: pathlib.Path) -> None:
    if not filepath.exists():
        print(f"  ⚠  File not found: {filepath}", file=sys.stderr)
        return
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}{endpoint}",
            files={"file": (filepath.name, f, "text/csv")},
            timeout=30,
        )
    if resp.ok:
        data = resp.json()
        print(f"  ✅ {filepath.name}: uploaded {len(data)} records")
    else:
        print(f"  ❌ {filepath.name}: {resp.status_code} – {resp.text[:200]}", file=sys.stderr)


def main() -> None:
    print(f"Seeding master data at {BASE_URL} …\n")
    upload_csv("/api/master-data/items/upload", TEMPLATES_DIR / "items_template.csv")
    upload_csv("/api/master-data/uoms/upload", TEMPLATES_DIR / "uom_template.csv")
    print("\nDone.")


if __name__ == "__main__":
    main()
