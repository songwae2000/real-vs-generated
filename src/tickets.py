"""Loading any of the three feeds into the same shape."""

import json
import os
import subprocess
from datetime import datetime

import numpy as np

PULLED = datetime(2026, 9, 23)
TRAIN_WEEK = ("2026-05-04", "2026-05-11")
TEST_WEEK = ("2026-06-08", "2026-06-15")
PAGE = 50000


def path_for(city, which):
    return f"data/{city.name.lower().replace(' ', '_')}_{which}.json"


def fetch(city, window, out_path):
    """Pages through the window so a row cap cannot silently truncate it."""
    start, end = window
    fields = ",".join((city.category, city.department, city.channel,
                       city.created, city.closed))
    rows, offset = [], 0
    while True:
        page = None
        for _ in range(4):
            result = subprocess.run([
                "curl", "-s", "--max-time", "300", "--retry", "2", "-G", city.endpoint,
                "--data-urlencode", f"$select={fields}",
                "--data-urlencode",
                # half open, because SoQL between is inclusive at both ends and
                # would pull a stray ticket from the following week
                f"$where={city.created} >= '{start}T00:00:00' "
                f"AND {city.created} < '{end}T00:00:00'",
                "--data-urlencode", f"$order={city.created}",
                "--data-urlencode", f"$limit={PAGE}",
                "--data-urlencode", f"$offset={offset}",
            ], capture_output=True, text=True)
            try:
                page = json.loads(result.stdout)
                break
            except json.JSONDecodeError:
                # a page truncated in transit. Nothing partial is ever kept.
                print(f"    page at offset {offset} came back short, retrying",
                      flush=True)
        if page is None:
            raise RuntimeError(f"could not fetch {city.name} at offset {offset}")

        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    json.dump(rows, open(out_path, "w"))
    return rows


def ensure(city):
    """Downloads both weeks for a city if they are not already on disk."""
    for which, window in (("train", TRAIN_WEEK), ("test", TEST_WEEK)):
        out = path_for(city, which)
        if not os.path.exists(out):
            print(f"  fetching {city.name} {which}...", flush=True)
            fetch(city, window, out)


def load(city, which):
    """Returns (features, hours, still_open) with the same keys for every city."""
    rows = []
    for record in json.load(open(path_for(city, which))):
        raw = record.get(city.created)
        if not raw:
            continue
        try:
            created = datetime.fromisoformat(raw)
        except ValueError:
            continue

        closed = record.get(city.closed)
        if closed:
            try:
                hours = (datetime.fromisoformat(closed) - created).total_seconds() / 3600
            except ValueError:
                continue
            if hours < 0:
                continue
            still_open = False
        else:
            hours = (PULLED - created).total_seconds() / 3600
            still_open = True

        rows.append((
            {"category": record.get(city.category) or "(missing)",
             "department": record.get(city.department) or "(missing)",
             "channel": record.get(city.channel) or "(missing)"},
            hours, still_open))

    if city.drop_instant_closes:
        rows = [r for r in rows if r[1] > 1 / 60]
    return rows


def split(rows, threshold):
    """Drops the censored, which is nothing here, and returns features and labels."""
    keep = [(f, h) for f, h, o in rows if not (o and h <= threshold)]
    return [f for f, _ in keep], [h > threshold for _, h in keep]


def median_hours(rows):
    return float(np.median([h for _, h, _ in rows]))
