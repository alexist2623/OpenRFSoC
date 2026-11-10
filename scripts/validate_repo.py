"""Cross-platform checks for bootstrap files; no EDA installation required."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
for folder in ("docs", "rtl", "dv", "firmware", "analog", "physical", "third_party", "scripts", "env"):
    if not (ROOT / folder).is_dir():
        errors.append(f"Missing directory: {folder}")
for folder in ("scripts", "env", "physical", ".vscode"):
    for path in (ROOT / folder).rglob("*"):
        if "runs" in path.relative_to(ROOT).parts:
            continue
        if path.suffix not in (".json", ".py", ".sh", ".ps1"):
            continue
        data = path.read_bytes()
        if b"\r\n" in data:
            errors.append(f"CRLF in Linux-managed source: {path.relative_to(ROOT)}")
        text = data.decode("utf-8")
        if path.suffix == ".json":
            json.loads(text)
        if path.suffix == ".py":
            ast.parse(text, filename=str(path))
config_path = ROOT / "physical/sky130/bringup_counter/config.json"
config = json.loads(config_path.read_text())
for reference in config["VERILOG_FILES"]:
    if not reference.startswith("dir::"):
        errors.append(f"Unexpected source reference: {reference}")
        continue
    source = (config_path.parent / reference.removeprefix("dir::")).resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():
        errors.append(f"Invalid physical-flow source: {reference}")
versions = json.loads((ROOT / "env/versions.json").read_text())
if len(versions["librelane"]["commit"]) != 40:
    errors.append("LibreLane must be pinned to a complete commit ID")
if len(versions["digital_smoke_pdk_revision"]) != 40:
    errors.append("PDK revision must be a complete commit ID")
if errors:
    raise SystemExit("\n".join(errors))
print("PASS: repository structure, JSON, Python syntax, LF endings and RTL source paths")
