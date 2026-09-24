# What a domain prior can and cannot replace

Every figure below is printed by `python run_all.py`. Reproducing the paper is
one command against four public feeds, with no key, no account and no cost. See
the closing section.

## Question

Labs generate enterprise data from procedurally built companies: an org chart,
a taxonomy of work, and hand-written rules for how that work behaves. If domain
reasoning can supply the behaviour, a generator can be built for a client
without their records.

This paper tests whether it can, for one concrete property of operational work:
how long a task takes.

## Hypothesis

**H.** Domain priors reasoned from the nature of the work capture a substantial
share of what real operational records provide for predicting task duration.

Recorded before evaluation: a prior written without sight of the target data
should reach an AUC of 0.60 to 0.72. Below 0.55 would mean domain reasoning
supplies essentially nothing.

**Why it matters.** If H holds, a taxonomy is enough to build a generator. If it
fails, the behaviour has to come from the client's own data.

## Method

**Data** (Table 1). Public 311 service request feeds from four cities. These are real
operational records, written by the organisations that do the work. Two
complete calendar weeks from each, the weeks of 4 May and 8 June 2026.

Caption: the four feeds, two complete weeks from each.
| city | train | test | median resolution | categories |
| --- | --- | --- | --- | --- |
| New York | 72,206 | 78,296 | 5.4h | 164 |
| Chicago | 17,291 | 38,671 | 118.0h | 92 |
| Austin | 5,968 | 6,029 | 23.8h | 117 |
| San Francisco | 17,723 | 17,007 | 15.1h | 37 |

Tickets still open at the pull date are kept and treated as slow, since all are
months past any threshold used. Chicago closes most of its feed within a second
of creation, so those informational records are excluded.

**Task.** At ticket opening, predict whether it will take longer than the median
to resolve. Logistic regression on one-hot categoricals, so the learner is held
constant. Recovered skill is the share of the achievable advantage over chance
that an arm reaches: `(arm - 0.5) / (ceiling - 0.5)`.

**The ceiling is the prior's own information.** A prior reasons over the service
category and the owning department. Fitting the conditional rate directly from
those same two columns gives the best any rule of that shape could do. Comparing
against it separates a weak rule from weak features.

**Blind authorship.** Rules were written from each city's service type and
department vocabulary alone. The taxonomy was pulled with the query restricted
to names and row counts, so no duration, rate or outcome was available. Rules
were written, committed with a recorded prediction, and only then evaluated.

**Two authors.** The largest threat to a result like this is that it describes
one person's reasoning. Each city was given two independent authors under the
same blind condition: the first was the experimenter, the second a language
model that saw only the taxonomy and was instructed not to look anything up.

## Results

### What a blind prior recovers

Caption: what a blind prior recovers, by city and by author.
| city | author | AUC [95% CI] | ceiling | recovered | vs chance |
| --- | --- | --- | --- | --- | --- |
| Austin | human | 0.494 [0.481, 0.508] | 0.883 | -1% | indistinguishable |
| Austin | independent | 0.611 [0.598, 0.626] | 0.883 | 29% | above |
| San Francisco | human | 0.676 [0.670, 0.684] | 0.886 | 46% | above |
| San Francisco | independent | 0.777 [0.770, 0.784] | 0.886 | **72%** | above |

Intervals are 1,000-resample bootstraps. The null baseline, always predicting
the majority class, scores 0.500 by construction.

**H cannot be answered yes or no** (Table 2). A blind prior recovers 72% of the achievable
skill in San Francisco and nothing at all in Austin. Testing one city would have
produced a confident conclusion in either direction, and the direction would
have been an artefact of the city.

Two effects sit inside that spread, and they differ in size. **Author** is
consistent and modest: the independent author beats the experimenter by 0.117 in
Austin and 0.101 in San Francisco, the same direction and roughly the same
magnitude twice. **City** is much larger: the same author moves from 29% to 72%.

### Three predictions, recorded before evaluation

| arm | predicted | observed | inside band |
| --- | --- | --- | --- |
| Austin, human | 0.60 to 0.72 | 0.494 | **no** |
| Austin, independent | 0.52 to 0.62 | 0.611 | yes |
| San Francisco, human | 0.55 to 0.68 | 0.676 | yes |

The first band was set before any result existed and was wrong. The later two
were set knowing the Austin outcome and were right, which is a weaker
achievement and is reported as such.

### One category family explains the gap between the cities

Caption: removing one category family closes the gap between the cities.
| subset | n | prior | ceiling | recovered |
| --- | --- | --- | --- | --- |
| Austin, all tickets | 6,029 | 0.611 | 0.883 | 29% |
| Austin, excluding waste collection | 4,008 | 0.766 | 0.881 | **70%** |
| San Francisco, all tickets | 17,007 | 0.777 | 0.886 | 72% |

