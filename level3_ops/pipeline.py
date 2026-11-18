"""Pipewright Level 3 - Operations: maintenance event logs.

Fourteen daily files arrive one at a time. The pipeline processes
them in order, keeps a running picture per asset, and files a run
report for the whole fortnight: events accepted, events rejected,
and the reason for every rejection. Nothing is silently dropped.
"""
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
ROOT = BASE.parent
DATA = BASE / "data"
OUT = ROOT / "output" / "level3"
KNOWN_TYPES = {"WO_OPEN", "WO_CLOSE", "PART_USED", "INSPECT", "NOTE"}


def run_pipeline():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"level": 3, "name": "Maintenance event logs (operations)", "days": []}
    quarantine = []
    accepted_frames = []

    for day_file in sorted(DATA.glob("day*.csv")):
        df = pd.read_csv(day_file, dtype=str).fillna("")
        day = {"file": day_file.name, "rows_in": len(df)}
        before = len(df)
        df = df.drop_duplicates()
        day["duplicates_removed"] = before - len(df)

        def reject(mask, reason):
            for _, r in df[mask].iterrows():
                quarantine.append({"file": day_file.name, "timestamp": r["timestamp"],
                                   "asset_id": r["asset_id"], "event_type": r["event_type"],
                                   "reason": reason})
            return df[~mask]

        df = reject(df["timestamp"].str.strip() == "", "missing timestamp")
        df = reject(~df["event_type"].isin(KNOWN_TYPES), "unknown event type")
        df = reject((df["event_type"] == "PART_USED") & (df["work_order"].str.strip() == ""),
                    "part used with no work order recorded")
        day["rows_accepted"] = len(df)
        day["rows_rejected"] = day["rows_in"] - day["duplicates_removed"] - len(df)
        report["days"].append(day)
        accepted_frames.append(df)

    events = pd.concat(accepted_frames, ignore_index=True)
    events["timestamp"] = pd.to_datetime(events["timestamp"])
    events = events.sort_values("timestamp")

    # ANALYZE: the running picture per asset
    summary = (events.groupby("asset_id")["event_type"]
               .value_counts().unstack(fill_value=0)
               .reindex(columns=["WO_OPEN", "WO_CLOSE", "PART_USED", "INSPECT", "NOTE"], fill_value=0))
    summary["open_work_orders"] = summary["WO_OPEN"] - summary["WO_CLOSE"]
    report["events_accepted"] = len(events)
    report["events_rejected"] = len(quarantine)
    report["duplicates_removed"] = sum(d["duplicates_removed"] for d in report["days"])
    report["work_orders_opened"] = int((events["event_type"] == "WO_OPEN").sum())
    report["work_orders_closed"] = int((events["event_type"] == "WO_CLOSE").sum())
    report["parts_used_events"] = int((events["event_type"] == "PART_USED").sum())
    report["assets_with_open_work"] = int((summary["open_work_orders"] > 0).sum())

    # LOAD
    events.to_csv(OUT / "events_clean.csv", index=False)
    summary.to_csv(OUT / "asset_summary.csv")
    pd.DataFrame(quarantine).to_csv(OUT / "quarantine.csv", index=False)
    (OUT / "run_report.json").write_text(json.dumps(report, indent=2))
    print(f"L3 14 days | accepted {report['events_accepted']} | rejected {report['events_rejected']} "
          f"| duplicates {report['duplicates_removed']} | WO opened {report['work_orders_opened']} "
          f"closed {report['work_orders_closed']} | assets with open work {report['assets_with_open_work']}")
    return report


if __name__ == "__main__":
    run_pipeline()
