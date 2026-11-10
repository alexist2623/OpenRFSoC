# DAC revision v1 — 수렴 오류 수정과 글리치 비교

이 문서는 2026-11-09의 후속 설계 기록이다. [초기 회로](README.md)의 수렴 문제를
수정하고, 전류원 배열을 유지하면서 steering switch를 작게 만든 안을 비교한다.
레이아웃 전 한 채널 연구 회로이며 14-bit 동적 정확도나 제작 준비 완료를 뜻하지 않는다.

## 수렴 오류 수정

동일 시각에 여러 PWL 신호가 전환될 때 ngspice가 매우 가까운 breakpoint를
서로 다르게 처리하는 문제가 있었다. 공식 버그 보고의 조건을 작은 RC 회로로
재현했다. 기존 `tran` 명령과 `minbreak` 옵션만 추가한 `tran` 명령은 중단됐고,
`.tran` 분석 지시문을 선언한 뒤 `run`으로 실행한 경우는 완료됐다.
[ngspice 공식 버그 #887](https://sourceforge.net/p/ngspice/bugs/887/)

`scripts/dac14_sim.py`에서 `minbreak=1e-15`와 `.tran`/`run`을 사용한다.
1 fs 이내의 사실상 같은 전환 시각을 묶는 설정이다. 전류·전압 허용오차를
느슨하게 하거나 신호의 20 ps 전환 시간을 바꿔 통과시킨 것이 아니다.
설치된 ngspice 44와 고정된 PDK를 유지했다.

초기 회로의 499.023 MHz 전체 파형은 최대 시간 간격 2.5 ps와 1.25 ps에서
모두 완료됐고 SFDR은 44.557/44.578 dBc였다. 세부 결과는
`build/dac14_revision/minbreak_regression/`와 `comparison.json`에 있다.
이 확인은 해당 테스트의 적분 간격 민감도 검사이며 모든 회로·조건의 수렴 보장은 아니다.

v1도 같은 두 간격에서 전체 해석을 완료했으며 SFDR은 50.864/50.852 dBc였다.
전·후 모두 간격을 반으로 줄였을 때 SFDR 변화는 0.022 dB 이내였다.

## 회로 변경

| 항목 | 초기 회로 | Revision v1 |
|---|---|---|
| 분할·입력 | 5+9, 14-bit, 2 GSPS | 동일 |
| 전류원·하단 cascode | WGT개 병렬 소자 | 동일 |
| 큰 MSB 뱅크의 스위치 | 0.42 µm 소자 512개 병렬 | 폭 1.12 µm 소자 한 개 |
| 스위치 길이 | 0.15 µm | 동일 |
| cascode bias | 1.05 V | 0.9 V |
| 논리 입력 | 이상적 0~1.8 V, 20 ps edge | 동일 |
| 출력 부하 | 각 출력 50 Ω, 200 fF | 동일, 필터 추가 없음 |

새 스위치 폭은 `max(0.42, 0.42 × WGT / 192)` µm이다. WGT=512에서
1.12 µm, WGT=256에서 0.56 µm, 작은 가중치에서는 최소 폭 0.42 µm를 사용한다.
소수 배수의 최소 소자를 물리 소자로 간주하지 않고 실제 W/L과 접합 면적·둘레를
SPICE에 전달한다. 전류원 매칭을 위한 배열 면적을 192분의 1로 줄인 것은 아니다.

출력에 직접 연결된 큰 스위치의 기생성분을 줄이는 것이 목적이다.
더 작은 스위치로 SFDR만 높인 일부 후보는 전류원 전압 여유가 부족하여
코드 역전이 생겼으므로 채택하지 않았다. 이 결과는 `explore_*` 폴더에 남겼다.
물리적인 작은 전압 폭의 구동기와 추가 출력 cascode 후보도 비교했으나
현재 선택한 회로에는 포함하지 않았다.

## 비교 조건과 해석

주 비교는 TT/27°C/1.8 V, 2 GSPS, 499.0234375 MHz, 동일한 90% full-scale
입력 코드열이다. 128 sample 후 2,048 sample 구간을 사용하고, 연속시간
출력을 128 GS/s로 재샘플링해 FFT를 계산한다. 전·후 모두 최대 SPICE 간격은
2.5 ps이며, 각각 1.25 ps로 추가 확인한다. 그래프의 전압 파형은 크기를
맞추기 위해 인위적으로 확대·축소하지 않는다.

| TT/499.023 MHz 지표 | 초기 회로 | v1 |
|---|---:|---:|
| SFDR, 0~1 GHz | 44.557 dBc | 50.864 dBc |
| SFDR, 0~500 MHz | 59.509 dBc | 58.600 dBc |
| 기본파 peak | 0.4105 V | 0.3686 V |
| 각 출력의 최대 전압 | 약 2.124 V | 약 1.797 V |

0~1 GHz에서는 개선됐지만 **사용자 목표 대역 0~500 MHz의 SFDR은 약 0.91 dB
악화**됐다. 가장 큰 스퍼가 502.93 MHz에 있어 분석 대역에 따라 결론이 달라진다.
따라서 v1을 전체적인 성능 개선이나 최종 채택안으로 확정하지 않는다.

전·후의 10 mA는 기준 전류의 설계 목표다. 실제 nominal DC span은
0.9489 → 0.9156 Vpp로 약 3.5% 감소했다. 따라서 글리치 개선을 판단할 때
원래 전압과 각 회로의 step 크기로 정규화한 그래프를 함께 본다.

큰 전환 `8192 → 12288`에서는 endpoint 범위를 넘는 overshoot가
약 307.68 → 1.67 mV로 줄었다. 500 ps 동안의 절대 추종 오차 적분을
step 크기로 나눈 값도 약 511.1 → 34.7 ps로 줄었다.

**작은 major-carry 전환 `8191 → 8192`에서는 악화가 있다.** Overshoot는
약 0.075 → 6.02 mV, 절대 추종 오차 면적은 0.0295 → 0.1457 V·ps다.
이 회로를 모든 코드에서 글리치가 개선된 DAC라고 해석하면 안 된다.
다음 과제는 MSB/binary 경계의 동적 매칭과 전하 주입·전환 시점의 균형이다.

Step 시험은 전환 후 500 ps를 관찰한다. Endpoint 기준은 전환 전후 코드를
각각 3.9 ns 유지한 시점의 출력으로 잡는다. 절대 오차 적분에는 정착 과정도
포함되며 순수한 glitch impulse energy로 표시하지 않는다. 별도의 전체 DC
sweep으로 INL/DNL과 단조성을 평가한다.

TT nominal DC 검사에서 v1은 16,384개 코드가 단조이며 endpoint INL 최대
약 0.426 LSB, DNL 최대 약 0.669 LSB다. 이 결과도 완벽히 매칭된 모델의
값으로, mismatch와 수율을 검증한 값은 아니다.

정확한 긴 파형 수치, 시간 간격 검사, 공정·온도 결과는 자동 생성되는
`build/dac14_revision/comparison.json`을 기준으로 한다. 추가 SS/85°C와
FF/−40°C의 transient 검사는 512 sample, 496.09375 MHz를 사용한다.
전원은 모두 1.8 V로 같으며 전체 PVT sweep이 아니다.

**SS/85°C에서 단조성이 깨졌다.** Endpoint INL 최대 약 6.20 LSB,
최소 DNL 약 −7.92 LSB였다. FF/−40°C에서는 단조이며 INL 약 0.357 LSB,
최대 절대 DNL 약 0.390 LSB였다. 높은 SFDR만으로 공정 변화에 견디는
14-bit DAC라고 판단할 수 없다는 결과다. v1은 실험안으로 보존하고,
전류원의 전압 여유와 MSB/LSB 동적 매칭을 다음 설계에서 개선해야 한다.

## 실행

Ubuntu에서 회로도를 연다. 표시된 WGT=512는 한 MSB 뱅크 예다.

```bash
cd /home/alexist/work/OpenRFSoC
bash scripts/xschem.sh analog/dac14_2g/current_cell_shared.sch
```

전체 비교를 처음부터 재현하거나, 결과가 이미 있을 때 그림만 생성한다.

```bash
cd /home/alexist/work/OpenRFSoC
bash scripts/eda.sh
make dac-revision
# 이미 완료한 결과로 그림만 다시 만들기:
make dac-compare
```

전체 재실행에는 여러 긴 SPICE 해석이 포함된다. 기본값은 동시 작업 1개,
ngspice 스레드 2개다. 같은 회로 소스로 실행하다 중단된 경우:

```bash
make dac-revision-resume
```

완료된 JSON과 조건이 일치하는 결과만 재사용한다. 회로 소스를 변경한 뒤에는
재개 기능을 사용하지 말고 새로 실행한다. `run_status.json`에 재사용 여부를 기록한다.

| 파일 | 용도 |
|---|---|
| `current_cell_shared.spice` | 실제 v1 SPICE 셀 |
| `current_cell_shared.sch` | 편집 가능한 Xschem 회로도 |
| `revision_v1.json` | 실험안의 조건, 변경 사항 |
| `scripts/dac14_minbreak_regression.py` | PDK와 무관한 breakpoint 회귀 검사 |
| `scripts/dac14_run_revision.py` | 비교 실행과 중단 후 재개 |
| `scripts/dac14_step.py` | 큰 step과 major-carry 시험 |
| `scripts/dac14_compare.py` | 비교 JSON 및 그래프 생성 |

회로도와 SPICE 셀은 별도 소스이므로 소자를 바꿀 때 함께 수정한다.
`make dac`은 초기 회로, `make dac-revision`은 전·후 비교를 실행한다.
`make pnr`은 기존 디지털 counter GDS용이며 이 아날로그 DAC의 GDS를 만들지 않는다.

## 현재 한계

실제 clock tree/retiming, bias generator, 소자 mismatch, 열잡음, 레이아웃 기생성분,
pad/ESD·패키지는 아직 포함하지 않았다. 단조성·스펙트럼·정착 시간·글리치는
서로 다른 지표이며 하나의 개선으로 14-bit 유효 분해능을 주장하지 않는다.
공정·온도별 코드 역전이나 성능 악화가 있으면 해당 결과도 보고서에 그대로 기록한다.

## TSMC PDK 접근

TSMC PDK는 공개 다운로드 자료가 아니다. EUROPRACTICE는 회사·연구기관의
TSMC 승인 후 3자 NDA 절차를 안내하고, 대학에는 65/40 nm 등의 신청 경로를
제공한다. 신청 자체가 자동 승인을 뜻하지 않는다.
[EUROPRACTICE 공식 접근 안내](https://europractice-ic.com/technologies/asics/tsmc/access-contacts/)

PDK 파일 자체가 항상 별도의 유료 상품이라고 단정할 수는 없다. 기관 계약과
접근 권한, EDA 라이선스, MPW 제작 비용을 구분해야 한다. 특정 공정·기관의
비용은 해당 제공 경로에서 확인해야 한다. 북미 대학의 FinFET 프로그램 역시
신청 심사와 TSMC 승인, NDA 후 접근하는 절차다.
[imec 북미 대학 프로그램](https://www.imeciclink.com/en/tsmc-university-finfet-program/north-america)

## 작업 중 Windows 비정상 종료

재부팅 후 System 로그에 41/6008이 있었고 BugcheckCode와 PowerButtonTimestamp는
0이었다. 확인한 구간에 1074 정상 종료 요청 기록은 없었다. WHEA 이벤트 3은
정보 수준이었으며, 이 기록만으로 전원·온도·시스템 멈춤 중 원인을 확정하지 않았다.
[Microsoft 이벤트 41 설명](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/event-id-41-restart)

완료된 파일을 보존하고 중단된 해석만 재개했다. 재개 후 실행 부하는 동시 작업
1개/스레드 2개로 줄였다. 컴퓨터의 전원·클럭·BIOS 설정은 변경하지 않았다.
