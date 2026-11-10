# SKY130 DAC 초기 설계: 14-bit 입력, 2 GSPS, 출력 대역 목표 500 MHz

후속 작업에서 수렴 오류를 수정하고 스위치를 변경한 비교 실험을 진행했다.
최신 결과와 실행 방법은 [revision v1 기록](revision-v1.md)을 참고한다.
아래의 수렴 실패와 성능 수치는 초기 설계 당시의 기록이다.

2026-11-09에 작성하고 설치된 SKY130A/ngspice 환경에서 실행한 **한 채널의
레이아웃 전 타당성 검토 회로**다. 시스템 목표는 두 채널이다.
14-bit 코드를 받아 전류를 전환하는 회로와 기능 검증용 RTL을 구현했다.
14-bit 유효 분해능, 실제 2 GHz 디지털 타이밍, 제작 가능한 DAC의 완성을 뜻하지 않는다.

## 바로 실행하기

PowerShell에서 Ubuntu에 진입한다.

```powershell
wsl -d Ubuntu-24.04
```

Ubuntu에서 편집 가능한 전류 셀 회로도를 연다. 별도 Linux 데스크톱은 필요 없다.

```bash
cd ~/work/OpenRFSoC
bash scripts/xschem.sh analog/dac14_2g/current_cell.sch
```

전체 배열의 시뮬레이션은 다른 Ubuntu 터미널에서 실행한다.

```bash
cd ~/work/OpenRFSoC
bash scripts/eda.sh
make dac
```

`make dac`은 디코더 lint와 16,384개 코드 검사, DC sweep, 네 개 transient
조건, 그래프 생성을 순서대로 수행한다. 실행 시간은 수 분 이상 걸릴 수 있다.
회로도는 셀의 편집·확인용이며 부하와 자극원을 포함하지 않는다.
Xschem의 Simulate 버튼만으로 전체 DAC 테스트가 실행되지는 않는다.

| 명령 | 수행 내용 |
|---|---|
| `make dac-check` | RTL lint 및 모든 입력 코드에 대한 기능 검사 |
| `make dac-sim` | 공정 소자를 사용한 DC 및 transient 시뮬레이션 |
| `make dac-plots` | 이미 생성된 결과로 그림 생성 |
| `python3 scripts/dac14_numerics.py` | FFT 재샘플링 간격에 대한 민감도 확인 |
| `python3 scripts/dac14_drive_experiment.py` | 별도 폴더에서 작은 게이트 전압 스윙 실험 |

작업 원본은 `/home/alexist/work/OpenRFSoC`다. Windows 탐색기에서는
`\\wsl.localhost\Ubuntu-24.04\home\alexist\work\OpenRFSoC`로 접근한다.
Windows의 `C:\JeonghyunPark\Workspace\OpenRFSoC`와 자동으로 동기화되지 않는다.

## 설계 구조

5+9 분할 방식의 차동 current-steering DAC다.

- 상위 5비트: 각 512 단위 전류인 31개 thermometer/unary 뱅크.
- 하위 9비트: 1, 2, 4, …, 256 단위 전류인 9개 binary 뱅크.
- 합계: `31 × 512 + 511 = 16,383` 단위. 입력 코드는 0~16,383.
- 각 뱅크는 NMOS 전류원, cascode, 두 개의 차동 steering 스위치로 구성된다.
- `WGT`는 동일한 소자의 병렬 배수를 뜻한다. 실제 배치된 16,383개 셀을
  개별적으로 시뮬레이션한 것은 아니며, 뱅크별 매칭·배선 차이는 반영하지 않았다.

| 설정 | 현재 값 |
|---|---|
| 공정 소자 | `sky130_fd_pr__nfet_01v8` |
| 전원 | 1.8 V |
| 샘플 주기 | 500 ps, 즉 2 GSPS |
| 총 전류 목표 | 10 mA, 단위 전류 약 0.6104 µA |
| 부하 | 출력마다 **VDD로 연결한** 50 Ω, 접지로 연결한 200 fF |
| cascode bias | 이상적 1.05 V 전압원 |
| 스위치 제어 | 이상적 0~1.8 V 상보 신호, 전환 시간 20 ps |
| 전류원 / cascode / switch W/L | 1/1, 1/0.3, 0.42/0.15 µm |

