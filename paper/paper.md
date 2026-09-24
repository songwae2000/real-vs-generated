# What a domain prior can and cannot replace

Can hand-written rules stand in for a client's operational records when
generating enterprise data? On 311 tickets from four cities, blind rules clear a
structural null in San Francisco (p 0.0015) and not in Austin (p 0.110), and a
conditional fitted on the real data beats them in both. Two cheaper things do
most of the work: category volume alone scores 0.672 against my own rules' 0.676,
and a city's published service target scores 79% of the achievable margin with no
reasoning and no records at all. What survives is a warning rather than a
substitute. If a taxonomy plus a published target carries most of the signal, an
agent benchmark built on generated tickets is testing something much weaker than
it looks.

Companies selling generated enterprise data build it from a description of a
business rather than anyone's real records: an org chart, a list of the work, and
hand-written rules for how that work behaves. A client who cannot share their
data can still be served, which is the appeal. What it costs is the open
question. Distributional fidelity is easy to measure and already known to be a
poor guide to downstream usefulness, so the practical question is which
properties of real records the rules can supply and which a client has to hand
over.

This study uses public 311 service request feeds from four cities. Each ticket is
a unit of work and the question asked of it is how long it takes to close. A
service catalogue lists job types and the departments that own them with no
timings, so it stands in for the description of a business, and the recorded
durations stand in for the client records a generator does without.

## Hypothesis

My hypothesis is that rules reasoned from the nature of the work, written
without sight of any outcome, predict how long a job takes at an AUC between
0.60 and 0.72, and that anything below 0.55 would mean the reasoning adds
nothing.

## Related work

That fidelity and utility can come apart is established [1, 2, 3, 4], and whether
the standard metrics measure the right thing is itself argued over [5]. I take
that as given rather than as something to show, and the fidelity ladder below is
here only because it makes the point on the same data as everything else.

The nearer literature is language models as priors over tabular problems, and
this is a small instance of it. Knauer et al. induce a decision tree from the
target and the column names alone, with no rows and no labels [6], which is the
move my model-written rules make, and TabLLM shows column names carry zero-shot
signal before any label [7]. AutoElicit scores an elicited prior against real
data by marginal likelihood and chooses between priors by Bayes factor [8], which
does not depend on a test split and is what I would adopt next time.

All four are classification where my target is duration, and the first three need
feature names to be descriptive, which Knauer et al. state as a precondition. A
311 taxonomy is unusually kind on that point. An enterprise schema of coded
columns would not be.

## Method

The records are written by the people who do the work. Each feed gives the work
type, the owning department, how the request came in, and when it opened and
closed. I take the full weeks of 4 May and 8 June 2026 (Table 1).

Caption: the four feeds, two complete weeks from each.
| city | train | test | median resolution | categories |
| --- | --- | --- | --- | --- |
| New York | 72,206 | 78,296 | 5.4h | 164 |
| Chicago | 17,291 | 38,671 | 118.0h | 92 |
| Austin | 5,968 | 6,029 | 23.8h | 117 |
| San Francisco | 17,723 | 17,007 | 15.1h | 37 |

Tickets still open when I pulled the data are kept and counted as slow, since all
are months past any threshold. Chicago closes most of its feed within a second of
creation, and I drop those rows as records rather than work.

The task is to predict, at the moment a ticket opens, whether it will take longer
than the median to close. Recovered skill, reported alongside AUC, is
`(AUC - 0.5) / (ceiling - 0.5)`. The null I test against is that the rules carry
no information about which work runs slow, so any score they reach is available
from carving up the same taxonomy at random.

The ceiling: a prior reads two columns, the service category and the owning
department, so I fit the conditional rate from those same two to see what they
support. It is a taxonomy ceiling, not a general limit on skill, and it separates
a weak rule from weak features. I settled on it after the first Austin arm had
been scored against a different estimator, so the AUCs here are pre-registered
and the denominator is not. Every percentage sits beside its raw AUC.

