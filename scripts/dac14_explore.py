"""Small, identical 496 MHz benches screen circuit candidates before long runs."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import argparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/dac14_revision/explore"
candidates={
    "baseline":{},
    "high_common_mode":{"control_low_v":1.2,"control_high_v":1.8},
    "output_cascode":{"cell_variant":"output_cascode","control_low_v":1.0,"control_high_v":1.4},
    "physical_driver":{"cell_variant":"driver","driver_low_rail_v":1.2},
}
parser=argparse.ArgumentParser()
parser.add_argument("--compact",action="store_true")
parser.add_argument("--headroom",action="store_true")
parser.add_argument("--final-sizing",action="store_true")
parser.add_argument("--shared",action="store_true")
parser.add_argument("--jobs",type=int,default=1)
parser.add_argument("--threads",type=int,default=2)
args=parser.parse_args()
if args.jobs<1 or args.threads<1: parser.error("jobs and threads must be positive")
if args.compact:
    OUT=ROOT/"build/dac14_revision/explore_compact"
    candidates={
        "compact8":{"cell_variant":"compact","switch_divisor":8},
        "compact16":{"cell_variant":"compact","switch_divisor":16},
        "compact32":{"cell_variant":"compact","switch_divisor":32},
        "compact16_cm":{"cell_variant":"compact","switch_divisor":16,"control_low_v":1.2},
        "compact16_driver":{"cell_variant":"compact_driver","switch_divisor":16,"driver_low_rail_v":1.2},
    }
if args.headroom:
    OUT=ROOT/"build/dac14_revision/explore_headroom"
    candidates={
        "compact64":{"cell_variant":"compact","switch_divisor":64},
        "compact64_bias":{"cell_variant":"compact","switch_divisor":64,"cascode_bias_v":0.9},
        "compact128_bias":{"cell_variant":"compact","switch_divisor":128,"cascode_bias_v":0.9},
        "compact128_cm":{"cell_variant":"compact","switch_divisor":128,"cascode_bias_v":0.9,"control_low_v":0.6},
    }
if args.final_sizing:
    OUT=ROOT/"build/dac14_revision/explore_final_sizing"
    candidates={
        "compact256_bias":{"cell_variant":"compact","switch_divisor":256,"cascode_bias_v":0.9},
        "compact256_lower_bias":{"cell_variant":"compact","switch_divisor":256,"cascode_bias_v":0.85},
        "compact256_cm":{"cell_variant":"compact","switch_divisor":256,"cascode_bias_v":0.9,"control_low_v":0.6},
        "compact128_lower_bias":{"cell_variant":"compact","switch_divisor":128,"cascode_bias_v":0.85},
    }
if args.shared:
    OUT=ROOT/"build/dac14_revision/explore_shared"
    candidates={
        "shared128":{"cell_variant":"shared","switch_divisor":128,"cascode_bias_v":0.9},
        "shared192":{"cell_variant":"shared","switch_divisor":192,"cascode_bias_v":0.9},
        "shared256":{"cell_variant":"shared","switch_divisor":256,"cascode_bias_v":0.9},
        "compact128":{"cell_variant":"compact","switch_divisor":128,"cascode_bias_v":0.9},
    }
def run(item):
    name,changes=item
    folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
    spec={"fft_samples":512,"settling_samples":64,"tone_bins":[127],"max_spice_timestep_s":2.5e-12,"simulation_threads":args.threads,**changes}
    config=folder/"spec.json";config.write_text(json.dumps(spec,indent=2)+"\n")
    dc_result={}
    if args.shared:
        with (folder/"dc_runner.log").open("w") as log:
            subprocess.run([sys.executable,str(ROOT/"scripts/dac14_sim.py"),"--case","dc",
                            "--spec",str(config),"--output-dir",str(folder)],stdout=log,stderr=subprocess.STDOUT,check=True)
        dc_result=json.loads((folder/"results_dc.json").read_text())["results"][0]
        print(json.dumps({"candidate":name,"dc":dc_result}),flush=True)
    with (folder/"runner.log").open("w") as log:
        process=subprocess.run([sys.executable,str(ROOT/"scripts/dac14_sim.py"),"--case","high-tone",
                                "--spec",str(config),"--output-dir",str(folder)],stdout=log,stderr=subprocess.STDOUT)
    result={"candidate":name,"exit_code":process.returncode,"dc":dc_result}
    if process.returncode==0:
        result.update(json.loads((folder/"results_high-tone.json").read_text())["results"][0])
    print(json.dumps(result),flush=True)
    return result
with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    results=list(pool.map(run,candidates.items()))
(OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
