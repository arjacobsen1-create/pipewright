"""Pipewright Level 1 - Teaching: student results.

Six steps on a small, deliberately messy file:
EXTRACT -> CLEAN -> TRANSFORM -> ANALYZE -> LOAD -> AUTOMATE
Writes a run report (output/level1/run_report.json) with rows in,
rows out, and every value that had to be fixed or filled.
"""
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
ROOT = BASE.parent
RAW = BASE / "data" / "students_raw.csv"
OUT = ROOT / "output" / "level1"


def extract(path):
    return pd.read_csv(path, dtype=str)


def clean(df, report):
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)
    for col in ["study_hours", "attendance", "exam_score"]:
        df[col] = (df[col].astype(str)
                   .str.replace("hrs", "", regex=False)
                   .str.replace("%", "", regex=False)
                   .str.strip())
        df[col] = pd.to_numeric(df[col], errors="coerce")
    impossible = int((df["exam_score"] > 100).sum() + (df["attendance"] > 100).sum())
    df.loc[df["exam_score"] > 100, "exam_score"] = pd.NA
    df.loc[df["attendance"] > 100, "attendance"] = pd.NA
    report["impossible_values_removed"] = impossible
    filled = int(df[["study_hours", "attendance", "exam_score"]].isna().sum().sum())
    for col in ["study_hours", "attendance", "exam_score"]:
        df[col] = df[col].fillna(df[col].median())
    report["gaps_filled_with_median"] = filled
    return df


def transform(df):
    def grade(s):
        return "Needs Improvement" if s < 50 else ("Good" if s < 80 else "Excellent")
    def band(a):
        return "Low" if a < 60 else ("Mid" if a < 85 else "High")
    df = df.copy()
    df["grade_group"] = df["exam_score"].apply(grade)
    df["attendance_band"] = df["attendance"].apply(band)
    return df


def analyze(df):
    by_att = (df.groupby("attendance_band")["exam_score"].mean().round(1)
              .reindex(["Low", "Mid", "High"]))
    corr = df[["study_hours", "attendance", "exam_score"]].corr()["exam_score"]
    return by_att, corr


def run_pipeline():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"level": 1, "name": "Students (teaching)"}
    raw = extract(RAW)
    report["rows_in"] = len(raw)
    df = clean(raw, report)
    df = transform(df)
    by_att, corr = analyze(df)
    df.to_csv(OUT / "students_clean.csv", index=False)
    by_att.rename("avg_exam_score").to_csv(OUT / "summary.csv")
    report["rows_out"] = len(df)
    report["avg_score_by_attendance"] = {k: float(v) for k, v in by_att.items()}
    report["correlation_study_hours"] = round(float(corr["study_hours"]), 2)
    report["correlation_attendance"] = round(float(corr["attendance"]), 2)
    (OUT / "run_report.json").write_text(json.dumps(report, indent=2))
    print(f"L1 EXTRACT {report['rows_in']} rows -> CLEAN {report['rows_out']} rows "
          f"(dupes {report['duplicates_removed']}, impossible {report['impossible_values_removed']}, "
          f"gaps filled {report['gaps_filled_with_median']}) -> LOAD output/level1/")
    return report


if __name__ == "__main__":
    run_pipeline()
