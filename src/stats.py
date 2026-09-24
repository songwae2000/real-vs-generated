"""Bootstrap intervals, so every figure carries its own uncertainty.

A bare AUC of 0.494 invites the obvious question of whether it differs from
chance at all. These answer it. Comparisons between two arms resample the test
set once and score both on the same resample, because the two scores are
measured on the same tickets and are not independent.

Two resampling units are available and they do not agree. Resampling tickets
treats every row as an independent observation. A prior is a function of the
category, so it takes one value for every ticket in a category, and the
independent unit is the category rather than the ticket. San Francisco has 37
categories against 17,007 test rows, so the difference is not cosmetic: the
ticket interval is roughly twenty times too narrow for any claim about how well
a rule set generalises to work it has not seen. Both are reported.
"""

import numpy as np
from sklearn.metrics import roc_auc_score

RESAMPLES = 1000
CLUSTER_RESAMPLES = 2000
SEED = 20260924


def _resample_indices(n, rng, draws):
    return rng.integers(0, n, size=(draws, n))


def _cluster_draw(groups, rng):
    """One resample that draws whole categories with replacement."""
    keys = np.unique(groups)
    where = {k: np.flatnonzero(groups == k) for k in keys}
    picked = rng.choice(keys, size=len(keys), replace=True)
    return np.concatenate([where[k] for k in picked])


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


def auc_interval_clustered(y_true, scores, groups, draws=CLUSTER_RESAMPLES):
    """Point estimate and interval resampling whole categories.

    The honest unit when the scores under test are constant within a category.
    """
    y = np.asarray(y_true)
    s = np.asarray(scores, dtype=float)
    g = np.asarray(groups)
    rng = np.random.default_rng(SEED)

    point = roc_auc_score(y, s)
    boot = []
    for _ in range(draws):
        idx = _cluster_draw(g, rng)
        if len(np.unique(y[idx])) < 2:
            continue
        boot.append(roc_auc_score(y[idx], s[idx]))

    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, lo, hi


def auc_difference_clustered(y_true, scores_a, scores_b, groups,
                             draws=CLUSTER_RESAMPLES):
    """Paired difference resampling whole categories rather than tickets."""
    y = np.asarray(y_true)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    g = np.asarray(groups)
    rng = np.random.default_rng(SEED)

    point = roc_auc_score(y, a) - roc_auc_score(y, b)
    boot = []
    for _ in range(draws):
        idx = _cluster_draw(g, rng)
        if len(np.unique(y[idx])) < 2:
            continue
        boot.append(roc_auc_score(y[idx], a[idx]) - roc_auc_score(y[idx], b[idx]))

    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, lo, hi


def permutation_interval(values_by_group, groups, y_true, draws=CLUSTER_RESAMPLES):
    """What the same rule set scores once its verdicts are shuffled.

    Holds everything structural: the number of categories, how many rows sit in
    each, and the exact multiset of scores the rules hand out. Only the pairing
    of verdict to category is destroyed. Whatever this reaches is available
    from partitioning a taxonomy at all, with no domain reasoning in it, so it
    is the baseline the headline number has to clear.
    """
    y = np.asarray(y_true)
    g = np.asarray(groups)
    keys = sorted(values_by_group)
    values = np.array([values_by_group[k] for k in keys], dtype=float)
    rng = np.random.default_rng(SEED)

    boot = []
    for _ in range(draws):
        shuffled = dict(zip(keys, rng.permutation(values)))
        scores = np.array([shuffled[k] for k in g], dtype=float)
        boot.append(roc_auc_score(y, scores))

    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(np.mean(boot)), lo, hi


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
