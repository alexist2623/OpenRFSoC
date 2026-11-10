# Verilog에서 SKY130 GDS까지

이 문서는 이 저장소의 고정된 LibreLane 3.0.9 환경과 `sky130A`를 사용한다.
이미 설치된 도구와 PDK를 재사용한다. 실제 실행 결과는
[설치 상태](setup-status.md)에 기록한다.

## 1. Linux 작업 폴더와 도구 환경 열기

Ubuntu 터미널에서 실행한다.

```bash
cd ~/work/OpenRFSoC
bash scripts/eda.sh
```

이후 명령은 이 터미널 안에서 실행한다. 종료는 `exit`이다. PowerShell에서
시작할 경우 먼저 `wsl -d Ubuntu-24.04`로 Ubuntu에 들어간다.

실제 저장소는 `/home/alexist/work/OpenRFSoC`이다. Windows 탐색기에서는
`\\wsl.localhost\Ubuntu-24.04\home\alexist\work\OpenRFSoC`로 접근할 수 있다.
VS Code는 WSL 확장으로 이 Linux 폴더를 열어 편집한다.
`C:\JeonghyunPark\Workspace\OpenRFSoC`는 별도 checkout이며 자동 동기화되지 않는다.

## 2. 현재 카운터 예제로 전체 흐름 익히기

```bash
make check
make pnr
```

`make check`는 현재 **bringup_counter 예제**의 lint, 기능 시뮬레이션, generic
합성과 별도 RC SPICE 점검을 수행한다. `make pnr`은 다음 설정을 사용한다.

- RTL: `rtl/bringup/bringup_counter.sv`
- 테스트벤치: `dv/bringup_counter_tb.sv`
- 물리 구현 설정: `physical/sky130/bringup_counter/config.json`
- 최상위 모듈: `bringup_counter`
- 클록: `clk`, 주기 20 ns = 50 MHz
- 예제 die 크기: 120 × 120 µm

다시 실행하면 `physical/sky130/bringup_counter/runs/RUN_.../` 아래에
실행별 결과가 생긴다. 기존 결과를 소스처럼 편집하지 않는다.

```text
Verilog RTL + 테스트벤치 → 기능 검증
Verilog RTL + PDK + 타이밍 제약 → 표준셀 합성 → 배치 → 클록 트리 → 배선
    → 기생성분 추출·타이밍 분석 → DRC·LVS 등 검증 → GDSII
```

PDK는 공정의 배선층·설계 규칙·소자 정보를 제공하고, 표준셀 라이브러리는
플립플롭·논리 게이트의 회로·면적·지연·레이아웃을 제공한다.
Verilog의 `always @(posedge clk)` 같은 기술을 Yosys가 이 셀들로 합성하고,
OpenROAD가 배치배선한다. LibreLane은 이 과정과 검증 도구를 연결한다.

`make smoke`는 도구 설치 확인용 공식 예제다. 매번 RTL을 수정할 때마다
실행할 필요는 없다. 자신의 RTL은 해당 테스트벤치와 `make pnr`로 검증한다.

## 3. 자신의 RTL 추가하기

예를 들어 `my_top`을 만들려면 다음 디렉터리를 사용한다.

```bash
mkdir -p rtl/my_top physical/sky130/my_top
```

`rtl/my_top/my_top.v`에 합성 가능한 RTL을 작성한다. 아래 코드는 시작용
8비트 카운터이며, 기존 예제와 같은 구조다.

```verilog
`default_nettype none
module my_top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n)
            count <= 8'd0;
        else if (enable)
            count <= count + 8'd1;
    end
endmodule
`default_nettype wire
```

상위 모듈이 사용하는 하위 모듈의 RTL도 함께 준비한다. `#10`, `$display`,
클록을 만드는 `initial` 블록 등 시뮬레이션용 코드는 테스트벤치에 둔다.
FPGA의 전원 투입 초기값을 전제로 하지 말고 필요한 초기 상태는 reset으로
정의한다. 조합 논리에서는 모든 분기의 출력을 할당하여 의도하지 않은 latch를
피한다. Xilinx primitive/IP는 이 공정의 구현으로 자동 변환되지 않는다.

## 4. 자신의 테스트벤치로 기능 검증하기

`dv/my_top_tb.sv`를 작성한다. 최소한 reset, 정상 동작, enable 정지, 경계값을
검사하고, 틀린 결과는 `$fatal`로 실패하게 한다. 새 블록에는 그 블록의 기능에
맞는 검사 항목이 필요하다. 기존 테스트벤치 구조를 참고할 수 있다.

```bash
verilator --lint-only -Wall --top-module my_top rtl/my_top/my_top.v
mkdir -p build/my_top
iverilog -g2012 -Wall -s my_top_tb -o build/my_top/test.vvp \
  rtl/my_top/my_top.v dv/my_top_tb.sv
vvp build/my_top/test.vvp
```

