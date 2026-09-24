# Note

The paper is at github.com/songwae2000/tgdc-research-paper. This repository is
the experiment, and `python run_all.py` prints every figure the paper quotes.

## Decisions

**Which narrow part.** "When does real operational data beat generated data" is
too big for a week. I took the part a generator has to solve: if you build a
client's data from a taxonomy and hand-written rules, how much of the behaviour
do the rules supply, and how much has to come from their records? Behaviour here
is one property, how long a task takes.

**Why 311 feeds.** Public, free, no key, and structurally a field service queue:
work type, owning team, intake channel, open and close timestamps. Four cities,
two complete weeks each. Austin and San Francisco carry the blind rules, New York
is the contrast written against its own rates, Chicago is where those are carried.

**The protocol.** I pulled each catalogue requesting only category names and row
counts, so no duration or outcome was available to write against. Rules were
committed with a recorded prediction, then evaluated. Austin and San Francisco
have two rule sets each, mine and a language model's, because the first version
of this work had a single author and the result turned out to be about me as
much as about the method.

## Results

Recovered skill is the share of the achievable margin over chance a rule set
reaches, against a ceiling fitted from the same two columns the rules use.

| rule set | Austin | San Francisco |
| --- | --- | --- |
| mine | -1% | 46% |
| model-written | 29% | 72% |

Both sets score far lower in Austin, and one department accounts for most of it.
Austin Resource Recovery is a third of the volume and 70% of its work runs slow,
because a missed collection stays open until the next scheduled route. Remove it
and the model-written set reaches 70% against San Francisco's 72%, mine 38%
against 46%. The work is routine. The ticket is not.

So the question cannot be answered yes or no. Blind rules hold where duration
follows from the job and fail where the clock is an administrative cycle, and
which a client has is not visible in their taxonomy.

Two controls say how much of that is reasoning. Shuffling the same rules'
verdicts across categories, which holds the taxonomy and row counts and destroys
only the reasoning, scores 0.501. Scoring by row count alone reaches 0.672
against my 0.676, so my own rules add almost nothing beyond volume.

Of four blind rule sets, three carry a prediction recorded before scoring. The
one producing the headline 72% does not. The only prediction made in genuine
ignorance is the one that failed.

## Limits

Three cost me a finding. Resampling categories rather than tickets, which is the
unit the rules are constant within, widens the headline interval to roughly 7% to
93% and leaves Austin's model-written set indistinguishable from chance. The
author effect, 0.116 and 0.101 in the same direction twice, crosses zero on that
unit. And the Chicago transfer failure was mostly a 22-fold threshold gap: held
at New York's own threshold the carried rules reach 37%, not the -2% I first
reported.

The row counts the pull supplied are themselves real operational data. The
language model cannot be blind to feeds this widely mirrored, and no prompt or
version was recorded, so that arm cannot be rerun. The ARR result is a subset
chosen after seeing the gap.

## Next step

Make the rules generate. Sample rows from the taxonomy and volume counts, label
them with the rules, train on that and test on real records. That turns a share
of achievable margin into the number the question asks for: how much of the
training value of real records does a generator built without them deliver?

Then name, from a fifth city's taxonomy alone and in advance, which families have
administrative clocks. Record the list. Then measure.
