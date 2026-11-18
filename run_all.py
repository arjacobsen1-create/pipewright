"""Pipewright: run all three levels, then rebuild the dashboard.
This is the Automate step for the whole project."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent

for script in ["level1_students/pipeline.py", "level2_parts/pipeline.py",
               "level3_ops/pipeline.py", "dashboard/build_dashboard.py"]:
    print(f"--- {script}")
    subprocess.run([sys.executable, str(ROOT / script)], check=True)
print("Done. Open dashboard/index.html for the demo.")
