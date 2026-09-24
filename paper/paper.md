# Domain priors do not substitute for real operational data

Every figure below is printed by `python run_all.py`.

## Question

Labs generate enterprise data from procedurally built companies: an org chart,
a taxonomy of work, and hand-written rules for how that work behaves. The
appeal is obvious. If domain reasoning can supply the behaviour, you do not
need the client's records to build a usable training set.

This paper tests whether domain reasoning can in fact supply it, for one
concrete property of operational work: how long a task takes.

## Hypothesis

**H.** Domain priors reasoned from the nature of the work capture a
substantial share of what real operational records provide for predicting task
duration.

The prediction was recorded before evaluation: a prior written without sight of
the target data should reach an AUC of 0.60 to 0.72, clearly above the 0.5 of
chance even if short of what real records achieve. Below 0.55 would mean domain
reasoning supplies essentially nothing. Above 0.80 would mean it supplies
nearly everything.

**Why it matters.** If H holds, a generator can be built for a client from
their taxonomy alone. If it fails, the behaviour in generated records has to
come from somewhere else, and the obvious somewhere else is the client's own
data.

## Method

**Data.** Public 311 service request feeds from New York, Chicago and Austin.
These are real operational records, written by the organisations that do the
work. Each carries an opening time, a service category, an owning department,
an intake channel and a closing time. We take two complete calendar weeks from
each city, the weeks of 4 May and 8 June 2026.

| city | train | test | median resolution |
| --- | --- | --- | --- |
| New York | 72,206 | 78,296 | 5.4h |
| Chicago | 17,291 | 38,671 | 118.0h |
| Austin | 5,968 | 6,029 | 23.8h |

Tickets still open at the pull date are kept and treated as slow, since all are
months past any threshold used here. Dropping them removes the slowest work.
Chicago closes most of its feed within a second of creation, so those
informational records are excluded and only worked tickets remain.

**Task.** At ticket opening, predict whether it will take longer than the
median to resolve. The model sees only what is known at that moment. Logistic
regression on one-hot categoricals throughout, so the learner is held constant
and differences between arms come from the training data. Recovered skill is
the share of the ceiling's advantage over chance that an arm reaches:
`(arm - 0.5) / (ceiling - 0.5)`.

**Two information conditions.** The independent variable is what the author of
the prior could see when writing it.

*Blind.* Rules for Austin, written from Austin's service type and department
vocabulary alone. The taxonomy was pulled with the query restricted to category
names and row counts, so no duration, rate or per-category outcome was
available. The rules were written, committed with the recorded prediction
above, and only then evaluated. This is the condition H is about.

*Informed.* Rules for New York, written with that city's conditional
resolution rates available. This is the condition a lab is in when it builds a
generator while inspecting a client's data, and it bounds what the same
procedure achieves with site statistics in hand.

*Carried across.* The New York rules, unmodified, applied to Chicago. This
separates rules that encode general domain structure from rules that encode one
site.

The pre-registration is checkable. The blind rules are commit `8973439` and
their evaluation is commit `4400226`.

## Results

### The blind prior reaches chance

| prior | evaluated on | had the site's rates | AUC [95% CI] | ceiling | recovered | vs chance |
| --- | --- | --- | --- | --- | --- | --- |
| Austin, **pre-registered** | Austin | **no** | **0.494** [0.481, 0.508] | 0.886 | **-1%** | **indistinguishable** |
| New York | Chicago | no | 0.496 [0.492, 0.499] | 0.729 | -2% | below |
| New York | New York | yes | 0.840 [0.837, 0.843] | 0.918 | 81% | above |

Intervals are 1,000-resample bootstraps of the test set. The null baseline,
always predicting the majority class, scores 0.500 by construction.

**H is refuted.** The blind prior scores 0.494, and its interval spans chance.
It is not weakly informative, it is statistically indistinguishable from
guessing. The recorded prediction of 0.60 to 0.72 was wrong, and wrong in the
direction that says domain reasoning supplied nothing at all.

This is not a coverage failure. The Austin rules fired on 98.9% of tickets,
producing scores spread from 0.05 to 0.95. Tickets they called slow ran slow
60.1% of the time and tickets they called fast ran slow 52.9% of the time, a
gap of seven points that does not survive as ranking skill.

The same procedure reaches 81% of the ceiling when the author has the site's
rates in hand. The distance between 81% and nothing is the measure of how much
of that performance comes from the site rather than from the domain.

The carried-across arm makes the same point from the other direction, and
slightly more sharply: its interval sits entirely below 0.5, so on Chicago the
New York rules are not merely uninformative but actively misleading. Their
department rules match 0.0% of Chicago rows, being New York acronyms, and
their keyword list is New York housing-stock vocabulary that in Chicago points
the wrong way. Rows it calls slow are slow 47.3% of the time against 58.6% for
everything else.

