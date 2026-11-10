# Analog work

The current target is two 14-bit-input, 2 GSPS DAC channels with about 500 MHz
output bandwidth and, if feasible, a 1 GSPS ADC. Required ENOB/SFDR, ADC resolution,
output interface, clock and power budgets remain open. SKY130 is preferred.

The [DAC feasibility prototype](dac14_2g/README.md) contains an editable Xschem
current cell, SKY130 transistor-level simulations, decoder RTL and actual results.
It is a one-channel pre-layout experiment, not a completed 14-bit-accuracy DAC.
The [revision v1 study](dac14_2g/revision-v1.md) fixes the PWL breakpoint issue and
compares smaller steering switches, including remaining glitch trade-offs.

`smoke/rc_smoke.cir` verifies that ngspice runs. It uses ideal components and does not
include foundry transistors, a converter implementation, or 1 GSPS validation.
Select and validate the analog PDK early. SKY130 for the digital smoke test is not
a fabrication-process commitment. IHP SG13G2 remains a candidate.
# GUI 실행과 SKY130 라이브러리

Ubuntu 터미널에서 다음 명령을 실행하면 설치한 PDK revision의 소자 라이브러리를
연결한 Xschem이 WSLg를 통해 Windows 창으로 열린다.

```bash
cd ~/work/OpenRFSoC
bash scripts/xschem.sh
```

처음에는 PDK의 `sky130_tests/top.sch` 예제 모음이 열린다. PDK 캐시의 예제를
직접 수정하지 말고, 자신의 회로도는 `analog/` 아래에 저장한다. 기존 회로도는
`bash scripts/xschem.sh analog/자신의회로.sch`처럼 저장소 기준 경로로 연다.

| 도구 | 용도 |
|---|---|
| Xschem | 소자 회로도와 SPICE netlist 작성 |
| ngspice | DC, AC, transient 등 회로 시뮬레이션 |
| Magic | 레이아웃 작성, 추출과 공정 규칙 검사 |
| KLayout | GDS 확인·편집과 지원되는 공정 규칙 검사 |
| Netgen | 추출 회로와 원래 netlist의 LVS 비교 |

별도 Ubuntu 데스크톱, VNC, 외부 X server 설치는 필요하지 않다.
[Microsoft WSLg 안내](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)를 참고한다.
GUI 실행과 PDK 연결, DAC 초기 회로의 공정 소자 시뮬레이션까지 확인했다.
DAC 레이아웃 및 추출 후 검증은 아직 수행하지 않았다.

아날로그 회로는 회로도 → SPICE 검증 → 레이아웃 → DRC/LVS → 기생성분 추출 후
재시뮬레이션으로 진행한다. 디지털의 `make pnr`이 ADC·DAC 아날로그 회로를
자동 설계하는 것은 아니다. 완성한 아날로그 블록은 GDS/LEF 등 macro
인터페이스와 모델을 갖춰 디지털 top-level에 통합한다.
