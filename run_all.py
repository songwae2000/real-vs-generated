"""Reproduces every number in paper/paper.md.

Usage: python run_all.py

Downloads four 311 feeds on first run, then reruns from disk. Takes a few
minutes, most of it bootstrap resampling.
"""

import random

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from src import cities, manifest, stats, tickets
from src.austin_prior import PREDICTED_RANGE as AUSTIN_HUMAN_BAND
from src.austin_prior import prior_slow_probability as austin_human
from src.austin_prior_llm import PREDICTED_RANGE as AUSTIN_LLM_BAND
from src.austin_prior_llm import prior_slow_probability as austin_llm
from src.generators import GENERATORS
from src.nyc_prior import prior_slow_probability as nyc_prior
from src.sf_prior import PREDICTED_RANGE as SF_HUMAN_BAND
from src.sf_prior import prior_slow_probability as sf_human
from src.sf_prior_llm import prior_slow_probability as sf_llm

WASTE = "ARR"          # Austin's waste collection prefix
COLUMNS = ("category", "department")


def heading(text):
    print(f"\n\n{text}\n{'=' * len(text)}\n")


def prepared(city):
    train, test = tickets.load(city, "train"), tickets.load(city, "test")
    threshold = tickets.median_hours(train)
    train_f, train_y = tickets.split(train, threshold)
    test_f, test_y = tickets.split(test, threshold)
    return train_f, train_y, test_f, test_y, threshold


def ceiling_from_columns(train_f, train_y, test_f, test_y):
    """Best any rule over the category and department columns could do."""
    return roc_auc_score(test_y, stats.conditional_lookup(train_f, train_y,
                                                          test_f, COLUMNS))


def score_prior(prior, test_f):
    return [prior(f["category"], f["department"]) for f in test_f]