하위 모듈이 있으면 위 명령에도 필요한 소스 파일을 추가한다. 프로젝트의 기본
`make check`는 새 블록을 자동으로 찾아 테스트하지 않는다. 반복 개발할 블록은
해당 lint·시뮬레이션 명령을 Makefile에 별도 target으로 등록한다.

## 5. 물리 구현 설정 연결하기

`physical/sky130/my_top/config.json`을 아래처럼 만든다. 작은 시작용 블록에는
검증된 카운터의 floorplan과 전원망 값을 출발점으로 사용할 수 있다.
회로가 커지면 die 면적과 배치 밀도, 전원망을 다시 잡아야 한다.

```json
{
  "DESIGN_NAME": "my_top",
  "VERILOG_FILES": ["dir::../../../rtl/my_top/my_top.v"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 20.0,
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 120, 120],
  "FP_CORE_UTIL": 30,
  "PL_TARGET_DENSITY_PCT": 35,
  "PDN_VOFFSET": 5,
  "PDN_HOFFSET": 5,
  "PDN_VWIDTH": 2,
  "PDN_HWIDTH": 2,
  "PDN_VPITCH": 30,
  "PDN_HPITCH": 30
}
```

`DESIGN_NAME`은 RTL의 최상위 `module` 이름과 정확히 같아야 한다.
`VERILOG_FILES`에는 구현에 필요한 RTL만 넣고 테스트벤치는 넣지 않는다.
`dir::`는 config 파일이 있는 디렉터리를 기준으로 경로를 해석한다.
여러 소스 파일은 배열에 추가한다.

`CLOCK_PERIOD`의 단위는 ns이며, 주파수 MHz는 `1000 / 주기(ns)`이다.
값을 줄이는 것만으로 고속 동작이 보장되지는 않는다. 이 예제는 기본 SDC를
사용하므로, 실제 시스템의 입출력 지연·부하·외부 클록 관계를 반영하려면
`PNR_SDC_FILE`과 `SIGNOFF_SDC_FILE` 등의 제약을 설계에 맞게 작성해야 한다.
멀티 클록과 CDC는 별도의 설계·검증 대상이다.

설정 파일의 의미는 [LibreLane 공식 configuration 설명](https://librelane.readthedocs.io/en/stable/reference/configuration.html)을 참고한다.

## 6. 자신의 GDS 생성하기

```bash
make pnr DESIGN_CONFIG=physical/sky130/my_top/config.json
```

오류가 나면 마지막 실패 단계의 로그를 확인하고 RTL 또는 설정을 수정한다.
DRC·LVS·타이밍 checker를 끄는 방식으로 통과시키지 않는다.
이 명령에는 해당 RTL의 기능 테스트벤치 실행이 포함되지 않으므로 4단계를 먼저
통과해야 한다.

실행 결과는 `physical/sky130/my_top/runs/RUN_.../`에 보관된다. GDS가 있는지
찾으려면 다음 명령을 사용한다.

```bash
find physical/sky130/my_top/runs -path '*/final/gds/*.gds' -type f
```

카운터를 실행했다면 경로의 `my_top`을 `bringup_counter`로 바꾼다.
찾은 실제 경로를 사용해 Nix 환경의 KLayout에서 연다.

```bash
klayout physical/sky130/my_top/runs/RUN_실제실행태그/final/gds/my_top.gds
```

Windows 파일 연결 프로그램으로 열기보다는 위 명령으로 WSLg의 KLayout을
실행하면 설치한 환경을 그대로 사용한다.

## 7. 성공 여부 판단하기

GDS 파일의 존재와 실행 성공을 구분한다. 실패한 실행도 중간 GDS를 남길 수 있다.
터미널의 완료 메시지와 종료 코드, 실행 폴더의 `error.log`, `warning.log`,
`final/metrics.json`, 단계별 보고서를 함께 확인한다.

- DRC: 실행한 규칙 검사에서 위반이 없는지.
- LVS: 레이아웃에서 추출한 회로와 합성 netlist가 일치하는지.
- 타이밍: 설정한 corner와 I/O 제약 아래 setup/hold 위반이 없는지.
- Antenna 등: 해당 흐름이 실행한 나머지 checker 결과.
- 경고: 전원 공급 위치, 지원하지 않는 규칙, 검사 생략 등을 이해했는지.

현재 결과는 작은 디지털 블록의 GDS다. 실제 MPW 제출에는 셔틀의 top-level
규격, pad/ESD, 전원·클록, SRAM/analog macro, DFT·테스트 구조, 패키지와
제출용 signoff를 별도로 갖춰야 한다. DAC·ADC의 아날로그 회로가 디지털 RTL에서
자동 생성되지는 않는다. 1 GSPS 동작은 별도 회로 설계와 검증이 필요하다.

전체 흐름의 배경은 [LibreLane 공식 입문 예제](https://librelane.readthedocs.io/en/stable/getting_started/newcomers/index.html)에 설명되어 있다.