I report two kinds of interval. Resampling tickets treats 17,007 San Francisco
rows as independent when the rules were written per category, so I also resample
categories [9]. That second unit carries two warnings. A score is constant within
a category only where the category has one owning department, which holds
throughout Austin but fails for 22 of San Francisco's 37 categories, 99.6% of its
rows. And clustered resampling is asymptotic in the number of clusters and
assumes rough balance, where one San Francisco category holds 34% of the rows and
the effective count is 5.3 against 37 categories, Austin 22.3 against 117. Almost
nothing could clear an interval that wide, so I read the category intervals as
descriptive rather than as tests, and where I say something is not established I
mean this design cannot establish it [10].

I pulled each catalogue with the query limited to category names and row counts,
so no duration, rate or outcome reached me. I wrote the rules from that alone,
committed them with a prediction, then evaluated. I amended one San Francisco
file 27 seconds after committing it, to match on word boundaries rather than
substrings, before that city's data existed on disk.

The biggest risk is that the result describes one person's reasoning, so Austin
and San Francisco each have two sets of rules under the same blind condition. I
wrote one, a language model wrote the other from the same catalogue. New York is
the contrast, written while I could see the real rates, and Chicago is where I
carried those rules.

## Results

### What a blind prior recovers

Caption: what blind rules recover, by city and by author. Ticket intervals are 1,000 resamples, category intervals 2,000.
| city | rules | AUC | by ticket | by category | ceiling | recovered |
| --- | --- | --- | --- | --- | --- | --- |
| Austin | mine | 0.494 | [0.481, 0.508] | [0.331, 0.649] | 0.883 | -1% |
| Austin | the model | 0.611 | [0.598, 0.626] | [0.442, 0.770] | 0.883 | 29% |
| San Francisco | mine | 0.676 | [0.670, 0.684] | [0.515, 0.815] | 0.886 | 46% |
| San Francisco | the model | 0.777 | [0.770, 0.784] | [0.529, 0.859] | 0.886 | 72% |

The answer is not yes or no (Table 2). The best blind rules recover 72% of the
taxonomy ceiling in San Francisco, the weakest nothing in Austin. Had I tested
one city I would have drawn a confident conclusion either way, and the city would
have decided which.

The two intervals disagree. By ticket three of the four arms beat chance, but by
category only the two San Francisco arms do, and Austin's model-written set spans
[0.442, 0.770], which I cannot tell from guessing. The 72% spans roughly 7% to
93% on that unit, so read every claim below at that width.

### What the rules add over structure alone

A rule set can score well because it is reasoning, or because almost any sensible
cut of a lopsided taxonomy would. Two controls tell those apart.

Caption: blind rules against two baselines built from structure alone, with category intervals and the permutation test of the null.
| city | arm | AUC | [95% CI] | recovered | p vs H0 |
| --- | --- | --- | --- | --- | --- |
| Austin | blind rules, per ticket | 0.611 | | 29% | |
| Austin | blind rules, per category | 0.617 | | | 0.110 |
| Austin | category frequency alone | 0.516 | [0.351, 0.726] | 4% | |
| Austin | same rules, verdicts shuffled | 0.501 | [0.322, 0.674] | 0% | |
| SF | blind rules, per ticket | 0.777 | | 72% | |
| SF | blind rules, per category | 0.741 | | | 0.0015 |
| SF | category frequency alone | 0.672 | [0.441, 0.785] | 45% | |
| SF | same rules, verdicts shuffled | 0.499 | [0.312, 0.690] | 0% | |

Shuffling the verdicts across categories keeps the taxonomy, the row counts and
the set of scores, and breaks only which category got which score, so it draws
from the null directly and the share of shuffles reaching the observed AUC is a
permutation p-value (Table 3). The null assigns one verdict per category, so the
arm is scored that way too, which is why the table carries a second AUC for it.
The rules reach 0.741 in San Francisco with 2 of 2,000 shuffles matching, p of
0.0015, and 0.617 in Austin with 220 matching, p of 0.110. I reject the null in
San Francisco and cannot in Austin, so the reasoning does real work in one city
and is not distinguishable from a lucky cut of the taxonomy in the other.

