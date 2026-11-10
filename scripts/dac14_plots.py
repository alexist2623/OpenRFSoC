"""Plot actual ngspice output; never substitute ideal traces for circuit results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/dac14_2g"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,
                     "axes.spines.right":False,"figure.facecolor":"#f7f9fc","axes.facecolor":"white"})


def architecture():
    fig,ax=plt.subplots(figsize=(15,6.5))
    ax.set(xlim=(0,15),ylim=(0,6.5));ax.axis("off")
    def box(x,y,w,h,text,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.12",facecolor=color,edgecolor="#364152",lw=1.2))
        ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=12)
    def arrow(a,b,label=""):
        ax.annotate("",xy=b,xytext=a,arrowprops={"arrowstyle":"->","lw":1.7,"color":"#364152"})
        if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+0.13,label,ha="center",fontsize=10)
    ax.text(0,6.1,"OpenRFSoC | 14-bit / 2 GSPS DAC feasibility design",fontsize=21,weight="bold")
    ax.text(0,5.6,"One channel prototype • 500 MHz output-band target • SKY130 1.8 V NMOS",fontsize=13)
    box(0.2,2.7,2.0,1.5,"14-bit code\n2 GSPS target\n500 ps / sample","#dce9fc")
    box(3.0,2.7,2.3,1.5,"5 + 9 decoder\nRegistered RTL\nFunctional test only","#dce9fc")
    box(6.2,3.5,3.2,1.3,"31 unary banks\n512 × Iunit each","#ffe4ba")
    box(6.2,1.7,3.2,1.3,"9 binary banks\n1, 2, ... 256 × Iunit","#ffe4ba")
    box(10.4,2.7,2.0,1.5,"Differential\ncurrent sum\nOUTP / OUTN","#ffe4ba")
    box(13.2,2.7,1.5,1.5,"50 Ω / leg\n200 fF / leg\nIdeal load","#e5e7eb")
    arrow((2.35,3.45),(2.85,3.45));arrow((5.45,3.7),(6.05,4.1),"31 controls")
    arrow((5.45,3.2),(6.05,2.35),"9 controls")
    arrow((9.55,4.1),(10.25,3.7));arrow((9.55,2.35),(10.25,3.2));arrow((12.55,3.45),(13.05,3.45))
    ax.text(7.8,1.0,"31 × 512 + (1 + 2 + ... + 256) = 16,383 units\nIunit = 0.6104 µA target; nominal simulated full scale differs",ha="center",fontsize=12)
    ax.text(0,0.12,"SPICE: ideal reference, cascode bias and complementary 20 ps controls.\nSerializer, retiming drivers, clock tree, calibration, pad/package and extracted layout are not implemented.",fontsize=11,color="#8a3b12")
    fig.savefig(OUT/"architecture.png",dpi=160,bbox_inches="tight");fig.savefig(OUT/"architecture.svg",bbox_inches="tight");plt.close(fig)


def results():
    report=json.loads((OUT/"results_all.json").read_text())
    rows=report["results"]
    dc=next(x for x in rows if "span_v" in x)
    tones=[x for x in rows if "tone_bin" in x]
    fig,axes=plt.subplots(2,2,figsize=(15,10))
    fig.suptitle("SKY130 DAC: actual pre-layout ngspice results",fontsize=21,weight="bold",y=0.97)
    fig.text(0.5,0.925,"14-bit input, 2 GSPS controls | Ideal bias / drivers | No random mismatch or thermal noise",ha="center",fontsize=12,color="#8a3b12")
    d=np.load(OUT/"tone_511_tt.npz")
    t=(d["time"]-d["time"][0])*1e9
    mask=t<8
    axes[0,0].plot(t[mask],d["ideal"][mask],color="#9299a3",lw=1.0,label="Ideal 14-bit ZOH (reference)")
    axes[0,0].plot(t[mask],d["output"][mask],color="#1858a8",lw=1.5,label="SKY130 transistor simulation")
    axes[0,0].set(title="499.023 MHz output, typical corner",xlabel="Time within FFT window (ns)",ylabel="Differential voltage (V)")
    axes[0,0].legend(fontsize=9)
    for corner,label,color in [("tt","TT, 27°C","#1858a8"),("ss","SS, 85°C","#c15128"),("ff","FF, -40°C","#24825f")]:
        q=np.load(OUT/f"tone_511_{corner}.npz")
        f=q["frequency"]/1e6; a=q["amplitude"]
        m=(f>0)&(f<=1000)
        axes[0,1].plot(f[m],20*np.log10(np.maximum(a[m]/a[511],1e-7)),lw=0.65,label=label,color=color,alpha=.85)
    axes[0,1].set(title="Continuous-waveform spectrum, first Nyquist band",xlabel="Frequency (MHz)",ylabel="Relative to fundamental (dBc)",ylim=(-100,5),xlim=(0,1000))
    axes[0,1].legend(fontsize=9)
    q=np.load(OUT/"dc_tt.npz")
    axes[1,0].plot(q["code"],q["inl"],color="#1858a8",lw=1.5)
    axes[1,0].set(title="Nominal endpoint INL (perfectly matched devices)",xlabel="Input code",ylabel="INL (LSB)")
    axes[1,0].text(.03,.94,"Perfect matching only.\nNot a yield / mismatch result.",transform=axes[1,0].transAxes,color="#8a3b12",fontsize=10,va="top")
    labels=[f"{x['frequency_hz']/1e6:.1f} MHz\n{x['corner'].upper()} / {x['temperature_c']}°C" for x in tones]
    bars=axes[1,1].bar(labels,[x["sfdr_first_nyquist_dbc"] for x in tones],color=["#487aac","#1858a8","#c15128","#24825f"])
    axes[1,1].bar_label(bars,fmt="%.1f dBc",padding=4,fontsize=10)
    axes[1,1].set(title="Pre-layout deterministic SFDR",ylabel="SFDR (dBc)",ylim=(0,max(x["sfdr_first_nyquist_dbc"] for x in tones)+14))
    axes[1,1].tick_params(axis="x",labelsize=9)
    for ax in axes.flat: ax.grid(alpha=.18);ax.set_axisbelow(True)
    fig.text(.05,.016,f"Nominal differential span: {dc['span_v']:.4f} Vpp | No pads / package / clock jitter / physical routing.\nInitial circuit; numerical workaround and before/after comparison are documented in revision-v1.md.\nThese results do not establish 14 effective bits, silicon performance, or tapeout readiness.",fontsize=10.5,color="#8a3b12")
    fig.subplots_adjust(top=.87,bottom=.12,hspace=.38,wspace=.25)
    fig.savefig(OUT/"results.png",dpi=160,bbox_inches="tight");fig.savefig(OUT/"results.pdf",bbox_inches="tight");plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    architecture();results()
    print(f"Plots: {OUT/'architecture.png'} and {OUT/'results.png'}")
