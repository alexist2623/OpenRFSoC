"""Isolated ideal-drive experiment. Does not implement the required driver."""
import json
import dac14_sim as sim

sim.OUT = sim.ROOT / "build/dac14_2g/reduced_swing"
sim.OUT.mkdir(parents=True, exist_ok=True)
sim.SPEC.update(control_low_v=0.8, control_high_v=1.6)
result=sim.transient(511)
report={"specification":sim.SPEC,"results":[result],"scope":"Ideal reduced-swing gate experiment; physical driver absent."}
(sim.OUT/"results_experiment.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(result),flush=True)
