"""Reproduce the matched before/after comparison and explicitly scoped corner checks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/dac14_revision"
parser=argparse.ArgumentParser()
parser.add_argument("--after-only",action="store_true",help="Use already verified baseline runs from this revision study")
parser.add_argument("--jobs",type=int,default=1)
parser.add_argument("--threads",type=int,default=2)
parser.add_argument("--resume",action="store_true",help="Reuse complete matching reports only; intended for the same circuit-source revision")
args=parser.parse_args()
if args.jobs<1 or args.threads<1: parser.error("jobs and threads must be positive")
config=ROOT/"analog/dac14_2g/revision_v1.json"
short=json.loads(config.read_text())
short.update(fft_samples=512,settling_samples=64,tone_bins=[127],simulation_threads=2)
OUT.mkdir(parents=True,exist_ok=True)
short_config=OUT/"corner_spec.json";short_config.write_text(json.dumps(short,indent=2)+"\n")
jobs=[]
def sim(name,options):
    jobs.append((name,[sys.executable,str(ROOT/"scripts/dac14_sim.py"),*options,"--threads",str(args.threads),"--output-dir",str(OUT/name)]))
def step(name,options):
    jobs.append((name,[sys.executable,str(ROOT/"scripts/dac14_step.py"),*options,"--threads",str(args.threads),"--output-dir",str(OUT/name)]))
if not args.after_only:
    sim("baseline_dc",["--case","dc"])
    sim("baseline_2p5ps",["--case","high-tone","--max-step-ps","2.5"])
    sim("baseline_1p25ps",["--case","high-tone","--max-step-ps","1.25"])
    step("baseline_steps",[])
sim("revision_2p5ps",["--case","high-tone","--spec",str(config),"--max-step-ps","2.5"])
sim("revision_1p25ps",["--case","high-tone","--spec",str(config),"--max-step-ps","1.25"])
sim("revision_dc",["--case","dc","--spec",str(config)])
step("revision_steps",["--spec",str(config)])
for corner,temp in [("ss","85"),("ff","-40")]:
    sim(f"revision_{corner}",["--case","high-tone","--spec",str(short_config),"--corner",corner,"--temperature",temp])
    sim(f"revision_{corner}_dc",["--case","dc","--spec",str(config),"--corner",corner,"--temperature",temp])
def run(item):
    name,command=item
    if args.resume:
        def option(key,default=None):
            return command[command.index(key)+1] if key in command else default
        case=option("--case")
        path=OUT/name/(f"results_{case}.json" if case else "step_results.json")
        try:
            previous=json.loads(path.read_text())
            expected=json.loads((ROOT/"analog/dac14_2g/spec.json").read_text())
            if option("--spec"): expected.update(json.loads(Path(option("--spec")).read_text()))
            if option("--max-step-ps"): expected["max_spice_timestep_s"]=float(option("--max-step-ps"))*1e-12
            match=all(previous["specification"].get(k)==v for k,v in expected.items() if k not in ("simulation_threads","status"))
            if case:
                match=match and all(r["corner"]==option("--corner","tt") and r["temperature_c"]==float(option("--temperature","27")) for r in previous["results"])
            match=match and bool(previous["results"]) and bool(list((OUT/name).glob("*.npz")))
            if match:
                result={"case":name,"exit_code":0,"reused_complete_report":True}
                print(json.dumps(result),flush=True)
                return result
        except (FileNotFoundError,ValueError,KeyError):
            pass
    print(json.dumps({"case":name,"status":"running","threads":args.threads}),flush=True)
    with (OUT/f"{name}_runner.log").open("w") as log:
        process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result={"case":name,"exit_code":process.returncode}
    print(json.dumps(result),flush=True)
    return result
with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    results=list(pool.map(run,jobs))
(OUT/"run_status.json").write_text(json.dumps(results,indent=2)+"\n")
raise SystemExit(1 if any(r["exit_code"] for r in results) else 0)
