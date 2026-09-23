# A domain prior remembers the site it was written against

Four-page structure. Every number below is measured and reproducible.

## Question

Labs generate enterprise data from procedurally built companies and
hand-written domain rules. The usual way to check such a generator is to train
an agent on its output and score that agent on held-out real records from the
same organisation. This paper asks whether that check can tell domain
knowledge apart from a memory of the data the rules were written against.

## Hypothesis

**H.** The conditional structure of real operational data is site-specific
rather than domain-general. A generator built from domain priors authored
against one site encodes that site, so it transfers within the site and fails
across sites. Evaluation on held-out records from the same site cannot
separate the two cases.

**Why it matters for agents.** A triage agent trained on generated data,
validated against the client it was built from, will be certified as working
and then fail at the next client.

**How it could fail.** If the priors transfer to a second city, domain
knowledge substitutes for real operational data and the locality claim dies.
That outcome was available: municipal service work is similar enough between
cities that transferable rules are plausible.

## Method

Real operational data: NYC 311 service tickets, complete weeks of 4 May
(72,230) and 8 June (78,308). Second site: Chicago 311. Tickets still open are
kept and treated as slow, since all are months past any threshold used.

Task: at ticket creation, predict whether resolution exceeds the median.
Trained on synthetic, tested on real (TSTR), with train-on-real as the
ceiling (TRTR). Logistic regression on one-hot categoricals, 10 seeds.

Arms: real records; marginal-only generator; marginals plus pairwise
(Chow-Liu tree, the order PrivBayes, MST and SDV's Column Pair Trends
optimise); empirical joint; hand-authored domain priors.

The prior rules were written by the author *after* reading NYC's conditional
rates. That contamination is the object of study, not an oversight.

## Results

**1. In-distribution the prior looks like expertise.** AUC 0.822 against real
training data's 0.890, recovering 82.5% of the achievable skill.

**2. Out of site it inverts.** The same rules, unmodified, score AUC 0.435 on
Chicago, below chance. The agency rules fire on 0.0% of Chicago rows, being
NYC acronyms. The keyword list is NYC housing-stock vocabulary whose Chicago
matches run the other way: rows it calls slow are slow 29.7% of the time
against 52.0% for the rest.

**3. Why the in-distribution check is so easy to pass.** The headline task's
signal is close to one column. A pairwise generator keeps 100% of the skill,
and `agency != NYPD` alone scores 0.833, beating the whole 30-keyword prior.
Remove the dominant column by predicting within complaint type and the same
pairwise generator keeps 44% where the empirical joint keeps 97%.

**4. Invalid records are not the mechanism.** Pairwise and joint generators
both emit 0% impossible agency and complaint-type pairs, yet differ by 53
points of recovered skill. The degradation lives in higher-order dependency
structure that a validity check cannot see. A pre-registered hypothesis that
invalid records drive the loss was wrong.

## Limits

Two cities, one domain, one task family, one model class. One author wrote the
priors by one procedure, and a different author might produce more
transferable rules. Chicago's feed auto-closes 62% of tickets within a second,
so the comparison uses worked tickets only, a cut decided before any arm was
scored. NYC 311 carries known artefacts: one agency closes 89.7% of its
tickets at midnight, making its resolution times administrative.

Result 3 confirms published work rather than discovering it (Ganev et al.
2024 on low-order fidelity and downstream utility; utility-theory work on task
dependence). It is context for why result 2 goes unnoticed, not a contribution.

Contamination is irreversible per dataset. Having inspected both cities, the
author can no longer produce a blind prior for either.

## What it would take to answer the general question

Priors pre-registered against a taxonomy with rates withheld, evaluated on a
third site never inspected. Several independent authors, to separate the
procedure from the person. Domains beyond municipal services, particularly
ones where the underlying process genuinely is standardised across sites,
which would bound how far the locality claim reaches.
