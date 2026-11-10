"""Small RC regression for the simultaneous-PWL-corner issue (ngspice #887).

Numerical conditions follow the upstream issue's published reproducer:
https://sourceforge.net/p/ngspice/bugs/887/
No PDK, nonlinear devices, ideal analog switches, or tolerance relaxation.
"""
from pathlib import Path
import subprocess
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/dac14_revision/minbreak_regression"
OUT.mkdir(parents=True,exist_ok=True)
results=[]
for mode in ("original", "option_with_interactive_tran", "fixed"):
    lines=[f"Simultaneous PWL breakpoint regression: {mode}"]
    for i,offset_ns in enumerate((8,7,4,3)):
        lines += [f"Vstim{i} s{i} 0 PWL(0 0 {0.001-offset_ns*1e-9:.12g} 0 0.001 0 0.001000001 1)",
                  f"Rload{i} s{i} out 1k"]
    lines += ["Cload out 0 1n"]
    if mode!="original": lines += [".options minbreak=1e-15"]
    command="tran 2n 0.001002 0.000999 4n"
    if mode=="fixed": lines += ["."+command]
    lines += [".control","save v(out)","run" if mode=="fixed" else command,
              "print vecmax(time)","quit",".endc",".end"]
    deck=OUT/f"{mode}.cir"; log=OUT/f"{mode}.log"
    deck.write_text("\n".join(lines)+"\n")
    subprocess.run(["ngspice","-b","-o",str(log),str(deck)],capture_output=True,check=True,timeout=60)
    text=log.read_text()
    end=float(re.search(r"vecmax\(time\)\s*=\s*(\S+)",text).group(1))
    results.append({"case":mode,"end_time_s":end,"aborted":"aborted" in text,
                    "reached_stop":abs(end-0.001002)<1e-12})
(OUT/"results.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps(results,indent=2))
assert not results[0]["reached_stop"] and not results[1]["reached_stop"] and results[2]["reached_stop"]
