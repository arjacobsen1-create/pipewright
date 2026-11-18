# How Pipewright Works — the plain version

A pipeline is a factory line for data. Raw material arrives messy at one
end; something clean and useful leaves at the other. Six stations on the
line, always in the same order.

## 1. Extract — bring the data in, exactly as it is

No fixing, no judging. Just load the file.

Real example, Level 1, as it arrived:

```
S006, 2.7 hrs, 69%,        <- score missing
S021, 5.0 hrs, abc%, 71    <- attendance is not a number
```

If you start "helpfully" fixing things while loading, you can never prove
later what the file actually said. Extract first. Touch nothing.

**What goes wrong here:** the file is not there, or it changed shape
(a column renamed itself). A good pipeline stops and says so, loudly.

## 2. Clean — fix what is fixable, quarantine what is not

Three kinds of mess, three different answers:

- **Written oddly, meaning clear** — `3.9 hrs`, `65%`, `pn-1042`, `PN1042`.
  Strip the decoration, standardise the format. In Level 2, the same part
  arrived written four different ways; until the codes were normalised,
  the three files could not join at all.
- **Impossible** — an exam score of 118 out of 100, a negative receipt.
  It cannot be true, so it cannot stay. Level 1 caught 3; Level 2
  quarantined 21 rows with quantities that were missing, not numbers,
  or not positive.
- **Unknown** — a movement for a part that is not in the parts master.
  Level 2 quarantined 45 of those. You do not invent a part to make the
  row fit; you set the row aside, with its reason written on it.

The rule that matters: **nothing is silently dropped.** Every rejected
row lands in a quarantine file with the reason. Silence is not a result.

## 3. Transform — reshape it into something a person can use

Cleaning makes data correct. Transforming makes it useful: groupings
(grades from scores, Low/Mid/High from attendance), joins (receipts and
issues meeting the parts master), and one row per thing you care about
(one row per part, with its stock position).

## 4. Analyze — ask the questions

Now, and only now, the questions the data was collected for:

- Level 1: does attendance track the score? (Yes — 39.9 average for Low
  attendance, 74.4 for High. Study hours tracked it even closer, 0.88.)
- Level 2: what do we hold, and what is wrong? (48 parts in negative
  stock — more issued than ever received. That is not a warehouse fact,
  it is a data problem, and the pipeline flags it instead of hiding it.)
- Level 3: what is still open? (139 work orders opened in the fortnight,
  103 closed, 9 assets with work still open at the end.)

## 5. Load — save it where the next thing can find it

Clean data, summaries, and the run report, saved as files. The run
report is part of the load, not an afterthought: rows in, rows out,
rows quarantined, and the reconciliation result.

**Reconciliation** is the pipeline proving its own arithmetic. Level 2:
36,601 units received, 35,252 issued, difference 1,349 — and the sum of
every part's stock position is also 1,349. Two different paths to the
same number. If they ever disagree, the pipeline says so and the run
is not trusted until a human looks.

## 6. Automate — wrap it so it can run without you

Each level is one function. `run_all.py` runs all three levels and
rebuilds the dashboard. Put it on a schedule and the factory line runs
itself — Level 3 is built exactly for that, one new file a day, keeping
its place, reporting every run.

## The one idea to keep

The steps are not the clever part. The discipline is: extract honestly,
clean openly, quarantine with reasons, reconcile before you trust, and
report everything. A pipeline that does that can be believed. One that
quietly tidies as it goes cannot, no matter how good its charts look.
