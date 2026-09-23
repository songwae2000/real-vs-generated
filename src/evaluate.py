"""Train on synthetic, test on real. Plus how many generated records are impossible."""

import random
import statistics

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from src.prepare import FEATURES

# a pair the real process never produces, e.g. a housing agency and a noise
# complaint. Measured over every real ticket we hold, train and test.
CONSTRAINT = ("agency", "complaint_type")


def real_combinations(*feature_sets):
    seen = set()
    for features in feature_sets:
        seen |= {tuple(row[c] for c in CONSTRAINT) for row in features}
    return seen


def impossible_rate(rows, allowed):
    if not rows:
        return 0.0
    bad = sum(1 for row in rows if tuple(row[c] for c in CONSTRAINT) not in allowed)
    return bad / len(rows)


def _fit_score(train_rows, train_labels, vectoriser, x_test, y_test):
    if len(set(train_labels)) < 2:
        return 0.5          # a constant arm has no skill, by construction
    model = LogisticRegression(max_iter=1000)
    model.fit(vectoriser.transform(train_rows), train_labels)
    return roc_auc_score(y_test, model.predict_proba(x_test)[:, 1])


def run(train_features, train_labels, test_features, test_labels,
        generators, seeds=10, scale=1.0):
    """Fits each generator on real training data, samples, trains, scores on real."""
    vectoriser = DictVectorizer(sparse=True)
    vectoriser.fit(train_features)
    x_test = vectoriser.transform(test_features)

    allowed = real_combinations(train_features, test_features)
    n = int(len(train_features) * scale)

    trtr = _fit_score(train_features, train_labels, vectoriser, x_test, test_labels)
    results = {"real data (TRTR)": {"auc": [trtr], "impossible": [
        impossible_rate(train_features, allowed)]}}

    for generator_class in generators:
        generator = generator_class().fit(train_features, train_labels)
        aucs, bad = [], []
        for seed in range(seeds):
            rng = random.Random(1000 + seed)
            rows, labels = generator.sample(n, rng)
            aucs.append(_fit_score(rows, labels, vectoriser, x_test, test_labels))
            bad.append(impossible_rate(rows, allowed))
        results[generator.name] = {"auc": aucs, "impossible": bad}

    return results, trtr


def report(results, trtr, title):
    print(f"\n{title}")
    print(f"  {'trained on':<24}{'AUC on real':>22}{'impossible records':>21}"
          f"{'skill kept':>12}")
    for name, data in results.items():
        aucs = data["auc"]
        mean = statistics.mean(aucs)
        spread = (f" +/- {1.96 * statistics.stdev(aucs) / len(aucs) ** 0.5:.3f}"
                  if len(aucs) > 1 else "")
        kept = (mean - 0.5) / (trtr - 0.5) if trtr > 0.5 else float("nan")
        print(f"  {name:<24}{mean:>9.3f}{spread:<13}"
              f"{statistics.mean(data['impossible']):>18.1%}{kept:>12.0%}")
