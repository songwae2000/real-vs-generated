"""Pulls every 311 ticket created in a window, paginating past the API row cap.

Two things the first pull got wrong, both fixed here:

  - `$limit=50000` silently truncated a 332k-row month to its last five days,
    so the "month" was five days and day-of-week did not overlap between the
    train and test windows. This paginates until the window is exhausted.

  - Filtering to closed tickets drops the ones still open, which are the
    slowest. This keeps them: an open ticket older than the threshold is known
    to be slow, and one younger than it is censored and gets excluded from the
    label rather than silently counted as fast.
"""

import json
import subprocess
import sys

BASE = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGE = 50000
FIELDS = ("unique_key,created_date,closed_date,agency,complaint_type,descriptor,"
          "borough,open_data_channel_type,location_type,status")


def fetch_window(start, end, out_path):
    rows, offset = [], 0
    while True:
        cmd = [
            "curl", "-s", "--max-time", "120", "-G", BASE,
            "--data-urlencode", f"$select={FIELDS}",
            "--data-urlencode",
            f"$where=created_date between '{start}T00:00:00' and '{end}T00:00:00'",
            "--data-urlencode", "$order=unique_key",
            "--data-urlencode", f"$limit={PAGE}",
            "--data-urlencode", f"$offset={offset}",
        ]
        page = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
        rows.extend(page)
        print(f"  {out_path}: +{len(page):>6}  total {len(rows):>7}", flush=True)
        if len(page) < PAGE:
            break
        offset += PAGE

    json.dump(rows, open(out_path, "w"))
    closed = sum(1 for r in rows if r.get("closed_date"))
    print(f"  {out_path}: {len(rows)} tickets, {closed} closed, "
          f"{len(rows) - closed} still open")
    return rows


if __name__ == "__main__":
    # complete calendar weeks, Monday to Monday, five weeks apart
    fetch_window("2026-05-04", "2026-05-11", "train_week.json")
    fetch_window("2026-06-08", "2026-06-15", "test_week.json")
