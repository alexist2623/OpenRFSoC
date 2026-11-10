SHELL := /bin/bash
PDK_ROOT ?= $(HOME)/.cache/openrfsoc/pdks
DESIGN_CONFIG ?= physical/sky130/bringup_counter/config.json

.PHONY: help validate doctor lint sim synth analog-smoke check smoke pnr
.PHONY: dac-check dac-sim dac-plots dac
.PHONY: dac-revision dac-revision-resume dac-compare
.NOTPARALLEL: dac

help:
	@printf '%s\n' 'Run inside nix-shell:' '  make check        repository, RTL, synthesis and SPICE checks' '  make smoke        upstream LibreLane SKY130 flow smoke test' '  make pnr          counter RTL-to-GDS experiment (50 MHz target)' '  make dac          DAC decoder, transistor simulations and plots' '  make doctor       record installed tool versions'

validate:
	python3 scripts/validate_repo.py

doctor:
	python3 scripts/doctor.py

lint:
	verilator --lint-only -Wall --top-module bringup_counter rtl/bringup/bringup_counter.sv

sim:
	mkdir -p build/sim
	iverilog -g2012 -Wall -s bringup_counter_tb -o build/sim/counter.vvp rtl/bringup/bringup_counter.sv dv/bringup_counter_tb.sv
	vvp build/sim/counter.vvp

synth:
	mkdir -p build/synth
	yosys -Q -T -p 'read_verilog -sv rtl/bringup/bringup_counter.sv; hierarchy -check -top bringup_counter; synth -top bringup_counter; check -assert; stat; write_json build/synth/counter.json' > build/synth/counter.log
	@tail -n 18 build/synth/counter.log

analog-smoke:
	mkdir -p build/analog
	ngspice -b -o build/analog/rc_smoke.log analog/smoke/rc_smoke.cir
	python3 scripts/check_spice_smoke.py build/analog/rc_smoke.log

check: validate lint sim synth analog-smoke doctor

smoke:
	librelane --pdk-root "$(PDK_ROOT)" --pdk sky130A --smoke-test

pnr:
	librelane --pdk-root "$(PDK_ROOT)" --pdk sky130A "$(DESIGN_CONFIG)"

dac-check:
	verilator --lint-only -Wall --top-module dac14_segment_decoder rtl/dac/dac14_segment_decoder.sv
	mkdir -p build/dac14_2g
	iverilog -g2012 -Wall -s dac14_segment_decoder_tb -o build/dac14_2g/decoder.vvp rtl/dac/dac14_segment_decoder.sv dv/dac14_segment_decoder_tb.sv
	vvp build/dac14_2g/decoder.vvp

dac-sim:
	python3 scripts/dac14_sim.py --case all

dac-plots:
	python3 scripts/dac14_plots.py

dac: dac-check dac-sim dac-plots

dac-revision:
	python3 scripts/dac14_minbreak_regression.py
	python3 scripts/dac14_run_revision.py --jobs 1 --threads 2
	python3 scripts/dac14_compare.py

dac-revision-resume:
	python3 scripts/dac14_run_revision.py --resume --jobs 1 --threads 2
	python3 scripts/dac14_compare.py

dac-compare:
	python3 scripts/dac14_compare.py
