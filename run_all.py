"""Reproduces every number in paper/paper.md.

Usage: python run_all.py

Downloads three 311 feeds on first run, then reruns from disk.
"""

import random

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from src import cities, stats, tickets
from src.generators import GENERATORS
from src.austin_prior import prior_slow_probability as austin_prior
from src.nyc_prior import prior_slow_probability as nyc_prior


def ceiling(train_f, train_y, test_f, test_y):
    """Train on real, test on real. The best the features support."""
    vec = DictVectorizer(sparse=True).fit(train_f)
    model = LogisticRegression(max_iter=1000).fit(vec.transform(train_f), train_y)
    return roc_auc_score(test_y, model.predict_proba(vec.transform(test_f))[:, 1])


def prior_auc(prior, test_f, test_y):
    scores = [prior(f["category"], f["department"]) for f in test_f]
    fired = float(np.mean([abs(s - 0.5) > 1e-9 for s in scores]))
    return roc_auc_score(test_y, scores), fired


def recovered(arm, top):
    return (arm - 0.5) / (top - 0.5)


def ladder(train_f, train_y, test_f, test_y, seeds=5):
    """Generators at three fidelity orders, and how many records they invent."""
    vec = DictVectorizer(sparse=True).fit(train_f)
    x_test = vec.transform(test_f)
    top = roc_auc_score(test_y, LogisticRegression(max_iter=1000)
                        .fit(vec.transform(train_f), train_y)
                        .predict_proba(x_test)[:, 1])
    allowed = ({(f["department"], f["category"]) for f in train_f}
               | {(f["department"], f["category"]) for f in test_f})

    print(f"  {'generator':<24}{'AUC':>8}{'recovered':>12}{'impossible':>13}")
    print(f"  {'real records (ceiling)':<24}{top:>8.3f}{'100%':>12}{'0.0%':>13}")
    for generator_class in GENERATORS:
        generator = generator_class().fit(train_f, train_y)
        aucs, invented = [], []
        for seed in range(seeds):
            rows, labels = generator.sample(len(train_f), random.Random(1000 + seed))
            model = LogisticRegression(max_iter=1000).fit(vec.transform(rows), labels)
            aucs.append(roc_auc_score(test_y, model.predict_proba(x_test)[:, 1]))
            invented.append(np.mean([(r["department"], r["category"]) not in allowed
                                     for r in rows]))
        mean = float(np.mean(aucs))
        print(f"  {generator.name:<24}{mean:>8.3f}{recovered(mean, top):>11.0%}"
              f"{np.mean(invented):>13.1%}")


def main():
    print("data")
    for city in cities.ALL:
        tickets.ensure(city)

    loaded = {}
    for city in cities.ALL:
        train, test = tickets.load(city, "train"), tickets.load(city, "test")
        threshold = tickets.median_hours(train)
        train_f, train_y = tickets.split(train, threshold)
        test_f, test_y = tickets.split(test, threshold)
        loaded[city.name] = (train_f, train_y, test_f, test_y, threshold)
        print(f"  {city.name:<10} {len(train_f):>6} train  {len(test_f):>6} test"
              f"   median {threshold:>6.1f}h")

    print("\n\nTABLE 1: what each prior recovers, with 95% bootstrap intervals")
    print(f"  {'prior':<12}{'tested on':<11}{'saw rates':<12}{'AUC [95% CI]':>22}"
          f"{'ceiling':>9}{'recovered':>11}{'vs chance':>19}")

    rows = [("Austin", "Austin", "no, pre-reg", austin_prior),
            ("New York", "Chicago", "no", nyc_prior),
            ("New York", "New York", "yes", nyc_prior)]

    for authored, tested, saw, prior in rows:
        train_f, train_y, test_f, test_y, _ = loaded[tested]
        scores = [prior(f["category"], f["department"]) for f in test_f]
        auc, lo, hi = stats.auc_interval(test_y, scores)
        top = ceiling(train_f, train_y, test_f, test_y)
        interval = f"{auc:.3f} [{lo:.3f}, {hi:.3f}]"
        print(f"  {authored:<12}{tested:<11}{saw:<12}{interval:>22}{top:>9.3f}"
              f"{recovered(auc, top):>10.0%}{stats.versus_chance(lo, hi):>19}")

    print("\n  null baseline: always predict the majority class, AUC 0.500 by "
          "construction")

    print("\n\nTABLE 2: the blind prior is not failing for lack of coverage")
    train_f, train_y, test_f, test_y, _ = loaded["Austin"]
    auc, fired = prior_auc(austin_prior, test_f, test_y)
    scores = [austin_prior(f["category"], f["department"]) for f in test_f]
    said_slow = [y for y, s in zip(test_y, scores) if s > 0.5]
    said_fast = [y for y, s in zip(test_y, scores) if s < 0.5]
    print(f"  rules fired on {fired:.1%} of Austin tickets")
    print(f"  tickets it called slow ran slow {np.mean(said_slow):.1%} of the time")
    print(f"  tickets it called fast ran slow {np.mean(said_fast):.1%} of the time")

    print("\n\nTABLE 3: the information ceiling for the prior's own columns")
    print("  best achievable from category and department alone, against what")
    print("  a prior reasoning over those same columns actually reaches\n")
    print(f"  {'city':<10}{'fitted lookup':>16}{'prior':>9}{'gap':>8}")
    for city_name, prior in (("Austin", austin_prior), ("New York", nyc_prior)):
        train_f, train_y, test_f, test_y, _ = loaded[city_name]
        lookup = stats.conditional_lookup(train_f, train_y, test_f,
                                          ("category", "department"))
        best = roc_auc_score(test_y, lookup)
        got = roc_auc_score(test_y, [prior(f["category"], f["department"])
                                     for f in test_f])
        print(f"  {city_name:<10}{best:>16.3f}{got:>9.3f}{best - got:>8.3f}")
    print("\n  the columns carry the signal. The gap is what not knowing the")
    print("  rates costs, not what the features lack.")

    print("\n\nTABLE 4: fidelity ladder, trained on generated New York records")
    train_f, train_y, test_f, test_y, _ = loaded["New York"]
    ladder(train_f, train_y, test_f, test_y)

    print("\n\nTABLE 5: why the New York rules do not carry to Chicago")
    train_f, train_y, test_f, test_y, _ = loaded["Chicago"]
    from src.nyc_prior import FAST_DEPT, SLOW_DEPT, SLOW_WORK
    hit = [y for f, y in zip(test_f, test_y)
           if any(k.lower() in f["category"].lower() for k in SLOW_WORK)]
    miss = [y for f, y in zip(test_f, test_y)
            if not any(k.lower() in f["category"].lower() for k in SLOW_WORK)]
    dept = np.mean([f["department"] in SLOW_DEPT or f["department"] in FAST_DEPT
                    for f in test_f])
    print(f"  department rules fire on {dept:.1%} of Chicago rows")
    print(f"  rows the keywords call slow are slow {np.mean(hit):.1%} of the time")
    print(f"  everything else is slow {np.mean(miss):.1%} of the time")


if __name__ == "__main__":
    main()
