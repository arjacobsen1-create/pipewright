"""Build the Pipewright dashboard (the demo) from the real run outputs.
Reads output/level*/run_report.json and the output CSVs; writes
dashboard/index.html. If a number is on this page, it came from a run."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"
PAGE = Path(__file__).parent / "index.html"


def load(level):
    return json.loads((OUT / level / "run_report.json").read_text())


def main():
    r1, r2, r3 = load("level1"), load("level2"), load("level3")
    q2 = pd.read_csv(OUT / "level2" / "quarantine.csv")
    q2_reasons = q2["reason"].value_counts().to_dict()
    q3 = pd.read_csv(OUT / "level3" / "quarantine.csv")
    q3_reasons = q3["reason"].value_counts().to_dict() if len(q3) else {}

    steps = ["Extract", "Clean", "Transform", "Analyze", "Load", "Automate"]
    step_html = "".join(
        f'<div class="step s{i+1}">{s}</div>' + ('<div class="arrow">&#8594;</div>' if i < 5 else "")
        for i, s in enumerate(steps))

    att_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in r1["avg_score_by_attendance"].items())
    neg_rows = "".join(
        f"<tr><td>{n['part_id']}</td><td>{n['position']}</td></tr>" for n in r2["worst_negative"])
    q2_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in q2_reasons.items())
    q3_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in q3_reasons.items())

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipewright — Messy In, Clean Out</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f6f7f9; color: #1c2333; }}
  header {{ background: #14324f; color: #fff; padding: 28px 22px; }}
  header h1 {{ margin: 0; font-size: 30px; }}
  header p {{ margin: 6px 0 0; opacity: .85; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 18px; }}
  .steps {{ display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin: 18px 0 6px; }}
  .step {{ padding: 8px 12px; border-radius: 8px; color: #fff; font-weight: 600; font-size: 14px; }}
  .s1 {{ background: #2e6da4; }} .s2 {{ background: #d97706; }} .s3 {{ background: #7c3aed; }}
  .s4 {{ background: #059669; }} .s5 {{ background: #be3455; }} .s6 {{ background: #334155; }}
  .arrow {{ color: #8a94a6; font-weight: 700; }}
  .card {{ background: #fff; border: 1px solid #e2e6ee; border-radius: 12px; padding: 18px; margin: 16px 0; }}
  .card h2 {{ margin: 0 0 4px; font-size: 20px; }}
  .card .sub {{ color: #5b6577; margin: 0 0 12px; }}
  .stats {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }}
  .stat {{ background: #f0f3f8; border-radius: 8px; padding: 8px 12px; }}
  .stat b {{ display: block; font-size: 18px; }}
  .stat span {{ font-size: 12px; color: #5b6577; }}
  table {{ border-collapse: collapse; margin: 8px 0; }}
  td, th {{ border: 1px solid #e2e6ee; padding: 5px 10px; font-size: 14px; text-align: left; }}
  .ok {{ color: #059669; font-weight: 700; }}
  footer {{ color: #5b6577; font-size: 13px; padding: 10px 22px 30px; max-width: 880px; margin: 0 auto; }}
</style></head><body>
<header><h1>Pipewright</h1><p>Messy In, Clean Out. One pipeline pattern, three levels of data.</p></header>
<main>
  <div class="steps">{step_html}</div>
  <p>Every level runs the same six steps. The pattern never changes; the data grows.</p>

  <div class="card"><h2>Level 1 — Students (teaching)</h2>
  <p class="sub">A small file, deliberately messy, checkable by eye.</p>
  <div class="stats">
    <div class="stat"><b>{r1['rows_in']}</b><span>rows in</span></div>
    <div class="stat"><b>{r1['rows_out']}</b><span>rows out</span></div>
    <div class="stat"><b>{r1['duplicates_removed']}</b><span>duplicates removed</span></div>
    <div class="stat"><b>{r1['impossible_values_removed']}</b><span>impossible values caught</span></div>
    <div class="stat"><b>{r1['gaps_filled_with_median']}</b><span>gaps filled</span></div>
  </div>
  <p><b>Average exam score by attendance band</b></p>
  <table><tr><th>Attendance</th><th>Average score</th></tr>{att_rows}</table>
  <p>Study hours tracked the score most closely (correlation {r1['correlation_study_hours']}),
     attendance next ({r1['correlation_attendance']}).</p></div>

  <div class="card"><h2>Level 2 — Maintenance parts (business)</h2>
  <p class="sub">A parts master plus receipts and issues files that must join and reconcile.</p>
  <div class="stats">
    <div class="stat"><b>{r2['master_parts']}</b><span>parts in master</span></div>
    <div class="stat"><b>{r2['receipts_rows_used'] + r2['issues_rows_used']:,}</b><span>movement rows used</span></div>
    <div class="stat"><b>{r2['quarantined_rows']}</b><span>rows quarantined</span></div>
    <div class="stat"><b>{r2['negative_stock_parts']}</b><span>parts in negative stock</span></div>
  </div>
  <p>Reconciliation: {r2['total_received']:,} received &minus; {r2['total_issued']:,} issued
     = {r2['stock_position_sum']:,} &mdash; matches the sum of every part's stock position.
     <span class="ok">Reconciles: {'YES' if r2['reconciles'] else 'NO'}</span></p>
  <p><b>Worst negative stock</b> (issued more than was ever received — a data problem, flagged, not hidden)</p>
  <table><tr><th>Part</th><th>Position</th></tr>{neg_rows}</table>
  <p><b>Why rows were quarantined</b></p>
  <table><tr><th>Reason</th><th>Rows</th></tr>{q2_rows}</table></div>

  <div class="card"><h2>Level 3 — Event logs (operations)</h2>
  <p class="sub">Fourteen daily files, processed in order, with a run report for the fortnight.</p>
  <div class="stats">
    <div class="stat"><b>{r3['events_accepted']}</b><span>events accepted</span></div>
    <div class="stat"><b>{r3['events_rejected']}</b><span>events rejected</span></div>
    <div class="stat"><b>{r3['duplicates_removed']}</b><span>duplicates removed</span></div>
    <div class="stat"><b>{r3['work_orders_opened']}</b><span>work orders opened</span></div>
    <div class="stat"><b>{r3['work_orders_closed']}</b><span>work orders closed</span></div>
    <div class="stat"><b>{r3['assets_with_open_work']}</b><span>assets with work still open</span></div>
  </div>
  <p><b>Why events were rejected</b></p>
  <table><tr><th>Reason</th><th>Events</th></tr>{q3_rows}</table></div>
</main>
<footer>All data on this page is synthetic, generated for the project. Every number
comes from an actual pipeline run; the run reports sit next to the outputs that produced them.</footer>
</body></html>"""
    PAGE.write_text(html)
    print(f"dashboard written: {PAGE} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
