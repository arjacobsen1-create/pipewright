"""Pipewright Level 2 - Business: maintenance parts.

Three files that belong together: a parts master, receipts (stock in)
and issues (stock out). The pipeline normalises part codes so the files
can join, quarantines what cannot be trusted (with reasons), computes
the stock position per part, and reconciles: total in minus total out
must equal the sum of all stock positions, to the unit.
"""
import json, re
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
ROOT = BASE.parent
DATA = BASE / "data"
OUT = ROOT / "output" / "level2"


def canon(part_id):
    """One canonical part code: PN-1042, however the file wrote it."""
    s = re.sub(r"[^A-Za-z0-9]", "", str(part_id)).upper()
    if s.startswith("PN") and s[2:].isdigit():
        return f"PN-{s[2:]}"
    return s


def load_movements(name, extra_col):
    df = pd.read_csv(DATA / name, dtype=str)
    df["part_key"] = df["part_id"].apply(canon)
    df["qty_num"] = pd.to_numeric(df["qty"], errors="coerce")
    return df


def run_pipeline():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"level": 2, "name": "Maintenance parts (business)"}
    quarantine = []

    # EXTRACT + master clean: dedupe, keep first cost, normalise UOM
    master_raw = pd.read_csv(DATA / "parts_master.csv", dtype=str)
    report["master_rows_in"] = len(master_raw)
    master_raw["part_key"] = master_raw["part_id"].apply(canon)
    master = (master_raw.drop_duplicates(subset=["part_key"], keep="first")
              .set_index("part_key"))
    report["master_parts"] = len(master)
    report["master_duplicates_removed"] = report["master_rows_in"] - len(master)
    master["uom"] = master["uom"].str.upper().replace({"EACH": "EA", "SET": "SET"})
    master["unit_cost"] = pd.to_numeric(master["unit_cost"], errors="coerce")

    # Movements: validate, quarantine with reasons
    cleaned = {}
    for name, extra in [("receipts.csv", "po_number"), ("issues.csv", "work_order")]:
        df = load_movements(name, extra)
        key = name.replace(".csv", "")
        report[f"{key}_rows_in"] = len(df)
        bad_qty = df[df["qty_num"].isna() | (df["qty_num"] <= 0)]
        for _, r in bad_qty.iterrows():
            quarantine.append({"source": key, "date": r["date"], "part_id": r["part_id"],
                               "qty": r["qty"], "reason": "quantity missing, not a number, or not positive"})
        df = df.drop(bad_qty.index)
        unknown = df[~df["part_key"].isin(master.index)]
        for _, r in unknown.iterrows():
            quarantine.append({"source": key, "date": r["date"], "part_id": r["part_id"],
                               "qty": r["qty"], "reason": "part not in the parts master"})
        df = df.drop(unknown.index)
        report[f"{key}_rows_used"] = len(df)
        cleaned[key] = df

    # TRANSFORM + ANALYZE: stock position per part
    rec = cleaned["receipts"].groupby("part_key")["qty_num"].sum().rename("received")
    iss = cleaned["issues"].groupby("part_key")["qty_num"].sum().rename("issued")
    pos = (master.join(rec).join(iss).fillna({"received": 0, "issued": 0}))
    pos["stock_position"] = pos["received"] - pos["issued"]
    pos["stock_value"] = (pos["stock_position"] * pos["unit_cost"]).round(2)
    pos = pos.reset_index().rename(columns={"part_key": "part_id"})

    # RECONCILE: in - out must equal the sum of positions, exactly
    total_in = int(cleaned["receipts"]["qty_num"].sum())
    total_out = int(cleaned["issues"]["qty_num"].sum())
    position_sum = int(pos["stock_position"].sum())
    report["total_received"] = total_in
    report["total_issued"] = total_out
    report["stock_position_sum"] = position_sum
    report["reconciles"] = (total_in - total_out) == position_sum

    neg = pos[pos["stock_position"] < 0].sort_values("stock_position")
    report["negative_stock_parts"] = len(neg)
    report["worst_negative"] = [
        {"part_id": r.part_id, "position": int(r.stock_position)} for r in neg.head(5).itertuples()
    ]
    report["parts_with_no_movement"] = int(((pos["received"] == 0) & (pos["issued"] == 0)).sum())
    report["stock_value_total"] = float(pos.loc[pos["stock_position"] > 0, "stock_value"].sum())
    report["quarantined_rows"] = len(quarantine)

    # LOAD
    pos.to_csv(OUT / "stock_position.csv", index=False)
    pd.DataFrame(quarantine).to_csv(OUT / "quarantine.csv", index=False)
    (OUT / "run_report.json").write_text(json.dumps(report, indent=2))
    print(f"L2 master {report['master_rows_in']}->{report['master_parts']} parts | "
          f"receipts {report['receipts_rows_in']}->{report['receipts_rows_used']} | "
          f"issues {report['issues_rows_in']}->{report['issues_rows_used']} | "
          f"quarantined {len(quarantine)} | reconciles: {report['reconciles']} | "
          f"negative stock parts: {len(neg)}")
    return report


if __name__ == "__main__":
    run_pipeline()