Frequency is the harder baseline, because the pull gave me row counts and those
are themselves real operational data. Scored rarer-is-slower it reaches 0.672
against 0.676 for my own San Francisco rules, so mine add almost nothing beyond
volume. The model's clear it by 0.105. Picking that direction is one bit the
catalogue did not give me, so the baseline is generous if anything.

### The author effect is not established

The model beats me by 0.116 in Austin and 0.101 in San Francisco, the same
direction and a similar size twice, which looks like something. By ticket both
miss zero, at [0.104, 0.131] and [0.095, 0.107], but by category neither does, at
[-0.036, 0.288] and [-0.021, 0.174]. Two cities are not enough, and an earlier
draft of mine reported these differences with no interval at all.

### What I predicted, before I looked

| arm | predicted | observed | in band |
| --- | --- | --- | --- |
| Austin, mine | 0.60 to 0.72 | 0.494 | no |
| Austin, the model | 0.52 to 0.62 | 0.611 | yes |
| SF, mine | 0.55 to 0.68 | 0.676 | yes |
| SF, the model | none | 0.777 | - |

I set the first band before the project had any result, and it was wrong. I set
the next two after seeing Austin, so I knew roughly what to expect, which is a
weaker achievement and I count it as one. The fourth arm produces my headline 72%
and carries no prediction at all. The only prediction made in real ignorance is
the one that failed.

### One department explains most of the gap

Caption: dropping the highest-volume categories in each city, for both sets of rules. The same operation run both ways.
| subset | rules | n | prior | ceiling | recovered |
| --- | --- | --- | --- | --- | --- |
| Austin, all | mine | 6,029 | 0.494 | 0.883 | -1% |
| Austin, all | the model | 6,029 | 0.611 | 0.883 | 29% |
| Austin, minus ARR | mine | 4,008 | 0.644 | 0.881 | 38% |
| Austin, minus ARR | the model | 4,008 | 0.766 | 0.881 | 70% |
| SF, all | mine | 17,007 | 0.676 | 0.886 | 46% |
| SF, all | the model | 17,007 | 0.777 | 0.886 | 72% |
| SF, minus top 2 | mine | 7,255 | 0.571 | 0.851 | 20% |
| SF, minus top 2 | the model | 7,255 | 0.595 | 0.851 | 27% |

Austin Resource Recovery (Table 4) is 34% of the city's volume and 70% of its
work runs slow, yet both sets of rules call it fast, 0.37 for the model and 0.05
for mine. Take it out and the model reaches 70% against San Francisco's 72% and I
reach 38% against 46%, so the gap closes for both of us. A missed collection sits
open until the next scheduled route, a week away. The work is routine. The ticket
is not, and nothing in the phrase ARR - Compost tells you so.

Run on San Francisco the same operation cuts the other way, which is the more
important half of the table. Its two largest categories are 57% of test volume,
both fast and both called fast. Drop them and the ceiling barely moves, 0.886 to
0.851, while the model falls from 72% to 27% and I fall from 46% to 20%. A
two-line rule calling those two fast and the rest slow scores 0.699 by itself, so
the 72% rests on a few high-volume decisions, not 37 categories of reasoning.

ARR is a department prefix rather than a category called waste, so removing it
also takes out fast work it owns, such as ARR - Dead Animal Collection at 0.0%
slow. And Graffiti Public is 8.2% of San Francisco volume and 85.1% slow but
priced at 0.37 by the model, so the failure ARR shows in Austin is present there
too and no subset here removes it.

### What the prior does not beat

Given the same two columns, a conditional fitted on the real data beats the blind
rules by 0.108 in San Francisco and 0.272 in Austin, so real records win on this
task in both cities. Against a conditional using the category column alone the
rules look level, 0.777 to 0.771, but that comparator is missing the department
column the rules read, which is worth 0.115 in San Francisco, and the 0.0067
margin has a paired interval of [-0.201, +0.108].

### The finding

Stated as an ordering rather than a level, because the level moves with which
categories sit in the subset and the interval on it is wide. Blind rules beat
chance in San Francisco and not in Austin, the model's beat mine in both cities,
and removing one administratively clocked department closes most of the gap
between the cities for both authors.

