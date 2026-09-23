"""Turns raw 311 tickets into feature rows and a slow/fast label."""

import json
from datetime import datetime

# everything here is known when the ticket is opened, so an agent could use it
FEATURES = ("agency", "complaint_type", "borough", "open_data_channel_type",
            "location_type")

# the pull date. Anything still open by now is months old, so far past any
# threshold used here that it is known slow rather than censored.
PULLED = datetime(2026, 9, 23)


def _row(record):
    try:
        created = datetime.fromisoformat(record["created_date"])
    except (KeyError, TypeError, ValueError):
        return None

    closed = record.get("closed_date")
    if closed:
        try:
            hours = (datetime.fromisoformat(closed) - created).total_seconds() / 3600
        except ValueError:
            return None
        if hours < 0:          # closed before opened, an known artefact of this feed
            return None
        still_open = False
    else:
        hours = (PULLED - created).total_seconds() / 3600
        still_open = True

    features = {f: (record.get(f) or "(missing)") for f in FEATURES}
    return features, hours, still_open


def load(path):
    rows = []
    for record in json.load(open(path)):
        parsed = _row(record)
        if parsed:
            rows.append(parsed)
    return rows


def label(rows, threshold):
    """Slow if it took longer than the threshold. Open tickets are already slow.

    Returns the feature dicts and labels for rows whose label is determined.
    An open ticket younger than the threshold would be censored, but none are.
    """
    features, labels = [], []
    for feats, hours, still_open in rows:
        if still_open and hours <= threshold:
            continue        # censored: cannot say yet. None of these exist here.
        features.append(feats)
        labels.append(hours > threshold)
    return features, labels