두 출력의 차는 `OUTN - OUTP`로 정의했다. 코드가 증가하면 OUTP로 흐르는
sink 전류가 증가하므로 이 부호를 사용한다. 목표 차동 span은 1 Vpp지만
실제 nominal DC 시뮬레이션은 약 0.9489 Vpp다. 전류 미러의 동작점 차이 등으로
목표 전류와 실제 전류가 다르다. 10 mA를 실제 달성값이나 전체 소비전력으로
해석하면 안 된다. 현재 gate driver와 clock 회로의 전력은 포함되어 있지 않다.

`rtl/dac/dac14_segment_decoder.sv`는 등록된 디코더다. SPICE 테스트는 같은
코드 분할을 Python으로 생성한 이상적 제어 신호를 사용한다. RTL 표준셀의 지연을
SPICE와 연동한 mixed-signal 검증은 아니다. RTL 테스트벤치의 2 GHz clock은
기능 검사 자극일 뿐, SKY130 표준셀에서 2 GHz timing closure의 증거가 아니다.

## 실제 결과와 해석

`results.png` 왼쪽 위 그래프의 회색 선은 이상적 zero-order hold 출력이다.
2 GSPS에서는 0.5 ns마다 값이 바뀌고 그 사이에는 유지한다. 약 499 MHz 파형은
한 주기가 약 2 ns이므로 주기당 약 네 개의 sample이 보인다. 출력 필터를
거치기 전이어서 이상적인 경우에도 계단 모양이다.

파란 선은 SKY130 트랜지스터 시뮬레이션의 출력이다. 전환 순간 크게 튀는
부분은 스위칭 글리치이며, 소자의 기생용량과 내부 전류 전환의 영향으로
보인다. 정확한 원인별 기여도와 크기는 수치 수렴 문제를 해결한 뒤 검증해야 한다.
세로축은 두 출력의 차이 `OUTN - OUTP`다. 음수 값은 음전원을 뜻하지 않는다.
이 그림은 출력 필터를 거친 깨끗한 sine이나 실제 칩에서 측정한 파형이 아니다.

SKY130A revision `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`, ngspice 44.
모든 조건은 1.8 V다. SS/FF 및 온도를 조합한 세 조건이며 전체 PVT sweep은 아니다.

| 출력 주파수 | 공정 / 온도 | SFDR, 0~1 GHz 대역 |
|---|---|---:|
| 100.5859375 MHz | TT / 27°C | 51.81 dBc |
| 499.0234375 MHz | TT / 27°C | 44.56 dBc |
| 499.0234375 MHz | SS / 85°C | 45.65 dBc |
| 499.0234375 MHz | FF / −40°C | 43.02 dBc |

입력 sine은 full scale의 90% 진폭이다. 128 sample을 기다린 뒤 2,048 sample
구간을 사용하며, FFT에 맞는 주파수 bin 103 및 511을 선택했다. 연속시간
출력을 128 GS/s로 재샘플링해 첫 Nyquist 대역의 SFDR을 계산한다.
따라서 결과는 정확히 500 MHz인 한 점이나 0~500 MHz 전체 sweep 결과가 아니다.

TT 499.023 MHz 조건의 가장 큰 스퍼는 **502.930 MHz**다. 측정 대역을
0~500 MHz로 좁히면 SFDR은 약 **59.6 dBc**로 계산된다. 위 표의 44.6 dBc는
0~1 GHz를 포함한 값이다. 대역 경계에서 바로 옆에 있는 스퍼를 제외했기 때문에
달라지는 것이며, 실제 출력 필터가 이 스퍼를 제거했다는 의미가 아니다.
필터·패키지까지 포함한 시스템 성능은 별도 검증이 필요하다.

TT DC endpoint INL은 최대 약 0.0173 LSB, DNL은 약 0.0000167 LSB이며 단조다.
이 수치는 **동일한 nominal 소자를 완벽하게 매칭한 모델**의 결과다.
공정 mismatch, 기울기, 잡음이 없으므로 14-bit 정확도나 수율의 증거로 쓰면 안 된다.
동적 결과 역시 SFDR이며 ENOB가 아니다. thermal noise를 포함한 SNR/ENOB 검증은 없다.