My explanation for that ordering, that a blind prior holds where duration follows
from the job and fails where the clock is an administrative cycle, is a
hypothesis and not a result. I derived the partition from which categories my
rules got wrong, in one city, so it cannot fail against the data that produced
it. The test that would settle it is in the closing section.

### What the real rates are worth

Caption: rules written with the rates in hand, those rules carried to another city, and the city's own published service target.
| rules | tested on | threshold | AUC | ceiling | recovered |
| --- | --- | --- | --- | --- | --- |
| New York | New York | 5.4h | 0.840 | 0.918 | 81% |
| NY rules carried | Chicago | 118.0h | 0.496 | 0.717 | -2% |
| NY rules carried | Chicago | 5.4h | 0.581 | 0.717 | 37% |
| published target | New York | 5.4h | 0.830 | 0.918 | 79% |

Rules written with a city's rates in hand reach 81% there, above the 72% a blind
author got in San Francisco but not by much.

The last row I did not expect. New York publishes the target it holds itself to,
in days, per complaint type. Ranking tickets by that alone reaches 0.830, or 79%,
matching rules written while looking at the real outcomes and needing no
reasoning, no language model and no client records. If a client publishes what
they intend to take, that document is worth about as much as the exercise this
paper measures, and it is the first thing to ask for.

It bears on contamination too, since a language model may be recalling published
material rather than reasoning, and this row shows such a document carries most
of the signal. I could not find an equivalent dataset for Austin or San Francisco,
which narrows that worry without settling it.

Carried to Chicago at Chicago's own median they score 0.496, which an earlier
draft called actively misleading. That does not hold up (Table 5): the medians
are 5.4h and 118.0h, so the carried row asks a question nobody wrote the rules
for. At New York's own threshold they reach 0.581, or 37%. What is left is
mechanical, since they fire on 17.1% of Chicago rows, being New York acronyms.

### Distribution fidelity misses all of this

My first recorded hypothesis, fixed in `HYPOTHESIS.md` before I ran anything, was
that generated records matching real data to low-order fidelity would still hold
combinations the real process could never produce, and that accuracy would fall
as those rose. I tested it by fitting generators on real New York records,
sampling, training on the sample and testing on real records [11]. It failed, for
a structural reason. My pairwise generator draws department conditional on
category, so it cannot emit a pair it never saw and its 0.0% impossible rate is
an identity, and the learner is additive over one-hot columns with no interaction
terms, so a wrong combination could not have hurt it either. Both were settled by
the design before any data was touched. The work moved to the narrower question
this paper answers, which is why my stated hypothesis and my pre-registration are
not the same sentence.

The ladder still shows the one thing it is here for. Marginals alone lose almost
everything, 0.511 against a 0.918 ceiling, while adding pairwise dependence
recovers all of it at 0.917. A generator clearing the column shapes and column
pair trends a quality report scores [12] is indistinguishable from real records
here, so a distribution-level check cannot see the effect this paper measures. My
generators are conditional probability tables with no privacy noise, so they are
not PrivBayes or MST, but the order of structure they keep is the order those
methods fit [13, 14].

## Limits

Four cities, one domain, one task, and only two cities blind. New York is a
contamination control and Chicago its transfer target, so neither replicates
anything, and what does replicate is an author effect whose category intervals
cross zero. A 311 feed has three usable columns, no documents that must agree
with each other and no prices, so it is a thin stand-in for enterprise data.

The second author is a language model, the biggest hole in my design. These feeds are
widely mirrored, so blind means the session showed it no durations, not that the
weights hold none. Models have
memorised popular tabular datasets and score better on ones they have seen [15],
the exact failure this arm is open to, and it produces every headline number. I
did not record the prompt or the model version, so I cannot rerun it.

I wrote the San Francisco rules knowing what Austin had shown, so they are blind
to that city's rates but I am not blind to the lesson.

