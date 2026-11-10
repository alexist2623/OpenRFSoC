"""Reproducible pre-layout SKY130 DAC feasibility simulation, not signoff."""
import argparse
import json
import os
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "analog/dac14_2g"
OUT = ROOT / "build/dac14_2g"
SPEC = json.loads((SRC / "spec.json").read_text())
REV = json.loads((ROOT / "env/versions.json").read_text())["digital_smoke_pdk_revision"]
PDK = Path(os.environ.get("PDK_ROOT", Path.home() / ".cache/openrfsoc/pdks")) / "ciel/sky130/versions" / REV / "sky130A"
WEIGHTS = [512] * 31 + [2**i for i in range(9)]


def controls(codes):
    codes = np.asarray(codes, dtype=np.int64)
    return np.column_stack([codes // 512 > i for i in range(31)] + [(codes >> i) & 1 for i in range(9)])


def base(corner, temp, behavioral_complements=True):
    s = SPEC
    variant=s.get("cell_variant", "baseline")
    cells={"baseline":("current_cell.spice","dac_cs_cell", ""),
           "output_cascode":("current_cell_output_cascode.spice","dac_cs_cell_output_cascode","vdd "),
           "driver":("current_cell_driver.spice","dac_cs_cell_driver","vdd vlow "),
           "compact":("current_cell_compact.spice","dac_cs_cell_compact",""),
           "compact_driver":("current_cell_compact_driver.spice","dac_cs_cell_compact_driver","vdd vlow "),
           "shared":("current_cell_shared.spice","dac_cs_cell_shared", "")}
    cell_file, cell_name, extra_ports=cells[variant]
    lines = [
        f"OpenRFSoC 14-bit 2 GSPS feasibility -- {corner}, {temp} C",
        f'.lib "{PDK}/libs.tech/combined/sky130.lib.spice" {corner}',
        f'.include "{SRC}/{cell_file}"',
        f".temp {temp}",
        f".options reltol=1e-5 abstol=1e-13 vntol=1e-8 method={s.get('integration_method', 'trap')} maxord=2 itl4={s.get('transient_iteration_limit', 10)} minbreak=1e-15",
        f"VDD vdd 0 {s['supply_v']}",
        f"IREF vdd vbias {s['full_scale_current_a']/16383:.12g}",
        "XREF vbias vbias 0 0 sky130_fd_pr__nfet_01v8 w=1 l=1 nf=1 ad=0.29 as=0.29 pd=2.58 ps=2.58",
        f"VCAS vcas 0 {s['cascode_bias_v']}",
        f"RP vdd outp {s['load_per_leg_ohm']}",
        f"RN vdd outn {s['load_per_leg_ohm']}",
        f"CP outp 0 {s['external_cap_per_leg_f']}",
        f"CN outn 0 {s['external_cap_per_leg_f']}",
    ]
    if variant=="compact_driver":
        lines.append(f'.include "{SRC}/current_cell_compact.spice"')
    if variant in ("driver","compact_driver"):
        lines.append(f"VLOW vlow 0 {s.get('driver_low_rail_v',1.2)}")
    for i, w in enumerate(WEIGHTS):
        params=f" WGT={w}"
        if variant.startswith("compact") or variant=="shared":
            params+=f" SWDIV={s.get('switch_divisor',16)}"
        lines.append(f"Xcell{i} outp outn gp{i} gn{i} vbias vcas {extra_ports}0 {cell_name}{params}")
        if behavioral_complements:
            lines.append(f"Bcomp{i} gn{i} 0 V={s['control_low_v']+s['control_high_v']}-v(gp{i})")
    return lines


def run_deck(name, lines, analysis):
    path = OUT / f"{name}.cir"
    data = OUT / f"{name}.dat"
    # Delete only this generated data file so a failed run cannot reuse stale output.
    data.unlink(missing_ok=True)
    # ngspice bug #887: coalesce coincident PWL corners. The interactive `tran`
    # command ignores minbreak; a .tran directive followed by `run` preserves it.
    # https://sourceforge.net/p/ngspice/bugs/887/
    lines += ["."+analysis, ".control", "set noaskquit", f"set num_threads={SPEC.get('simulation_threads',2)}", "set wr_singlescale", "set wr_vecnames", "set numdgt=12",
              "save v(outp) v(outn) v(vbias)", "run",
              f"wrdata {data} v(outp) v(outn) v(vbias)", "quit", ".endc", ".end"]
    path.write_text("\n".join(lines) + "\n")
    result = subprocess.run(["ngspice", "-b", "-o", str(OUT / f"{name}.log"), str(path)],
                            capture_output=True, text=True, timeout=1200, cwd=OUT)
    if result.returncode or not data.exists():
        raise RuntimeError(f"Simulation failed: {name}; inspect {OUT/name}.log")
    rows = np.loadtxt(data, skiprows=1)
    if rows.shape[0] < 100 or not np.isfinite(rows).all():
        raise RuntimeError(f"Invalid or incomplete output: {name}")
    return rows


def dc(corner="tt", temp=27):
    lines = base(corner, temp) + ["VCODE code 0 0"]
    for i in range(40):
        expr = f"(v(code)>={512*(i+1)})" if i < 31 else f"(floor(v(code)/{2**(i-31)})-2*floor(v(code)/{2**(i-30)}))"
        lines.append(f"Bdecode{i} gp{i} 0 V={SPEC['control_low_v']}+{SPEC['control_high_v']-SPEC['control_low_v']}*{expr}")
    data = run_deck(f"dc_{corner}", lines, "dc VCODE 0 16383 1")
    if len(data) != 16384:
        raise RuntimeError("DC sweep did not cover every code")
    # Increasing code steers sink current into outp, so define positive output as outn-outp.
    y = data[:, 2] - data[:, 1]
    lsb = (y[-1] - y[0]) / 16383
    inl = (y - (y[0] + np.arange(16384) * lsb)) / lsb
    dnl = np.diff(y) / lsb - 1
    np.savez(OUT / f"dc_{corner}.npz", code=data[:, 0], output=y, inl=inl, dnl=dnl)
    return {"corner": corner, "temperature_c": temp, "span_v": float(y[-1]-y[0]),
            "endpoint_inl_max_lsb": float(abs(inl).max()), "endpoint_dnl_max_lsb": float(abs(dnl).max()),
            "monotonic": bool((np.diff(y)>0).all()), "minimum_dnl_lsb": float(dnl.min())}


def driven_array(codes, corner="tt", temp=27):
    s=SPEC
    ts=1/s["sample_rate_hz"]
    count=len(codes)
    gates=controls(codes)
    paired_pwl=s.get("complement_mode", "pwl")=="pwl"
    lines=base(corner,temp,behavioral_complements=not paired_pwl)
    for i in range(40):
        # Exact complementary zero-impedance controls with explicit 20 ps edges.
        value=s["control_low_v"]+int(gates[0,i])*(s["control_high_v"]-s["control_low_v"])
        points=[(0.0,value)]
        for k in range(1,count):
            new=s["control_low_v"]+int(gates[k,i])*(s["control_high_v"]-s["control_low_v"])
            if new != value:
                points.extend([(k*ts,value),(k*ts+s['control_edge_s'],new)])
                value=new
        lines += [f"Vdrive{i} gp{i} 0 PWL("] + [f"+ {t:.12g} {v:.12g}" for t,v in points] + ["+ )"]
        if paired_pwl:
            # Same ideal complementary waveform, without a dependent B-source branch.
            total=s["control_low_v"]+s["control_high_v"]
            lines += [f"Vcomp{i} gn{i} 0 PWL("] + [f"+ {t:.12g} {total-v:.12g}" for t,v in points] + ["+ )"]
    return lines


def transient(tone_bin, corner="tt", temp=27):
    s=SPEC
    ts=1/s["sample_rate_hz"]
    count=s["fft_samples"]+s["settling_samples"]+2
    n=np.arange(count)
    codes=np.rint(8191.5*(1+s["signal_fraction_full_scale"]*np.sin(2*np.pi*tone_bin*n/s["fft_samples"]))).astype(int)
    lines=driven_array(codes,corner,temp)
    name=f"tone_{tone_bin}_{corner}"
    stop=(s["fft_samples"]+s["settling_samples"])*ts
    data=run_deck(name,lines,f"tran {ts/64:.12g} {stop:.12g} 0 {s['max_spice_timestep_s']:.12g}")
    if data[-1,0] < stop*(1-1e-8):
        raise RuntimeError("Transient stopped early")
    oversampling=64
    t=(s["settling_samples"]+np.arange(s["fft_samples"]*oversampling)/oversampling)*ts
    y=np.interp(t,data[:,0],data[:,2]-data[:,1])
    ideal_codes=codes[s["settling_samples"]:s["settling_samples"]+s["fft_samples"]]
    ideal=np.repeat((2*ideal_codes/16383-1)*s["full_scale_current_a"]*s["load_per_leg_ohm"],oversampling)
    fft=abs(np.fft.rfft(y-y.mean()))*2/len(y)
    ideal_fft=abs(np.fft.rfft(ideal-ideal.mean()))*2/len(ideal)
    band=fft[1:s["fft_samples"]//2+1].copy()
    fundamental=fft[tone_bin]
    band[tone_bin-1]=0
    sfdr=float(20*np.log10(fundamental/band.max()))
    sinad=float(10*np.log10(fundamental**2/np.sum(band**2)))
    np.savez(OUT/f"{name}.npz", time=t, output=y, ideal=ideal,
             frequency=np.fft.rfftfreq(len(y),ts/oversampling), amplitude=fft, ideal_amplitude=ideal_fft)
    return {"corner":corner,"temperature_c":temp,"tone_bin":tone_bin,
            "frequency_hz":tone_bin*s["sample_rate_hz"]/s["fft_samples"],
            "fundamental_peak_v":float(fundamental),"sfdr_first_nyquist_dbc":sfdr,
            "deterministic_sinad_first_nyquist_db":sinad,
            "outp_min_v":float(data[:,1].min()),"outp_max_v":float(data[:,1].max()),
            "outn_min_v":float(data[:,2].min()),"outn_max_v":float(data[:,2].max()),
            "note":"Coherent FFT of continuous waveform resampled at 128 GS/s; band 0..1 GHz. Ideal logic stimuli and bias. No thermal noise, random mismatch, clock-tree or layout parasitics. Driver transistors only present in *_driver variants."}


def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument("--spec",type=Path,help="JSON test-condition overrides")
    parser.add_argument("--corner",choices=["tt","ss","ff"],default="tt")
    parser.add_argument("--temperature",type=float,default=27)
    parser.add_argument("--threads",type=int)
    parser.add_argument("--case", choices=["dc","tones","high-tone","corners","all"],default="all")
    parser.add_argument("--max-step-ps",type=float)
    parser.add_argument("--method", choices=["trap", "gear"])
    parser.add_argument("--complement-mode", choices=["pwl", "behavioral"])
    parser.add_argument("--iteration-limit", type=int)
    parser.add_argument("--output-dir",type=Path)
    args=parser.parse_args()
    if args.spec is not None:
        SPEC.update(json.loads(args.spec.read_text()))
    if args.threads is not None:
        if args.threads<1: parser.error("threads must be positive")
        SPEC["simulation_threads"]=args.threads
    if args.iteration_limit is not None:
        if args.iteration_limit < 1:
            parser.error("iteration-limit must be positive")
        SPEC["transient_iteration_limit"]=args.iteration_limit
    if args.method is not None:
        SPEC["integration_method"]=args.method
    if args.complement_mode is not None:
        SPEC["complement_mode"]=args.complement_mode
    if args.max_step_ps is not None:
        if args.max_step_ps <= 0:
            parser.error("max-step-ps must be positive")
        SPEC["max_spice_timestep_s"]=args.max_step_ps*1e-12
    if args.output_dir is not None:
        OUT=args.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    report_path=OUT/f"results_{args.case}.json"
    # A partial rerun must not leave a previous success report looking current.
    report_path.unlink(missing_ok=True)
    if not (PDK/"libs.tech/combined/sky130.lib.spice").exists():
        raise SystemExit("Run make smoke to install the pinned SKY130 PDK first")
    allcodes=np.arange(16384)
    assert np.array_equal(controls(allcodes)@np.array(WEIGHTS),allcodes)
    results={"specification":SPEC,"pdk_revision":REV,"case":args.case,"results":[]}
    if args.case in ("dc","all"):
        results["results"].append(dc(args.corner,args.temperature)); print(json.dumps(results["results"][-1]),flush=True)
    if args.case in ("tones","high-tone","all"):
        for k in (SPEC["tone_bins"][-1:] if args.case=="high-tone" else SPEC["tone_bins"]):
            results["results"].append(transient(k,args.corner,args.temperature));print(json.dumps(results["results"][-1]),flush=True)
    if args.case in ("corners","all"):
        for corner,temp in [("ss",85),("ff",-40)]:
            results["results"].append(transient(SPEC["tone_bins"][-1],corner,temp));print(json.dumps(results["results"][-1]),flush=True)
    report_path.write_text(json.dumps(results,indent=2)+"\n")


if __name__ == "__main__":
    main()
