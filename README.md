# Pipewright

**Messy In, Clean Out.**

A data pipeline project that teaches, by building, how a data pipeline
actually works: messy data in at one end, clean data and answers out at
the other, with every step shown, explained and proven on real runs.

## The six steps

Every level of this project runs the same six steps:

**Extract → Clean → Transform → Analyze → Load → Automate**

1. **Extract** — load the raw files, exactly as they arrive
2. **Clean** — duplicates out, junk stripped, impossible values caught,
   and anything that cannot be fixed is quarantined and reported, never hidden
3. **Transform** — reshape into groupings and joins a reader can act on
4. **Analyze** — the questions the data was collected to answer
5. **Load** — save clean data, summaries and a run report
6. **Automate** — the whole flow is one function per level, ready to schedule

## The three levels

The pattern never changes. The data grows.

| Level | Data | What it proves |
| ----- | ---- | -------------- |
| 1 — Teaching | Students: 62 rows, deliberately messy | The six steps end to end, small enough to check by eye |
| 2 — Business | Maintenance parts: a parts master plus receipts and issues files, thousands of rows that must join and reconcile | The same steps survive real-world mess: inconsistent part codes, unknown parts, negative stock, totals that disagree |
| 3 — Operations | Maintenance event logs arriving day by day for 14 days | The pipeline runs incrementally, keeps its place, and files a run report saying what it accepted, what it rejected, and why |

## Run it

```bash
pip install -r requirements.txt
python3 run_all.py
```

That runs all three levels and rebuilds the dashboard in `dashboard/`.
Open `dashboard/index.html` to see the results as a page: the demo.

Each level also runs on its own, e.g. `python3 level2_parts/pipeline.py`.

## The proof-first rule

A Pipewright pipeline reports what it did: rows in, rows out, rows
quarantined and the reason for each one. Silence is not a result.
Every level writes a run report next to its outputs.

## Data

All data in this project is synthetic, generated for the project and
labelled as such. No real organisation's data appears anywhere in it.

## Guide

`docs/HOW-IT-WORKS.md` explains each step the plain way: what it does,
what the data looks like before and after, and what usually goes wrong.