The Austin model arm has an ordering problem I should state. The commit that
evaluated my own rules names three categories with their measured slow rates:
compost at 96%, traffic signal maintenance at 8%, vehicle abatement at 94%. My
rules call all three the wrong way. The model wrote its Austin rules twelve hours
later and got two of the three right, using my own phrasing as keyword strings.
Compost it still called fast, which argues against the rates being handed over
wholesale, and both corrections are argued for in the file on grounds that do not
need them. I did not record the prompt, so I cannot settle it. The blind
condition I describe covers the catalogue pull, not what I had already written
down by the time that author was asked. The ARR result is a subset
I chose after seeing which family my rules got wrong, so it fits the numbers and
nothing has tested it. New York carries known artefacts too, including a
department that closes most tickets at exactly midnight.

## What it would take to answer the general question

Make the rules generate. My arms score rule sets against a conditional fitted on
real data, which measures how much of a conditional a person can guess, whereas
the question asks what generated data costs. Sampling rows from the taxonomy and
volume counts, labelling them with the prior, then training on those and testing
on real records would answer it directly. Then predict the failures before
looking: my ARR explanation says any category whose clock is an administrative
cycle will break a blind prior, so name those in a fifth city from the taxonomy
alone, record the list, then measure.

This bears on evaluating agents. If a taxonomy and a published target reach most
of the achievable skill, an agent scored on tickets generated from that taxonomy
is being scored on the part of the problem that was easiest to reconstruct. The
categories where a blind prior fails are the ones a generated benchmark will get
wrong, and they are invisible in the taxonomy it was built from. A high score
there is evidence about the generator, not the agent.

A prior can only be evaluated as a prior once per dataset, before anyone has seen
the outcomes, and the prediction has to come first. Of the predictions I made
here, the only one made in real ignorance is the one that turned out wrong.

## References

[1] A. F. Karr, C. N. Kohnen, A. Oganian et al. A
framework for evaluating the utility of data altered to protect confidentiality.
*The American Statistician*, 60(3):224-232, 2006.



[2] J. Snoke, G. M. Raab, B. Nowok et al. General and
specific utility measures for synthetic data. *J. R. Stat. Soc. A*,
181(3):663-688, 2018.



[3] L. Hansen, N. Seedat, M. van der Schaar et al. Reimagining synthetic tabular
data generation through data-centric AI. In *NeurIPS Datasets and Benchmarks*,
2023.



[4] B. van Breugel, Z. Qian and M. van der Schaar. Synthetic data, real errors: how
(not) to publish and use synthetic data. In *ICML*, PMLR 202, 2023.



[5] Y. Du and N. Li. Systematic assessment of tabular data synthesis. In *ACM
CCS*, 2025.



[6] R. Knauer, M. Koddenbrock, R. Wallsberger et al. Zero-shot decision tree
induction and embedding with large language models. In *KDD*, 2025.



[7] S. Hegselmann, A. Buendia, H. Lang et al. TabLLM: few-shot classification of
tabular data with large language models. In *AISTATS*, PMLR 206, 2023.



[8] A. Capstick, R. G. Krishnan and P. Barnaghi. AutoElicit: LLMs for expert prior
elicitation in predictive modelling. In *ICML*, PMLR vol. 267, 2025.

[9] C. A. Field and A. H. Welsh. Bootstrapping clustered data. *J. R. Stat. Soc.
B*, 69(3):369-390, 2007.



[10] A. C. Cameron, J. B. Gelbach and D. L. Miller. Bootstrap-based improvements for
inference with clustered errors. *Rev. Econ. Stat.*, 90(3):414-427, 2008.



[11] C. Esteban, S. L. Hyland and G. Rätsch. Real-valued (medical) time series
generation with recurrent conditional GANs. arXiv:1706.02633, 2017.



[12] SDV Team. Quality report: column shapes and column pair trends. SDMetrics
docs.sdv.dev/sdmetrics, accessed 24 Sep 2026.



[13] J. Zhang, G. Cormode, C. M. Procopiuc et al. PrivBayes: private data release
via Bayesian networks. *ACM Trans. Database Syst.*, 42(4):25, 2017.



[14] R. McKenna, G. Miklau and D. Sheldon. Winning the NIST contest. *J. Privacy and
Confidentiality*, 11(3), 2021.



[15] S. Bordt, H. Nori, V. Rodrigues et al. Elephants never forget: memorization of
tabular data in large language models. In *COLM*, 2024.