Remove one family of work from Austin (Table 3) and its blind prior recovers 70%, which is
San Francisco's 72%. The cities were never different. One category family was.

Waste collection is 34% of Austin's volume and 70% of it runs slow. The prior
calls it fast, mean prediction 0.37, and the reason is worth stating plainly. A
missed-collection ticket stays open until the next scheduled route, which is a
week away. The work is trivially routine. The ticket is not. Nothing in the
phrase `ARR - Compost` reveals that.

San Francisco has no equivalent. Its two largest categories, street cleaning and
parking enforcement, are 57% of volume, and both behave the way the work
suggests.

| city | categories | top 5 share | volume misread |
| --- | --- | --- | --- |
| Austin | 117 | 40% | 35% |
| San Francisco | 37 | 78% | 17% |

### The finding

A blind domain prior recovers roughly 70% of the achievable skill on work whose
duration follows from the nature of the job, in both cities and for both
authors. It recovers nothing on work whose duration is set by an administrative
cycle the job description does not reveal. What determines its value is how much
of a client's volume sits in the second group, and that is not knowable from the
taxonomy.

### What having the rates is worth

Caption: the same procedure with the site's rates in hand.
| prior | tested on | AUC [95% CI] | ceiling | recovered |
| --- | --- | --- | --- | --- |
| New York | New York | 0.840 [0.837, 0.843] | 0.918 | 81% |
| New York, carried across | Chicago | 0.496 [0.492, 0.499] | 0.717 | -2% |

Rules written with a city's conditional rates in hand (Table 4) reach 81% there, above the
72% a blind author reached in San Francisco but not by much. The same rules
carried to another city fall entirely below chance. Their interval excludes 0.5
from beneath, so they are not merely uninformative but actively misleading. The
department rules match 0.0% of Chicago rows, being New York acronyms.

### Distribution fidelity does not detect any of this

| generator | AUC | recovered | impossible |
| --- | --- | --- | --- |
| real records (ceiling) | 0.918 | 100% | 0.0% |
| marginal only | 0.466 | -8% | 70.5% |
| marginals + pairwise | 0.917 | **100%** | **0.0%** |
| empirical joint | 0.917 | 100% | 0.0% |

Matching marginals and pairwise dependence, the bar SDV's Quality Score and the
NIST differential-privacy winners optimise, recovers everything on the New York
task and invents no impossible records. A second recorded prediction, that
impossible records would explain downstream loss, therefore failed at the
fidelity order that matters.

## Limits

Four cities, one domain, one task family, one model class. Municipal services may
be unusually institution-bound.

Two authors, and one of them is the experimenter. The independent author is a
language model, which is a real second author but not a domain practitioner. A
retired public works manager might do better than either.

The waste-collection result is a single family in a single city. It is an
explanation consistent with the numbers rather than a tested mechanism, and the
way to test it is to predict in advance, in a fifth city, which families will
break a prior and check.

The San Francisco human prior was written knowing what Austin had shown. Its
rules are blind to San Francisco's rates but its author is not blind to the
general lesson, so that arm tests transfer of a lesson rather than reasoning from
scratch.

Chicago's June week ran roughly twice the volume of its May week, so the carried
arm compares two operating conditions as well as two cities.

New York carries known artefacts, including one department that closes 89.7% of
its tickets at exactly midnight, so its recorded durations are administrative.

That low-order fidelity fails to imply downstream utility is established. The
ladder is included because it shows a distribution-level check cannot see the
effect this paper measures.

## Reproducing this

    python run_all.py

Four public 311 feeds, no key, no account, no cost, numpy and scikit-learn the
only dependencies. The first run downloads about 60MB and takes a few minutes.
It prints the six tables above, in order.

Two runs on the same data are byte-identical, since every random draw is
seeded. `scripts/check_paper.py` walks every table cell here and fails if a
number appears that the run did not print, which exists because two figures
once reached a draft without being computed. The feeds are live, so
`data/MANIFEST.json` records the row count and hash of each file these figures
came from and the run reports any disagreement before printing. A reviewer
whose numbers differ can tell whether the data moved or the code did.

The blind priors are one file per author per city in `src/`, each carrying its
reasoning and its recorded prediction.

## What it would take to answer the general question

Predict the failure families before looking. The waste-collection explanation
implies that any category whose clock is an administrative cycle rather than the
work itself will break a blind prior. That is checkable: name the categories in a
fifth city from the taxonomy, record the list, then measure.

More authors, including practitioners, would separate the procedure from the
person further than two can.

The procedural point stands regardless. A prior can only be evaluated as a prior
once per dataset, before anyone has seen the outcomes, and the recorded
prediction has to come first. Of the three predictions here, the only one made in
genuine ignorance was the one that turned out wrong.
