# A domain prior remembers the site it was written against

## Question

A lab that generates enterprise data has to decide whether its generator is
any good. The usual check is to train a model on the generated records and
score it on held-out real records from the organisation the generator was
built for. If the model performs, the generator is judged faithful enough for
the task.

When a generator encodes hand-written domain rules, can in-distribution
evaluation distinguish genuine domain knowledge from a memory of the data
those rules were written against?

## Hypothesis

**H.** The conditional structure of real operational data is site-specific
rather than domain-general. A generator built from domain priors authored
against one organisation encodes that organisation. It will transfer within
that site and fail across sites, and evaluation on held-out records from the
same site cannot tell the two cases apart.

This matters because a triage agent trained on generated data and validated
against the client it was modelled on will be certified as working, then fail
at the next client.

The hypothesis was available to fail in two ways. Rules written against one
city might transfer to another, since municipal service work is broadly
similar. Or a prior written with no sight of the data might work in place, in
which case the apparent skill of the first prior was knowledge rather than
memory.

## Method

**Data.** Public 311 service request feeds from three cities: New York,
Chicago and Austin. These are real operational records, written by the
organisations that do the work, with a creation timestamp, a service
category, a responsible department, an intake channel and a closing
timestamp. For New York we take two complete calendar weeks, the weeks of 4
May 2026 (72,230 tickets) and 8 June 2026 (78,308). Chicago and Austin use the
same two weeks: 18,926 and 20,645 worked tickets for Chicago, 5,968 and 6,029
for Austin.

Tickets still open at the pull date are kept and treated as slow, since all
are months past any threshold used here. Dropping them removes the slowest
work and biases the test set.

**Task.** At ticket creation, predict whether the ticket will take longer than
the median to resolve. The model sees only what is known when the ticket is
opened. We train on synthetic records and test on real ones (TSTR), with
train-on-real (TRTR) as the ceiling. The model is logistic regression on
one-hot categorical features throughout, so the learner is held constant and
differences between arms come from the training data.

Recovered skill is the share of the ceiling's advantage over chance that an
arm reaches: `(arm - 0.5) / (ceiling - 0.5)`.

**The three prior conditions.** The same procedure, under three information
conditions:

1. *Contaminated, in-distribution.* Rules for New York, which we wrote after
   reading New York's conditional resolution rates, then evaluated on
   held-out New York tickets. This is the condition a lab is in when it builds
   a generator by inspecting a client's data.
2. *Transferred.* The same New York rules, unmodified, evaluated on Chicago.
3. *Blind, pre-registered.* Rules for Austin, written from Austin's service
   type and department vocabulary alone. The taxonomy was pulled with the
   query restricted to category names and row counts. No duration, rate or
   per-category outcome was requested or displayed. The rules were then
   written, committed to version control with a recorded prediction, and only
   then evaluated.

The pre-registration is checkable. The rules are commit `8973439` and the
evaluation is commit `4400226`.

