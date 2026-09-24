"""Bootstrap intervals, so every figure carries its own uncertainty.

A bare AUC of 0.494 invites the obvious question of whether it differs from
chance at all. These answer it. Comparisons between two arms resample the test
set once and score both on the same resample, because the two scores are
measured on the same tickets and are not independent.
"""

import numpy as np
from sklearn.metrics import roc_auc_score

RESAMPLES = 1000
SEED = 20260924


def _resample_indices(n, rng, draws):
    return rng.integers(0, n, size=(draws, n))


def auc_interval(y_true, scores, draws=RESAMPLES):
    """Point estimate and a 95% percentile interval for one arm."""
    y = np.asarray(y_true)
    s = np.asarray(scores, dtype=float)
    rng = np.random.default_rng(SEED)

    point = roc_auc_score(y, s)
    boot = []
    for idx in _resample_indices(len(y), rng, draws):
        if len(np.unique(y[idx])) < 2:
            continue
        boot.append(roc_auc_score(y[idx], s[idx]))

    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, lo, hi


def auc_difference(y_true, scores_a, scores_b, draws=RESAMPLES):
    """Paired interval for (A minus B), both scored on the same resample."""
    y = np.asarray(y_true)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    rng = np.random.default_rng(SEED)

    point = roc_auc_score(y, a) - roc_auc_score(y, b)
    boot = []
    for idx in _resample_indices(len(y), rng, draws):
        if len(np.unique(y[idx])) < 2:
            continue
        boot.append(roc_auc_score(y[idx], a[idx]) - roc_auc_score(y[idx], b[idx]))

    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, lo, hi


def versus_chance(lo, hi):
    """Where the interval sits relative to 0.5, with direction.

    An interval that excludes 0.5 from below is significantly worse than
    guessing, which is a different finding from being better than it.
    """
    if lo > 0.5:
        return "above"
    if hi < 0.5:
        return "below"
    return "indistinguishable"


def conditional_lookup(train_features, train_labels, test_features, columns):
    """Best achievable using only these columns: the fitted conditional rate.

    This is the information ceiling for any rule that reasons over those
    columns, so it separates "the columns are weak" from "the rule is weak".
    """
    table, counts = {}, {}
    for row, y in zip(train_features, train_labels):
        key = tuple(row[c] for c in columns)
        table[key] = table.get(key, 0) + int(y)
        counts[key] = counts.get(key, 0) + 1

    overall = float(np.mean(train_labels))
    rates = {k: table[k] / counts[k] for k in counts}
    return [rates.get(tuple(row[c] for c in columns), overall) for row in test_features]
