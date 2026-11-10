"""Show matched DAC simulations, including improvements and regressions."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/dac14_revision"
def read(folder,file): return json.loads((OUT/folder/file).read_text())
def tone(folder): return read(folder,"results_high-tone.json")
before=tone("baseline_2p5ps");after=tone("revision_2p5ps")
keys=("resolution_bits","sample_rate_hz","fft_samples","settling_samples","tone_bins",
      "supply_v","full_scale_current_a","load_per_leg_ohm","external_cap_per_leg_f",
      "control_edge_s","control_low_v","control_high_v","signal_fraction_full_scale","max_spice_timestep_s")
assert all(before["specification"][k]==after["specification"][k] for k in keys),"Comparison conditions differ"
wave_b=np.load(OUT/"baseline_2p5ps/tone_511_tt.npz")
wave_a=np.load(OUT/"revision_2p5ps/tone_511_tt.npz")
def metrics(report,wave,folder):
    r=report["results"][0].copy()
    amp=wave["amplitude"].copy();freq=wave["frequency"]
    amp[0]=0;fund=amp[511];amp[511]=0
    mask=(freq>0)&(freq<=5e8)
    r["sfdr_0_to_500mhz_dbc"]=float(20*np.log10(fund/amp[mask].max()))
    band=(freq>0)&(freq<=1e9)
    r["strongest_spur_first_nyquist_hz"]=float(freq[np.flatnonzero(band)[np.argmax(amp[band])]])
    if "outp_max_v" not in r:
        raw=np.loadtxt(OUT/folder/"tone_511_tt.dat",skiprows=1)
        r.update(outp_min_v=float(raw[:,1].min()),outp_max_v=float(raw[:,1].max()),
                 outn_min_v=float(raw[:,2].min()),outn_max_v=float(raw[:,2].max()))
    r["max_single_ended_output_v"]=max(r["outp_max_v"],r["outn_max_v"])
    return r
mb=metrics(before,wave_b,"baseline_2p5ps");ma=metrics(after,wave_a,"revision_2p5ps")
step_b=read("baseline_steps","step_results.json")
step_a=read("revision_steps","step_results.json")
baseline_dc=read("baseline_dc","results_dc.json")["results"][0]
after_dc=read("revision_dc","results_dc.json")["results"][0]
convergence=[]
for name,basefolder,finefolder in [("before","baseline_2p5ps","baseline_1p25ps"),("after","revision_2p5ps","revision_1p25ps")]:
    coarse=tone(basefolder)["results"][0];fine=tone(finefolder)["results"][0]
    convergence.append({"design":name,"coarse_step_ps":2.5,"fine_step_ps":1.25,
                        "coarse_sfdr_dbc":coarse["sfdr_first_nyquist_dbc"],"fine_sfdr_dbc":fine["sfdr_first_nyquist_dbc"],
                        "sfdr_change_db":fine["sfdr_first_nyquist_dbc"]-coarse["sfdr_first_nyquist_dbc"],
                        "fundamental_relative_change":fine["fundamental_peak_v"]/coarse["fundamental_peak_v"]-1})
corners=[]
for c in ("ss","ff"):
    corners.append({"transient":tone(f"revision_{c}")["results"][0],
                    "dc":read(f"revision_{c}_dc","results_dc.json")["results"][0]})
summary={"before":mb,"after":ma,"before_dc":baseline_dc,"after_dc":after_dc,
         "before_steps":step_b["results"],"after_steps":step_a["results"],"numerical_checks":convergence,
         "additional_corner_checks":corners,
         "scope":"Same 2 GSPS, 499.0234375 MHz input sequence, 90% amplitude, 1.8 V, 50 ohm/200 fF per leg, no output filter; TT 27C comparison. Extra SS/FF checks use 496.09375 MHz, 512 samples. Ideal logic/bias, no random mismatch, thermal noise, PEX or timing closure."}
(OUT/"comparison.json").write_text(json.dumps(summary,indent=2)+"\n")

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,
                     "axes.spines.right":False,"figure.facecolor":"#f7f9fc","axes.facecolor":"white"})
old="#6b7280";new="#087f6d"
fig,axes=plt.subplots(2,2,figsize=(15,10))
fig.suptitle("SKY130 DAC: before / after circuit revision",fontsize=21,weight="bold",y=.98)
fig.text(.5,.935,"Identical 2 GSPS / 499.023 MHz stimulus | TT, 27 C, 1.8 V | No output filter",ha="center",fontsize=12)
for w,label,color in [(wave_b,"Before",old),(wave_a,"After",new)]:
    t=(w["time"]-w["time"][0])*1e9;m=t<6
    axes[0,0].plot(t[m],w["output"][m],label=label,color=color,lw=1.4)
    f=w["frequency"]/1e6;a=w["amplitude"];m=(f>0)&(f<=1000)
    axes[0,1].plot(f[m],20*np.log10(np.maximum(a[m]/a[511],1e-7)),color=color,label=label,lw=.7,alpha=.8)
axes[0,0].set(title="Actual differential output (not rescaled)",xlabel="Time (ns)",ylabel="Voltage (V)")
axes[0,1].set(title=f"SFDR 0-1 GHz: {mb['sfdr_first_nyquist_dbc']:.1f} -> {ma['sfdr_first_nyquist_dbc']:.1f} dBc\n0-500 MHz: {mb['sfdr_0_to_500mhz_dbc']:.1f} -> {ma['sfdr_0_to_500mhz_dbc']:.1f} dBc",xlabel="Frequency (MHz)",ylabel="Relative to fundamental (dBc)",ylim=(-100,5),xlim=(0,1000))
for folder,label,color in [("baseline_steps","Before",old),("revision_steps","After",new)]:
    d=np.load(OUT/folder/"large_step.npz")
    norm=(d["output"]-float(d["before"]))/float(d["after"]-d["before"])
    axes[1,0].plot(d["time"]*1e12,norm,color=color,label=label,lw=1.6)
    d=np.load(OUT/folder/"major_carry.npz")
    axes[1,1].plot(d["time"]*1e12,(d["output"]-float(d["after"]))*1e3,color=color,label=label,lw=1.5)
axes[1,0].axhline(1,color="#374151",ls="--",lw=.8)
axes[1,0].set(title="Large step 8192 -> 12288: gain-normalized",xlabel="Time after transition (ps)",ylabel="Fraction of each design's step",xlim=(0,500))
axes[1,1].set(title="Trade-off: major-carry glitch is WORSE",xlabel="Time after 8191 -> 8192 transition (ps)",ylabel="Error from final value (mV)",xlim=(0,500))
for ax in axes.flat:
    ax.grid(alpha=.18);ax.legend(fontsize=10);ax.set_axisbelow(True)
fig.subplots_adjust(top=.88,bottom=.13,hspace=.38,wspace=.24)
fig.text(.05,.025,"Simulated transistor models, ideal logic inputs and bias. No mismatch, thermal noise, pads/package or extracted layout.\nLarge-step tracking improves; small major-carry transitions regress. This is not 14-bit dynamic-accuracy or tapeout signoff.",fontsize=11,color="#8a3b12")
fig.savefig(OUT/"comparison.png",dpi=160,bbox_inches="tight")
fig.savefig(OUT/"comparison.svg",bbox_inches="tight");plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(13,4.8))
for file,label,color in [(OUT/"baseline_dc/dc_tt.npz","Before",old),(OUT/"revision_dc/dc_tt.npz","After",new)]:
    d=np.load(file)
    axes[0].plot(d["code"],d["inl"],color=color,label=label,lw=.9)
    axes[1].plot(d["code"][1:],d["dnl"],color=color,label=label,lw=.7)
axes[0].set(title="Endpoint INL, nominal perfectly matched devices",ylabel="LSB",xlabel="Input code")
axes[1].set(title="DNL: verify monotonicity as well as the spectrum",ylabel="LSB",xlabel="Input code")
for ax in axes: ax.grid(alpha=.18);ax.legend()
fig.tight_layout();fig.savefig(OUT/"dc_comparison.png",dpi=160);plt.close(fig)
print(json.dumps({"before_sfdr":mb["sfdr_first_nyquist_dbc"],"after_sfdr":ma["sfdr_first_nyquist_dbc"],
                  "numerical_checks":convergence,"after_dc_monotonic":after_dc["monotonic"]},indent=2))
