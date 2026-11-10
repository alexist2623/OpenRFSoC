"""Record actual local tools. A tool's presence is not a successful flow run."""
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
commands = {
    "iverilog": ["iverilog", "-V"],
    "verilator": ["verilator", "--version"],
    "yosys": ["yosys", "-V"],
    "openroad": ["openroad", "-version"],
    "librelane": ["librelane", "--version"],
    "ngspice": ["ngspice", "--version"],
}
report = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(),
    "pinned_environment": json.loads((ROOT / "env/versions.json").read_text()),
    "tools": {},
}
missing = []
for name, command in commands.items():
    executable = shutil.which(command[0])
    entry = {"path": executable}
    if not executable:
        missing.append(name)
    else:
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=30)
            output = (result.stdout + result.stderr).strip()
            entry.update(returncode=result.returncode, version_output=output[:3000])
        except (OSError, subprocess.TimeoutExpired) as error:
            entry["error"] = str(error)
            missing.append(name)
    report["tools"][name] = entry
for name in ("xschem", "klayout", "magic", "netgen", "make"):
    path = shutil.which(name)
    report["tools"][name] = {"path": path}
    if not path:
        missing.append(name)
destination = ROOT / ".local/environment-report.json"
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(report, indent=2) + "\n")
print(f"Environment report: {destination}")
for name, entry in report["tools"].items():
    print(f"{name}: {'available' if entry.get('path') else 'MISSING'}")
if missing:
    raise SystemExit("Missing or unavailable tools: " + ", ".join(missing))
