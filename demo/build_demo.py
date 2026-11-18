"""Build the Pipewright interactive demo from the real run outputs.
Emits demo/demo.html: pick a level, walk the six steps, see the actual
rows before and after each step, with the run's real numbers."""
import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"
PAGE = Path(__file__).parent / "demo.html"


def canon(s):
    s = re.sub(r"[^A-Za-z0-9]", "", str(s)).upper()
    return f"PN-{s[2:]}" if s.startswith("PN") and s[2:].isdigit() else s


def level1():
    rep = json.loads((OUT / "level1" / "run_report.json").read_text())
    raw = pd.read_csv(ROOT / "level1_students" / "data" / "students_raw.csv", dtype=str).fillna("(blank)")
    clean = pd.read_csv(OUT / "level1" / "students_clean.csv")
    scored = []
    for _, r in raw.iterrows():
        score = 0
        if r["exam_score"] == "(blank)" or r["attendance"] == "(blank)" or r["study_hours"] == "(blank)":
            score += 3
        if r["exam_score"].isdigit() and int(r["exam_score"]) > 100:
            score += 3
        if not r["attendance"].replace("%", "").isdigit():
            score += 3
        if "hrs" in r["study_hours"] or "%" in r["attendance"]:
            score += 1
        if score:
            c = clean[clean["student_id"] == r["student_id"]].iloc[0]
            scored.append((score, {"id": r["student_id"],
                          "before": f'{r["study_hours"]} | {r["attendance"]} | {r["exam_score"]}',
                          "after": f'{c["study_hours"]} hrs | {c["attendance"]}% | {int(c["exam_score"])}'}))
    scored.sort(key=lambda t: -t[0])
    pairs = [p for _, p in scored[:5]]
    return {"report": rep, "pairs": pairs}

def level2():
    rep = json.loads((OUT / "level2" / "run_report.json").read_text())
    rec = pd.read_csv(ROOT / "level2_parts" / "data" / "receipts.csv", dtype=str)
    rec["key"] = rec["part_id"].apply(canon)
    variants = []
    for key, g in rec.groupby("key"):
        forms = sorted(set(g["part_id"]))
        if len(forms) >= 3:
            variants = [{"form": f, "key": key} for f in forms[:4]]
            break
    q = pd.read_csv(OUT / "level2" / "quarantine.csv").head(5)
    quar = [{"part": r.part_id, "qty": str(r.qty), "reason": r.reason} for r in q.itertuples()]
    pos = pd.read_csv(OUT / "level2" / "stock_position.csv")
    neg = pos.sort_values("stock_position").head(5)
    neg_rows = [{"part": r.part_id, "desc": r.description, "received": int(r.received),
                 "issued": int(r.issued), "position": int(r.stock_position)} for r in neg.itertuples()]
    return {"report": rep, "variants": variants, "quarantine": quar, "negative": neg_rows}

def level3():
    rep = json.loads((OUT / "level3" / "run_report.json").read_text())
    q = pd.read_csv(OUT / "level3" / "quarantine.csv")
    quar = [{"file": r.file, "type": r.event_type, "reason": r.reason} for r in q.itertuples()]
    days = [{"file": d["file"], "in": d["rows_in"], "accepted": d["rows_accepted"],
             "rejected": d["rows_rejected"], "dupes": d["duplicates_removed"]} for d in rep["days"]]
    return {"report": rep, "quarantine": quar, "days": days}

DATA = {"l1": level1(), "l2": level2(), "l3": level3()}
template = (Path(__file__).parent / "demo_template.html").read_text()
PAGE.write_text(template.replace("/*__DATA__*/", json.dumps(DATA)))
print(f"demo written: {PAGE} ({PAGE.stat().st_size:,} bytes)")