### The columns were not the problem

A prior that reasons over service category and department could in principle
reach whatever those two columns support. Fitting the conditional rate directly
from training records, using nothing but those same two columns, gives the
ceiling for any rule of that shape:

| city | best from category and department | the prior reached | gap |
| --- | --- | --- | --- |
| Austin (blind) | 0.883 | 0.494 | **0.389** |
| New York (informed) | 0.918 | 0.840 | 0.078 |

The columns carry nearly all of the available signal in both cities. What
separates the two rows is whether the author had the rates. The gap is the
price of not knowing them, and it is five times larger when the author is
working blind.

### Why domain reasoning fails here

The blind prior rests on four claims about the nature of municipal work. One
person attending once is fast. An inspection that opens a process is slow. Work
needing a crew and materials is slow. A fixed-cycle routine service is fast.
Each is plausible, and each is wrong somewhere.

| service type | predicted slow | actually slow |
| --- | --- | --- |
| ARR Compost | 5% | 96% |
| Vehicle Abatement Report | 5% | 94% |
| ARR Bulk | 5% | 92% |
| Animal Protection, Loose Dog | 5% | 81% |
| Traffic Signal Maintenance | 90% | 8% |
| Parking Violation Enforcement | 30% | 0% |
| Request Code Officer | 95% | 82% |

A traffic signal is physically crew work but administratively a same-day safety
priority. Compost collection is physically routine, but the ticket stays open
across the collection cycle. Vehicle abatement is a police matter subject to a
statutory waiting period.

In each case the duration is set by the organisation's workflow and its closing
conventions, not by the nature of the job. That is the answer to the question:
what real operational records supply here is institutional convention, and
convention is local and arbitrary enough that reasoning about the work does not
reach it.

### Distribution fidelity does not detect the problem

A generator ladder shows why a lab would not notice. Trained on generated New
York records and scored on real ones:

| generator | AUC | recovered | records that cannot occur |
| --- | --- | --- | --- |
| real records (ceiling) | 0.918 | 100% | 0.0% |
| marginal only | 0.466 | -8% | 70.5% |
| marginals + pairwise | 0.917 | **100%** | **0.0%** |
| empirical joint | 0.917 | 100% | 0.0% |

Matching marginals and pairwise dependence, the bar that SDV's Quality Score
and the NIST differential-privacy winners optimise, recovers everything on this
task and invents no impossible records. The New York task is close to a lookup
on one column: the service category alone scores 0.916 against the 0.918
ceiling, and the single rule `department is not NYPD` scores 0.850. An
evaluation built on this task will certify almost anything that gets one column
roughly right.

A second recorded prediction also failed. We expected generated records
violating real-world constraints to explain downstream loss. Marginal-only
generation does invent impossible department and category pairs, 70.5% of its
records, and it does lose everything. But the standard bar invents none and
loses nothing, so at the fidelity order that matters there was nothing to
measure.

## Limits

One author wrote both priors by one procedure. A practitioner with real
municipal operations experience might write rules that reach further, and
nothing here separates the procedure from the person. This is the largest
limit: the result bounds what this procedure achieves, not what domain
reasoning achieves in principle.

Three cities, one domain, one task family, one model class. Municipal service
records may be unusually institution-bound. A domain with genuinely
standardised process, such as a regulated industry or a franchise operation,
could behave differently, and that is the first thing we would test next.

Chicago's June week ran roughly twice the volume of its May week, so the
carried-across arm compares two operating conditions as well as two cities. Its
ceiling of 0.729 is also the lowest of the three, leaving less skill available
to recover.

We tried a harder framing, predicting speed within a service category to remove
the dominant column. Its ceiling is 0.514, too close to chance to separate
anything, so we report it as a limit and not a result.

New York carries known artefacts, including one department that closes 89.7% of
its tickets at exactly midnight, so its recorded durations are administrative.

That many high-order joints share low-order marginals, and that low-order
fidelity therefore fails to imply downstream utility, is established. We include
the ladder because it explains why a distribution-level check misses this.

## What it would take to answer the general question

Several independent authors writing priors under the blind condition would
separate the procedure from the person, which is the limit that most constrains
this result. Domains chosen to include genuinely standardised process would
establish whether institutional locality is a property of operational data in
general or of public services in particular.

The procedural point stands on its own. A prior can only be evaluated as a
prior once per dataset, before anyone has seen the outcomes, and the recorded
prediction has to come first. That is the only arrangement here that produced a
number worth trusting, and it cost an afternoon.
