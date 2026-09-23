"""Reproduces the experiment end to end.

Usage: python run_all.py
"""

import numpy as np

from src.evaluate import report, run
from src.generators import GENERATORS
from src.prepare import label, load

TRAIN = "data/train_week.json"
TEST = "data/test_week.json"


def main():
    train_rows = load(TRAIN)
    test_rows = load(TEST)

    threshold = float(np.median([h for _, h, _ in train_rows]))
    train_features, train_labels = label(train_rows, threshold)
    test_features, test_labels = label(test_rows, threshold)

    print(f"train {len(train_features)} tickets (week of 4 May)")
    print(f"test  {len(test_features)} tickets (week of 8 June)")
    print(f"slow = took longer than {threshold:.2f}h, the training median")
    print(f"base rate: train {np.mean(train_labels):.1%}, test {np.mean(test_labels):.1%}")

    results, trtr = run(train_features, train_labels, test_features, test_labels,
                        GENERATORS)
    report(results, trtr,
           "trained on each generator's output, scored on real June tickets")


if __name__ == "__main__":
    main()
