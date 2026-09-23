"""A harder task: predict speed *within* a complaint type.

The headline task is close to a lookup, because complaint type alone carries
almost all of the signal, and a pairwise generator reproduces a single-column
relationship for free. Labelling each ticket against its own complaint type's
median removes that column as a signal: every type is 50/50 by construction,
so whatever skill remains has to come from the other columns and from how they
interact.
"""

import numpy as np

from src.prepare import FEATURES


def stratified_label(rows, min_per_type=400):
    """Slow relative to the ticket's own complaint type, not to the shop overall."""
    by_type = {}
    for features, hours, still_open in rows:
        by_type.setdefault(features["complaint_type"], []).append(hours)

    medians = {t: float(np.median(h)) for t, h in by_type.items()
               if len(h) >= min_per_type}

    out_features, out_labels = [], []
    for features, hours, still_open in rows:
        threshold = medians.get(features["complaint_type"])
        if threshold is None:
            continue
        if still_open and hours <= threshold:
            continue
        out_features.append(features)
        out_labels.append(hours > threshold)
    return out_features, out_labels, medians
