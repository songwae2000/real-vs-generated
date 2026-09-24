# What a domain prior can and cannot replace

Can hand-written domain rules replace a client's operational records when
generating enterprise data? This tests it on 311 service tickets from four
cities, and the answer turns out to depend on the client.

Written for the TGDC case study, research track. The paper is `paper/paper.md`.

## Run it

    python run_all.py

Four public 311 feeds, no key, no account, no cost. numpy and scikit-learn are
the only dependencies. The first run downloads about 60MB and takes a few
minutes, most of it bootstrap resampling. Later runs read from disk.

It prints the six tables the paper quotes, in order.

## The result

A prior written blind, from a city's service catalogue alone, recovers 72% of
the achievable skill in San Francisco and nothing at all in Austin. One
category family accounts for the whole gap: Austin's waste collection is a
third of its volume and runs slow, because a missed-collection ticket stays
open until the next scheduled route. The work is routine. The ticket is not.

So a blind prior works on work whose duration follows from the job, and fails
on work whose clock is an administrative cycle. Which of those a client has is
not visible in their taxonomy.

## How blindness was enforced

Each city's taxonomy was pulled with the query restricted to category names and
row counts, so no duration, rate or outcome was available to the author. Rules
were written, committed with a recorded prediction, and only then evaluated.

Each city has two independent authors under that condition, because the first
draft of this work had one and the result turned out to be partly about him.

## Layout

- `run_all.py` prints every figure in the paper.
- `src/*_prior.py` and `src/*_prior_llm.py` are the blind priors, one file per
  author per city. Each carries its reasoning and its recorded prediction.
- `src/nyc_prior.py` is the contrast case, written with the site's rates in hand.
- `src/tickets.py` loads any of the four feeds into one shape.
- `src/generators.py` is the fidelity ladder: marginal, pairwise, joint.
- `src/stats.py` is bootstrap intervals and the information ceiling.
- `scripts/check_paper.py` and `scripts/make_paper.py`.
- `HYPOTHESIS.md` is the hypothesis as fixed before the first experiment ran,
  including the three ways it could fail. One of them happened.

## Checks

`scripts/check_paper.py` walks every table cell in the paper and fails if a
number appears there that the run did not print. It exists because two figures
once reached a draft without being computed.

`data/MANIFEST.json` records the row count and hash of each file the paper was
computed from. The feeds are live, so `run_all.py` reports any disagreement
before printing a figure, and a reviewer whose numbers differ can tell whether
the data moved or the code did.

`scripts/make_paper.py` generates the LaTeX from `paper/paper.md`, so the
typeset version cannot drift from the text.
