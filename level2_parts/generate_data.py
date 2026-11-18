"""Generate the synthetic Level 2 data: maintenance parts.
Three files that belong together and do not quite agree:
parts_master.csv, receipts.csv, issues.csv. Mess is deliberate."""
import csv, random
from pathlib import Path

random.seed(42)
D = Path(__file__).parent / "data"
D.mkdir(parents=True, exist_ok=True)

WORDS = ["bearing", "seal kit", "gasket", "filter", "valve", "pump rotor",
         "motor brush", "coupling", "belt", "sensor", "switch", "hose",
         "o-ring set", "impeller", "shaft", "gear", "fuse pack", "relay",
         "actuator", "nozzle"]
parts = []
for i in range(1, 121):
    pid = f"PN-{1000 + i}"
    parts.append({
        "part_id": pid,
        "description": f"{random.choice(WORDS)} {random.choice(['std', 'HD', 'LP', 'X2', 'pro'])}",
        "uom": random.choice(["EA", "ea", "Each", "EA", "SET", "set"]),
        "unit_cost": round(random.uniform(4, 900), 2),
        "criticality": random.choice(["A", "B", "C", "B", "C"]),
    })

with open(D / "parts_master.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["part_id", "description", "uom", "unit_cost", "criticality"])
    w.writeheader()
    for p in parts:
        w.writerow(p)
    # deliberate mess: three duplicated master rows, one with a changed cost
    w.writerow(parts[7]); w.writerow(parts[7])
    dup = dict(parts[40]); dup["unit_cost"] = dup["unit_cost"] + 25.0; w.writerow(dup)

def variant(pid):
    """The same part, written the ways real files write it."""
    r = random.random()
    if r < 0.62: return pid
    if r < 0.78: return pid.replace("-", "")
    if r < 0.90: return pid.lower()
    return " " + pid + " "

def daterange_rows(n, kind):
    rows = []
    for _ in range(n):
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        p = random.choice(parts)
        qty = random.randint(1, 40)
        row = {"date": f"2026-{month:02d}-{day:02d}", "part_id": variant(p["part_id"]), "qty": qty}
        if kind == "receipt":
            row["po_number"] = f"PO-{random.randint(5000, 5999)}" if random.random() > 0.06 else ""
        else:
            row["work_order"] = f"WO-{random.randint(2000, 2999)}" if random.random() > 0.05 else ""
        rows.append(row)
    return rows

receipts = daterange_rows(1800, "receipt")
issues = daterange_rows(1600, "issue")
# deliberate mess: unknown parts, bad quantities
for _ in range(25):
    receipts.append({"date": "2026-06-15", "part_id": f"PN-{9000 + random.randint(1, 60)}",
                     "qty": random.randint(1, 10), "po_number": "PO-5999"})
for _ in range(20):
    issues.append({"date": "2026-07-02", "part_id": f"XX-{random.randint(100, 999)}",
                   "qty": random.randint(1, 5), "work_order": "WO-2999"})
for r in random.sample(receipts, 12):
    r["qty"] = -random.randint(1, 9)          # negative receipt: invalid
for r in random.sample(issues, 9):
    r["qty"] = "lots"                          # non-numeric quantity: invalid
for r in random.sample(issues, 6):
    r["qty"] = 500                             # absurd issue qty: drives negative stock

with open(D / "receipts.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "part_id", "qty", "po_number"])
    w.writeheader(); w.writerows(receipts)
with open(D / "issues.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "part_id", "qty", "work_order"])
    w.writeheader(); w.writerows(issues)
print(f"master rows: {len(parts) + 3}, receipts: {len(receipts)}, issues: {len(issues)}")