**Fidelity ladder.** We also compare generators at three fidelity orders:
marginals only, marginals plus pairwise dependence (a Chow-Liu tree, the order
that PrivBayes, MST and SDV's Column Pair Trends optimise), and the empirical
joint.

## Results

### The prior only works where it was written

| rules authored for | evaluated on | had we seen this city's rates | AUC |
| --- | --- | --- | --- |
| New York | New York | yes | **0.822** |
| New York | Chicago | no, rules transferred unchanged | 0.435 |
| Austin | Austin | **no, pre-registered** | **0.494** |

Against a real-data ceiling of 0.890 in New York, the contaminated prior's
0.822 recovers 82.6% of the achievable skill. Against Austin's ceiling of
0.886, the blind prior's 0.494 recovers nothing: the raw figure sits just
below chance, so the ratio is slightly negative.

This is not a coverage failure. The Austin rules fired on 98.9% of tickets,
producing scores spread from 0.05 to 0.95. Tickets it called slow ran slow 64.3% of the
time. Tickets it called fast ran slow 66.1% of the time, marginally more. The
two groups are indistinguishable.

The transferred case fails differently. The New York rules score below chance
on Chicago because they are actively inverted there: the department rules fire
on 0.0% of Chicago rows because they are New York acronyms, and the keyword list is New
York housing-stock vocabulary whose Chicago matches run the other way. Rows
the rules call slow are slow 29.7% of the time, against 52.0% for the rest.

### Why the prior fails, in detail

The Austin prior was built from four claims about the nature of municipal
work: one person attending once is fast, an inspection that opens a process is
slow, work needing a crew and materials is slow, and a fixed-cycle routine
service is fast. Each is plausible, and each is wrong somewhere.

| service type | predicted slow | actually slow |
| --- | --- | --- |
| ARR Compost | 5% | 96% |
| Vehicle Abatement Report | 5% | 94% |
| ARR Bulk | 5% | 92% |
| Animal Protection, Loose Dog | 5% | 81% |
| Traffic Signal Maintenance | 90% | 8% |
| Parking Violation Enforcement | 30% | 0% |
| Request Code Officer | 95% | 82% |

A traffic signal is physically crew work but administratively a same-day
safety priority. Compost collection is physically routine, but the ticket
stays open across the collection cycle. Vehicle abatement is a police matter
subject to a statutory waiting period. In each case the duration is set by the
organisation's workflow and its closing conventions, not by the nature of the
job. That is not something reasoning about the work can recover.

### Why the in-distribution check is easy to pass

The fidelity ladder explains it. The headline task is close to a lookup on one
column. A generator matching marginals and pairwise dependence recovers 100%
of the achievable skill. The single rule `department is not NYPD` scores
0.833, against the hand-written prior's 0.822. When the dominant column is
removed by predicting speed within a service category, the same pairwise
generator keeps 44% where the empirical joint keeps 97%.

So the same generator, judged by the same fidelity metric, looks either
lossless or half-useless depending on which task it is scored against. An
evaluation that happens to pick the easy framing will certify almost anything.

### A prediction that was wrong

Before evaluating Austin we recorded a predicted range of 0.60 to 0.72, on the
reasoning that genuine domain knowledge ought to be worth something even if
less than a contaminated prior. The observed 0.494 is below that band. The
prediction was wrong, and the hypothesis holds in a stronger form than
expected: the contaminated prior's advantage was not mostly memory, it was
entirely memory.

A separate pre-registered hypothesis also failed. We expected generated
records that violate real-world constraints to explain the loss in downstream
skill. They do not. The pairwise and joint generators both emit 0% impossible
department and category pairs while differing by 53 points of recovered skill.
The loss lives in higher-order dependency structure that a validity check
cannot see.

## Limits

Three cities, one domain, one task family, one model class. Municipal service
records may be unusually institution-bound, and a domain with genuinely
standardised process, such as a regulated industry or a franchise operation,
could behave differently. That would bound how far the locality claim reaches,
and it is the first thing we would test next.

We wrote all three priors by one procedure. A different author, or a
practitioner with real municipal operations experience, might produce rules
that transfer. Nothing here separates the procedure from the person.

Chicago's feed auto-closes 62% of tickets within a second of creation, so the
Chicago comparison uses worked tickets only. That filter was decided before
any arm was scored. New York carries its own artefacts, including one
department that closes 89.7% of its tickets at exactly midnight, so its recorded
durations are administrative.

The fidelity-order results confirm published work.
That many high-order joints share low-order marginals, and that low-order
fidelity therefore fails to imply downstream utility, is established. We include it because it explains why the
contamination goes unnoticed.

Finally, the contamination is irreversible. Having inspected New York and
Chicago, we can no longer write a blind prior for either. A prior-driven
generator can be evaluated honestly once per dataset, and only before anyone
has looked.

## What it would take to answer the general question

Pre-registration would have to become the default rather than an experiment.
Rules authored against a taxonomy with outcomes withheld, committed, then
scored once, is the only procedure here that produced a number worth
trusting. It cost an afternoon.