499 MHz TT 파형에서 각 출력이 약 1.066~2.125 V까지 변한다. 1.8 V 전원을
넘는 순간적인 overshoot가 있으므로 출력단과 구동 회로를 개선하고 소자별
VGS/VDS/VGD 및 신뢰성을 확인해야 한다. 출력 노드 전압만으로 소자의 모든
단자 간 전압을 판정한 것은 아니다.

0.8~1.6 V로 이상적 게이트 스윙을 줄인 별도 실험의 SFDR은 42.70 dBc로
오히려 나빠졌다. 이 설정은 기본 설계에 채택하지 않았다.

최초 behavioral 상보 구동원 실행의 FFT 재샘플링을 128/256/512 GS/s로
바꿨을 때 SFDR은 각각 44.578/44.601/44.598 dBc였다. 동일 파형을 PWL 쌍으로
직접 지정한 현재 기본 실행도 5 ps에서 약 44.6 dBc로 일치한다.
최종 파형의 FFT 격자 검사와 스퍼 주파수는 `build/dac14_2g/numerics.json`에 있다.

초기 실행에서는 **SPICE 적분 간격 수렴 검증을 통과하지 못했다.** Behavioral 구동의
2.5 ps와 2 ps 실행은 각각 약 0.9545 µs와 0.4785 µs에서 `Timestep too small`로
중단됐다. Gear 적분, 직접 PWL 상보 구동, transient 반복 한도 100으로 바꾼
추가 2.5 ps 실행도 중단됐다. 실패한 실행은 성능 표에 사용하지 않았다.
따라서 위 수치는 회로 개선 방향을 보는 **잠정적인 시뮬레이션 결과**이며,
당시 수치적으로 충분히 수렴했다고 판정한 결과는 아니었다. 후속 수정본에서는
`.tran`/`run` 및 `minbreak` 설정으로 해당 문제를 해결했다. 초기 실패 로그는
`build/dac14_2g/convergence*/`에 보존했다.

## 파일과 수정 방법

| 파일 | 역할 |
|---|---|
| `current_cell.sch` | Xschem에서 편집 가능한 4-MOS 셀 |
| `current_cell.spice` | 전체 배열 테스트에서 실제 사용하는 셀 netlist |
| `spec.json` | 테스트 조건 및 구조·소자 치수 기록 |
| `../../rtl/dac/dac14_segment_decoder.sv` | 합성 가능한 디코더 RTL |
| `../../scripts/dac14_sim.py` | 40개 뱅크의 SPICE 테스트벤치 생성·실행·분석 |
| `../../scripts/dac14_plots.py` | 구조도 및 실제 결과 그림 생성 |
| `../../build/dac14_2g/` | 생성한 `.cir`, `.log`, `.dat`, `.npz`, 결과 JSON과 그림 |

**현재 회로도와 SPICE 셀은 별도 소스**다. 회로를 변경하면 두 파일을 함께
수정해야 한다. `spec.json`의 W/L은 기록용이며 이것만 바꿔도 MOS 치수가
자동 변경되는 구조는 아니다. 14-bit/5+9 분할도 고정 구현이다. 소자 크기,
분할 방식 변경 시 RTL, generator, 회로 소스와 테스트를 함께 수정한다.
부하, bias, 샘플링 속도, 제어 전압 등 테스트 조건은 generator가 JSON에서 읽는다.

간격·적분 방법 비교는 기존 결과를 덮어쓰지 않는 별도 경로로 실행한다.
다음은 위 수렴 실패를 재현하기 위한 명령이며 정상 완료 예제가 아니다.

```bash
python3 scripts/dac14_sim.py --case high-tone --method gear --max-step-ps 2.5 \
  --output-dir build/dac14_2g/convergence_gear
```

새 회로를 그린 다음의 순서는 소자 시뮬레이션 → layout → DRC/LVS → 기생성분
추출 → 추출 회로 재시뮬레이션이다. **`make pnr`은 기존 counter의 디지털
GDS를 만들며 이 DAC의 아날로그 GDS를 만드는 명령이 아니다.** DAC GDS는 아직 없다.

