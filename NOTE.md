# Note

The paper is at github.com/songwae2000/tgdc-research-paper. This repository is
the experiment, and `python run_all.py` prints every figure the paper quotes.

## Decisions

**Which narrow part.** "When does real operational data beat generated data" is
too big for a week. I took the part a generator has to solve: if you build a
client's data from a taxonomy and hand-written rules, how much of the behaviour
do the rules supply, and how much has to come from their records? Behaviour here
is one property, how long a task takes.

**Why 311 feeds.** Public, free, no key, and structurally a field-service queue:
work type, owning team, intake channel, open and close timestamps. Four cities,
two complete calendar weeks each. Austin and San Francisco carry the blind rule
sets. New York is the contrast, with rules written against its own rates, and
Chicago is where those rules are carried to see what survives.

**The protocol.** I pulled each city's service catalogue requesting only category
names and row counts, so no duration or outcome was available to write against.
Rules were written from that alone, committed with a recorded prediction, and
only then evaluated. Austin and San Francisco each have two such rule sets, one
mine and one written by a language model given the same catalogue, because the
first version of this
work had a single author and the result turned out to be about me as much as
about the method. A language model is a second author, not a second practitioner.

## Results

Each rule set reasons over two columns, the service category and the owning
department. Fitting the conditional rate directly from those two columns gives
the ceiling. The ceiling beats chance by some margin, and recovered skill is the
share of that margin a rule set reaches. Below zero is worse than chance.

| rule set | Austin | San Francisco |
| --- | --- | --- |
| mine | -1% | 46% |
| model-written | 29% | 72% |

Both sets score far lower in Austin. For the model-written set, removing one
category family closes almost all of that gap. Austin's waste collection is a third of its volume and runs slow,
because a missed-collection ticket stays open until the next scheduled route. The
work is routine. The ticket is not, and nothing in the phrase `ARR - Compost`
says so.

So the question cannot be answered yes or no. Blind rules hold where duration
follows from the job and fail where the clock is an administrative cycle, and
which of those a client has is not visible in their taxonomy.

Three of the four blind rule sets carry a prediction recorded before that set was
scored. The first, for my own Austin rules, was written when the project had no
results at all, and it missed by a wide margin. The other two were recorded once
Austin had been scored, so I already knew roughly what to expect. The San
Francisco model-written set, the one that produces the 72%, carries no recorded
prediction. The single prediction made in genuine ignorance is the one that
failed.

## Limits

The ones that would change the result.

The paper's intervals resample individual tickets. The rules are functions of
category, so the honest unit is the category, and San Francisco has 37 of them.
Resampling categories instead, 2,000 draws with the ceiling held fixed, widens
the headline interval to roughly 7% to 93% recovered, and the endpoints move a
point or two with the seed. Austin's model-written set stops being
distinguishable from chance. The paper reports intervals far too narrow for the claims built on them.

The catalogue pull gave both authors category names and row counts, and row
counts are real operational data. Scoring tickets by category frequency alone
reaches AUC 0.672 in San Francisco, against 0.676 for the rules I wrote. Mine add
almost nothing beyond volume.

The model-written rules are the stronger set everywhere, and these feeds are
among the most widely mirrored public datasets in existence. Blind here means the
session showed the model no durations. It does not mean the weights hold none.

The waste-collection explanation rests on a subset chosen after seeing the gap.
It fits the numbers and nothing has tested it.

## Next step

Make the rules generate. Sample rows from the taxonomy and volume counts, label
them with the rules, train on that and test on real records, with train-on-real
as the ceiling. That turns "the rules reach 72% of the achievable margin" into
the number the question asks for: how much of the training value of real records
does a generator built without them deliver?

Then the falsification the mechanism implies. Name in advance, from the taxonomy
alone, which families in a fifth city have administrative clocks. Record the
list. Then measure.
