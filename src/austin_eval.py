"""Evaluates the pre-registered Austin prior. Run once, after commit 8973439."""

import json
from datetime import datetime

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from src.austin_prior import prior_slow_probability

PULLED = datetime(2026, 9, 23)


def load(path):
    rows = []
    for r in json.load(open(path)):
        try:
            created = datetime.fromisoformat(r["sr_created_date"])
        except (KeyError, TypeError, ValueError):
            continue
        closed = r.get("sr_closed_date")
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
            {"type": r.get("sr_type_desc") or "?",
             "dept": r.get("sr_department_desc") or "?",
             "channel": r.get("sr_method_received_desc") or "?"},
            hours, still_open))
    return rows


def main():
    train, test = load("data/austin_train.json"), load("data/austin_test.json")

    auto = sum(1 for _, h, _ in train if h <= 1 / 60) / len(train)
    print(f"austin: {len(train)} train / {len(test)} test tickets")
    print(f"closed within a minute: {auto:.1%}  "
          f"({'filtering to worked tickets' if auto > 0.2 else 'no auto-close problem'})")

    if auto > 0.2:
        train = [r for r in train if r[1] > 1 / 60]
        test = [r for r in test if r[1] > 1 / 60]

    threshold = float(np.median([h for _, h, _ in train]))
    print(f"slow = longer than {threshold:.1f}h, the training median\n")

    def split(rows):
        feats = [f for f, h, o in rows if not (o and h <= threshold)]
        ys = [h > threshold for f, h, o in rows if not (o and h <= threshold)]
        return feats, ys

    train_f, train_y = split(train)
    test_f, test_y = split(test)

    # the pre-registered prior, used directly as a scorer
    prior_scores = [prior_slow_probability(f["type"], f["dept"]) for f in test_f]
    prior_auc = roc_auc_score(test_y, prior_scores)

    # how often the rules actually fire rather than falling through to 0.5
    fired = np.mean([s != 0.5 for s in prior_scores])

    # ceiling: train on real Austin, test on the held-out real Austin week
    vec = DictVectorizer(sparse=True).fit(train_f)
    model = LogisticRegression(max_iter=1000).fit(vec.transform(train_f), train_y)
    trtr = roc_auc_score(test_y, model.predict_proba(vec.transform(test_f))[:, 1])

    kept = (prior_auc - 0.5) / (trtr - 0.5)
    print(f"  {'real Austin data (ceiling)':<38}{trtr:>8.3f}")
    print(f"  {'PRE-REGISTERED blind prior':<38}{prior_auc:>8.3f}   "
          f"{kept:>6.0%} of the ceiling")
    print(f"  {'rules fired on':<38}{fired:>8.1%} of tickets\n")

    print("  for comparison, from the earlier runs:")
    print(f"  {'NYC prior on NYC (author saw the rates)':<38}{0.822:>8.3f}")
    print(f"  {'NYC prior on Chicago (transferred)':<38}{0.435:>8.3f}")

    print(f"\n  predicted before evaluation: 0.60 to 0.72")
    verdict = ("WITHIN the predicted band" if 0.60 <= prior_auc <= 0.72 else
               "BELOW the band: NYC's 0.822 was mostly contamination" if prior_auc < 0.60 else
               "ABOVE the band: refutes the contamination reading")
    print(f"  observed {prior_auc:.3f} -> {verdict}")


if __name__ == "__main__":
    main()