## 공정 선택과 다음 설계

TSMC 45 nm는 130 nm보다 미세한 공정이다. 공정 숫자만으로 DAC 정확도를
결정할 수는 없지만, 고속 스위칭·디지털 구동과 아날로그 headroom의 조건이 달라진다.
실제 TSMC 65 nm의 14-bit/2 GS/s 연구는 5+9 분할을 사용했고, 240 MHz 출력에서
측정 SFDR이 보정 전 63.8 dBc, predistortion 후 70 dBc였다. 이는 500 MHz에서의
70 dBc나 14 ENOB 달성을 뜻하지 않는다.
[Chang 등의 2018년 논문](https://www.jstage.jst.go.jp/article/elex/15/13/15_15.20180509/_article/-char/en)

0.13 µm에서도 14-bit DAC 실측 사례는 있지만 이 예는 250 MS/s이며 SKY130과
동일한 공정이라고 볼 수 없다. 여기서 SKY130 2 GSPS 성능을 추론하면 안 된다.
[Li 등의 2013년 논문](https://www.jos.ac.cn/article/doi/10.1088/1674-4926/34/8/085013)

현재처럼 공개 PDK와 무료 도구로 회로를 직접 익히고 검증하는 출발점으로는
SKY130을 유지하는 것이 합리적이다. 2 GSPS·500 MHz에서 높은 동적 정밀도가
필수라면, 학교나 연구기관을 통해 PDK/MPW 접근이 가능한 65/40 nm급 mixed-signal
공정도 성능·비용·도구 조건과 함께 비교하는 것을 권한다. 이는 설계 판단이며
공정 변경만으로 성능이 보장되지는 않는다. 아날로그 회로는 새 PDK로 재설계해야 한다.
[TSMC CyberShuttle](https://www.cld.tsmc.com/english/dedicatedFoundry/services/cyberShuttle)

다음 설계 우선순위는 실제 retiming/driver와 출력단 개선, 바이어스·기준전류
회로, mismatch/gradient에 맞춘 셀 크기와 배치, calibration, clock jitter,
추출 기생성분을 포함한 검증이다. 현재의 전압 overshoot와 수치 수렴 문제를
먼저 해소해야 한다. 이후 실제 요구 SFDR/ENOB와 전력·면적 예산으로 공정의
진행 여부를 판단한다. 두 채널을 동시에 동작시키는 전원/클럭 간섭도 검증 대상이다.

14-bit × 2 GSPS × 2채널은 순수 sample payload만 56 Gbit/s다. 일반 저속
GPIO로 모든 샘플을 공급하는 구조가 아니라, 칩 내부 파형 메모리/NCO와 병렬
데이터 경로부터 설계해야 한다. 16-bit 저장 포맷이면 두 채널 메모리 읽기는
8 GB/s다. 이 데이터 경로와 선택적인 1 GSPS ADC는 아직 구현하지 않았다.

## 패키징과 본드 패드

SkyWater는 패키징 서비스를 제공하지만 모든 SKY130 MPW에 자동 포함된다고
볼 수 없다. 선택한 shuttle/중개업체 계약의 bare die, 패키지, 조립·검사 범위를
확인해야 한다. [SkyWater 서비스](https://www.skywatertechnology.com/services/)

2026-11-09에 확인한 chipIgnite 안내에는 표준 I/O ring과 **100개 QFN 패키지
또는 bare die 선택**이 있다. 이런 서비스를 사용하면 지정된 pad ring/harness에
맞춰 통합한다. 독립 die를 제작하면 자체 pad/ESD ring과 bond map, 전원·접지
배치를 설계해야 한다. [chipIgnite 공식 안내](https://chipfoundry.io/chipignite)

패키징 포함 여부와 500 MHz 아날로그 경로의 적합성은 별개다. pad/ESD, bond wire,
패키지와 보드의 기생성분을 모델에 넣어 검증해야 한다. 현재 셀의 OUTP/OUTN
라벨은 신호 포트이며 실제 bond pad가 아니다. pad ring, 패키지 및 DAC layout은
이 초기 설계에 포함되어 있지 않다.
