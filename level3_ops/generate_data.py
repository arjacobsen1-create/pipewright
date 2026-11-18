"""Generate the synthetic Level 3 data: maintenance event logs,
one file per day for 14 days, the way a system would drop them."""
import csv, random
from pathlib import Path

random.seed(11)
D = Path(__file__).parent / "data"
D.mkdir(parents=True, exist_ok=True)
ASSETS = [f"AST-{n}" for n in range(101, 113)]
TYPES = ["WO_OPEN", "WO_CLOSE", "PART_USED", "INSPECT", "NOTE"]
weights = [0.22, 0.18, 0.30, 0.15, 0.15]

for day in range(1, 15):
    rows = []
    n = random.randint(28, 46)
    for _ in range(n):
        t = random.choices(TYPES, weights)[0]
        hh, mm = random.randint(5, 22), random.randint(0, 59)
        rows.append({
            "timestamp": f"2026-10-{day:02d}T{hh:02d}:{mm:02d}:00",
            "asset_id": random.choice(ASSETS),
            "event_type": t,
            "work_order": f"WO-{random.randint(2000, 2999)}" if t in ("WO_OPEN", "WO_CLOSE", "PART_USED") else "",
            "detail": {"WO_OPEN": "work order opened", "WO_CLOSE": "work order closed",
                       "PART_USED": "part fitted", "INSPECT": "inspection done",
                       "NOTE": "operator note"}[t],
        })
    # deliberate mess, sprinkled through the fortnight
    if day in (3, 8, 12):
        rows.append(dict(rows[5]))                       # exact duplicate event
    if day in (5, 10):
        rows.append({"timestamp": f"2026-10-{day:02d}T09:15:00", "asset_id": random.choice(ASSETS),
                     "event_type": "PING", "work_order": "", "detail": "unknown event type"})
    if day in (6, 13):
        rows.append({"timestamp": f"2026-10-{day:02d}T14:40:00", "asset_id": random.choice(ASSETS),
                     "event_type": "PART_USED", "work_order": "", "detail": "part fitted, no work order recorded"})
    if day == 9:
        rows.append({"timestamp": "", "asset_id": random.choice(ASSETS),
                     "event_type": "INSPECT", "work_order": "", "detail": "missing timestamp"})
    random.shuffle(rows)  # files arrive unordered, like real drops
    with open(D / f"day{day:02d}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "asset_id", "event_type", "work_order", "detail"])
        w.writeheader(); w.writerows(rows)
print("14 daily files written")