def main():
    print("data")
    for city in cities.ALL:
        tickets.ensure(city)

    drift = manifest.check()
    if drift:
        print("\n  WARNING: the feeds have moved since the paper was written.")
        for note in drift:
            print(f"    {note}")
        print("  Figures below will differ from the paper by that much.")
    else:
        print("  data matches the manifest the paper was computed from")

    loaded = {city.name: prepared(city) for city in cities.ALL}
    print(f"\n  {'city':<16}{'train':>8}{'test':>8}{'median':>9}{'categories':>12}")
    for city in cities.ALL:
        train_f, _, test_f, _, threshold = loaded[city.name]
        cats = len({f["category"] for f in test_f})
        print(f"  {city.name:<16}{len(train_f):>8}{len(test_f):>8}"
              f"{threshold:>8.1f}h{cats:>12}")

    heading("TABLE 1: blind priors, two authors, two cities")
    print(f"  {'city':<16}{'author':<14}{'AUC [95% CI]':>24}{'ceiling':>9}"
          f"{'recovered':>11}{'vs chance':>20}")

    blind = ((cities.AUSTIN, "human", austin_human),
             (cities.AUSTIN, "independent", austin_llm),
             (cities.SF, "human", sf_human),
             (cities.SF, "independent", sf_llm))
    observed = {}
    for city, author, prior in blind:
        train_f, train_y, test_f, test_y, _ = loaded[city.name]
        top = ceiling_from_columns(train_f, train_y, test_f, test_y)
        auc, lo, hi = stats.auc_interval(test_y, score_prior(prior, test_f))
        observed[(city.name, author)] = (auc, (auc - 0.5) / (top - 0.5))
        print(f"  {city.name:<16}{author:<14}{f'{auc:.3f} [{lo:.3f}, {hi:.3f}]':>24}"
              f"{top:>9.3f}{(auc - 0.5) / (top - 0.5):>10.0%}"
              f"{stats.versus_chance(lo, hi):>20}")

    print("\n  intervals are 1,000-resample bootstraps. The null baseline, always")
    print("  predicting the majority class, scores 0.500 by construction.")

    heading("TABLE 2: predictions recorded before evaluation")
    print(f"  {'arm':<34}{'predicted':>14}{'observed':>10}{'inside band':>14}")
    for label, band, auc in (
            ("Austin, human", AUSTIN_HUMAN_BAND, observed[("Austin", "human")][0]),
            ("Austin, independent", AUSTIN_LLM_BAND, observed[("Austin", "independent")][0]),
            ("San Francisco, human", SF_HUMAN_BAND, observed[("San Francisco", "human")][0])):
        inside = "yes" if band[0] <= auc <= band[1] else "NO"
        print(f"  {label:<34}{f'{band[0]:.2f} to {band[1]:.2f}':>14}"
              f"{auc:>10.3f}{inside:>14}")

    heading("TABLE 3: one category family explains the gap between the cities")
    train_f, train_y, test_f, test_y, _ = loaded["Austin"]
    waste = [f["category"].upper().startswith(WASTE) for f in test_f]
    rest_f = [f for f, w in zip(test_f, waste) if not w]
    rest_y = [y for y, w in zip(test_y, waste) if not w]

    print(f"  {'subset':<36}{'n':>7}{'prior':>8}{'ceiling':>9}{'recovered':>11}")
    for label, feats, ys in (("Austin, all tickets", test_f, test_y),
                             ("Austin, excluding waste collection", rest_f, rest_y)):
        top = ceiling_from_columns(train_f, train_y, feats, ys)
        auc = roc_auc_score(ys, score_prior(austin_llm, feats))
        print(f"  {label:<36}{len(feats):>7}{auc:>8.3f}{top:>9.3f}"
              f"{(auc - 0.5) / (top - 0.5):>11.0%}")

    sf_train_f, sf_train_y, sf_test_f, sf_test_y, _ = loaded["San Francisco"]
    sf_top = ceiling_from_columns(sf_train_f, sf_train_y, sf_test_f, sf_test_y)
    sf_auc, sf_share = observed[("San Francisco", "independent")]
    print(f"  {'San Francisco, all tickets':<36}{len(sf_test_f):>7}{sf_auc:>8.3f}"
          f"{sf_top:>9.3f}{sf_share:>11.0%}")

    waste_y = [y for y, w in zip(test_y, waste) if w]
    waste_p = [p for p, w in zip(score_prior(austin_llm, test_f), waste) if w]
    print(f"\n  waste collection is {sum(waste) / len(test_f):.0%} of Austin volume "
          f"and {np.mean(waste_y):.0%} of it runs slow.")
    print(f"  the prior calls it fast: mean predicted {np.mean(waste_p):.2f}")

    heading("TABLE 4: how concentrated each city is, and where the prior misreads it")
    print(f"  {'city':<16}{'categories':>12}{'top 5 share':>13}"
          f"{'volume in wrong-direction categories':>38}")
    for city, prior in ((cities.AUSTIN, austin_llm), (cities.SF, sf_llm)):
        _, _, feats, ys, _ = loaded[city.name]
        by = {}
        for f, y in zip(feats, ys):
            by.setdefault(f["category"], []).append(
                (y, prior(f["category"], f["department"])))
        ranked = sorted(by.values(), key=len, reverse=True)
        top5 = sum(len(v) for v in ranked[:5]) / len(feats)
        wrong = sum(len(v) for v in by.values()
                    if (np.mean([p for _, p in v]) > 0.5)
                    != (np.mean([y for y, _ in v]) > 0.5))
        print(f"  {city.name:<16}{len(by):>12}{top5:>12.0%}{wrong / len(feats):>37.0%}")

    heading("TABLE 5: the same procedure with the site's rates in hand")
    print(f"  {'prior':<18}{'tested on':<14}{'AUC [95% CI]':>24}{'ceiling':>9}"
          f"{'recovered':>11}")
    for tested in ("New York", "Chicago"):
        train_f, train_y, test_f, test_y, _ = loaded[tested]
        top = ceiling_from_columns(train_f, train_y, test_f, test_y)
        auc, lo, hi = stats.auc_interval(test_y, score_prior(nyc_prior, test_f))
        label = "New York" if tested == "New York" else "NY rules carried"
        print(f"  {label:<18}{tested:<14}{f'{auc:.3f} [{lo:.3f}, {hi:.3f}]':>24}"
              f"{top:>9.3f}{(auc - 0.5) / (top - 0.5):>10.0%}")

    heading("TABLE 6: fidelity ladder, trained on generated New York records")
    train_f, train_y, test_f, test_y, _ = loaded["New York"]
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
        for seed in range(5):
            rows, labels = generator.sample(len(train_f), random.Random(1000 + seed))
            model = LogisticRegression(max_iter=1000).fit(vec.transform(rows), labels)
            aucs.append(roc_auc_score(test_y, model.predict_proba(x_test)[:, 1]))
            invented.append(np.mean([(r["department"], r["category"]) not in allowed
                                     for r in rows]))
        mean = float(np.mean(aucs))
        print(f"  {generator.name:<24}{mean:>8.3f}{(mean - 0.5) / (top - 0.5):>11.0%}"
              f"{np.mean(invented):>13.1%}")


if __name__ == "__main__":
    main()
