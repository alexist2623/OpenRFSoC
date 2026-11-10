v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {OpenRFSoC DAC revision v1: shared steering switches} 120 -140 0 0 0.5 0.5 {}
T {VCAS = 0.9 V. Same 0-1.8 V logic inputs. Pre-layout prototype.} 120 -100 0 0 0.3 0.3 {}
T {Example: WGT=512; source/cascode m=512; switch W=1.12 um, m=1.} 120 -80 0 0 0.3 0.3 {}
N 340 40 340 90 {lab=outp}
N 620 40 620 90 {lab=outn}
N 340 150 340 200 {lab=common}
N 340 200 620 200 {lab=common}
N 620 150 620 200 {lab=common}
N 480 200 480 230 {lab=common}
N 480 290 480 370 {lab=tail}
N 480 430 480 470 {lab=vss}
N 340 120 380 120 {lab=vss}
N 620 120 660 120 {lab=vss}
N 480 260 520 260 {lab=vss}
N 480 400 520 400 {lab=vss}
C {devices/opin.sym} 340 40 3 0 {name=p1 lab=outp}
C {devices/opin.sym} 620 40 3 0 {name=p2 lab=outn}
C {devices/ipin.sym} 120 120 0 0 {name=p3 lab=gp}
C {devices/ipin.sym} 120 160 0 0 {name=p4 lab=gn}
C {devices/ipin.sym} 120 260 0 0 {name=p5 lab=vcas}
C {devices/ipin.sym} 120 400 0 0 {name=p6 lab=vbias}
C {devices/ipin.sym} 120 470 0 0 {name=p7 lab=vss}
C {devices/lab_pin.sym} 300 120 0 0 {name=l1 lab=gp}
C {devices/lab_pin.sym} 580 120 0 0 {name=l2 lab=gn}
C {devices/lab_pin.sym} 440 260 0 0 {name=l3 lab=vcas}
C {devices/lab_pin.sym} 440 400 0 0 {name=l4 lab=vbias}
C {devices/lab_pin.sym} 480 470 0 1 {name=l5 lab=vss}
C {devices/lab_pin.sym} 380 120 0 1 {name=l6 lab=vss}
C {devices/lab_pin.sym} 660 120 0 1 {name=l7 lab=vss}
C {devices/lab_pin.sym} 520 260 0 1 {name=l8 lab=vss}
C {devices/lab_pin.sym} 520 400 0 1 {name=l9 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 320 120 0 0 {name=Msp model=nfet_01v8 spiceprefix=X W=WSW L=0.15 nf=1 mult=1 nrd="'0.14/WSW'" nrs="'0.14/WSW'"}
C {sky130_fd_pr/nfet_01v8.sym} 600 120 0 0 {name=Msn model=nfet_01v8 spiceprefix=X W=WSW L=0.15 nf=1 mult=1 nrd="'0.14/WSW'" nrs="'0.14/WSW'"}
C {sky130_fd_pr/nfet_01v8.sym} 460 260 0 0 {name=Mcas model=nfet_01v8 spiceprefix=X W=1 L=0.3 nf=1 mult=WGT nrd=0.14 nrs=0.14}
C {sky130_fd_pr/nfet_01v8.sym} 460 400 0 0 {name=Mtail model=nfet_01v8 spiceprefix=X W=1 L=1 nf=1 mult=WGT nrd=0.14 nrs=0.14}
C {devices/code.sym} 760 280 0 0 {name=parameters only_toplevel=false value=".param WGT=512 SWDIV=192 WSW='max(0.42,0.42*WGT/SWDIV)'"}
T {Run make dac-revision for comparison.} 740 60 0 0 0.3 0.3 {}
T {Cell topology only: stimulus and load} 740 90 0 0 0.3 0.3 {}
T {are in the generated SPICE testbenches.} 740 120 0 0 0.3 0.3 {}
