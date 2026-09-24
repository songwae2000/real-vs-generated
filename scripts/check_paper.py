"""Checks that every figure in the paper is one run_all.py actually prints.

Two numbers reached a draft of the paper without ever being computed. They
looked plausible and nobody would have caught them by reading. This walks every
table cell, pulls out each number, and fails if the run output does not contain
it.

Usage: python run_all.py > out.txt && python scripts/check_paper.py out.txt
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper" / "paper.md"
NUMBER = re.compile(r"-?\d[\d,]*\.?\d*%?")


def figures_in(markdown):
    """Every number appearing in a table row, with the row it came from."""
    found = []
    for line in markdown.splitlines():
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        for cell in line.strip("|").split("|"):
            for token in NUMBER.findall(cell):
                found.append((token, line.strip()))
    return found


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: check_paper.py <run_all output file>")

    run = Path(sys.argv[1]).read_text()
    haystack = run + "\n" + run.replace(",", "")

    missing = [(tok, row) for tok, row in figures_in(PAPER.read_text())
               if tok not in haystack and tok.replace(",", "") not in haystack]

    if missing:
        print(f"{len(missing)} figure(s) in the paper that run_all.py never printed:")
        for token, row in missing:
            print(f"  {token:>10}   {row[:70]}")
        sys.exit(1)

    print(f"all {len(figures_in(PAPER.read_text()))} table figures "
          f"are present in the run output")


if __name__ == "__main__":
    main()
