"""Validate the ideal RC response; this does not validate a DAC, ADC or PDK."""
import math
import re
import sys
from pathlib import Path

log = Path(sys.argv[1]).read_text(errors="replace")
match = re.search(r"vout_1us\s*=\s*([-+\deE.]+)", log, re.IGNORECASE)
if not match:
    raise SystemExit("FAIL: ngspice did not produce the vout_1us measurement")
value = float(match.group(1))
expected = 1.0 - math.exp(-1.0)
if not math.isfinite(value) or abs(value - expected) > 0.02:
    raise SystemExit(f"FAIL: RC response {value}, expected approximately {expected}")
print(f"PASS: ideal RC response {value:.6f} V")
