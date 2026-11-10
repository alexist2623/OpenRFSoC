"""Measure large-step tracking and major-carry glitch without an output filter."""
import argparse
import json
import numpy as np
from pathlib import Path
import dac14_sim as sim

parser=argparse.ArgumentParser()
parser.add_argument("--spec",type=Path)
parser.add_argument("--threads",type=int,default=2)
parser.add_argument("--output-dir",type=Path,required=True)
args=parser.parse_args()
if args.spec: sim.SPEC.update(json.loads(args.spec.read_text()))
if args.threads<1: parser.error("threads must be positive")
sim.SPEC["simulation_threads"]=args.threads
sim.OUT=args.output_dir.resolve();sim.OUT.mkdir(parents=True,exist_ok=True)
results=[]
for name,a,b in [("large_step",8192,12288),("major_carry",8191,8192)]:
    codes=np.array([a]*8+[b]*9)
    data=sim.run_deck(name,sim.driven_array(codes),"tran 1p 8n 0 1.25p")
    if data[-1,0]<8e-9*(1-1e-8): raise RuntimeError("Incomplete step simulation")
    y=data[:,2]-data[:,1];t=data[:,0]
    before=float(np.interp(3.9e-9,t,y)); after=float(np.interp(7.9e-9,t,y))
    times=np.arange(501)*1e-12
    wave=np.interp(times+4e-9,t,y)
    error=wave-after; span=after-before
    overshoot=max(0,float(wave.max()-max(before,after)),float(min(before,after)-wave.min()))
    result={"transition":name,"code_before":a,"code_after":b,"before_v":before,"after_v":after,
            "step_v":span,"overshoot_beyond_endpoint_range_v":overshoot,
            "absolute_tracking_error_area_v_ps":float(np.trapezoid(abs(error),times)*1e12),
            "normalized_tracking_error_area_ps":float(np.trapezoid(abs(error),times)/abs(span)*1e12),
            "settled_error_at_450ps_v":float(abs(wave[450]-after))}
    np.savez(sim.OUT/f"{name}.npz",time=times,output=wave,reference=np.full(len(times),after),before=before,after=after)
    results.append(result)
report={"specification":sim.SPEC,"results":results,
        "scope":"No external filter. Same two static endpoint codes and 500 ps observation window. Tracking-error area includes settling and is not pure glitch impulse energy."}
(sim.OUT/"step_results.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
