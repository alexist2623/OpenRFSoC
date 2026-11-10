# OpenRFSoC development

- Scope: a mixed-signal ASIC prototype with a RISC-V CPU, two target 14-bit-input 2 GSPS DAC channels with about 500 MHz output bandwidth, and an optional approximately 1 GSPS ADC. SKY130 is preferred; final process, dynamic fidelity requirements, ADC resolution and packaging are not fixed.
- Reuse original RTL and permissively licensed open-source IP. Commercial AXI IP purchases are excluded. Preserve upstream license notices and record exact revisions when importing IP.
- Keep FPGA primitives behind replaceable wrappers. Do not import Xilinx generated IP as ASIC implementations.
- Develop and run EDA tools in Linux. Use the pinned environment in `shell.nix` and `env/versions.json`.
- Keep PDKs, tool installations, simulation waveforms and physical-design runs out of Git. Record reproducible commands and reports of relevant measurements.
- Distinguish digital simulation, synthesis, timing closure, analog simulation, extracted-layout simulation, and measured silicon. Passing a digital smoke test is not evidence of 1 GSPS converter operation or tapeout readiness.
- For digital RTL changes, run the relevant simulation and lint checks. For setup changes, validate scripts and report checks that could not run.
- The INQC manuscript is reference material. Work in OpenRFSoC unless the user explicitly requests manuscript changes.
