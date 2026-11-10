"""Check FFT-grid sensitivity independently of the SPICE integration timestep."""
import json
from pathlib import Path
import re

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/dac14_2g"
report = json.loads((OUT / "results_all.json").read_text())
s = report["specification"]
raw = np.loadtxt(OUT / "tone_511_tt.dat", skiprows=1)
checks = []
for factor in (64, 128, 256):
    t = (s["settling_samples"] + np.arange(s["fft_samples"] * factor) / factor) / s["sample_rate_hz"]
    y = np.interp(t, raw[:, 0], raw[:, 2] - raw[:, 1])
    spectrum = abs(np.fft.rfft(y - y.mean())) * 2 / len(y)
    band = spectrum[1:s["fft_samples"] // 2 + 1].copy()
    band[510] = 0
    target_band = band[:int(s["output_band_hz"] * s["fft_samples"] / s["sample_rate_hz"])]
    checks.append({"fft_grid_samples_per_second": factor * s["sample_rate_hz"],
                   "sfdr_first_nyquist_dbc": float(20 * np.log10(spectrum[511] / band.max())),
                   "strongest_spur_hz": float((band.argmax() + 1) * s["sample_rate_hz"] / s["fft_samples"]),
                   "sfdr_0_to_500mhz_dbc": float(20 * np.log10(spectrum[511] / target_band.max()))})
integration_checks = []
for log in sorted(OUT.glob("convergence*/*.log")):
    text = log.read_text()
    failure = re.search(r"doAnalyses: TRAN:.*", text)
    integration_checks.append({"log": str(log.relative_to(ROOT)),
                               "status": "aborted" if failure else "inspect corresponding result JSON",
                               "failure": failure.group(0) if failure else None})
result = {"case": "TT 27C, 499.0234375 MHz; same 5 ps maximum-step SPICE waveform",
          "fft_grid_checks": checks,
          "integration_checks": integration_checks,
          "outp_min_v": float(raw[:, 1].min()), "outp_max_v": float(raw[:, 1].max()),
          "outn_min_v": float(raw[:, 2].min()), "outn_max_v": float(raw[:, 2].max()),
          "scope": "FFT resampling sensitivity only; not integration convergence or device reliability signoff."}
(OUT / "numerics.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
