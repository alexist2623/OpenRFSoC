# 설치와 실행 검증 상태 — 2026-11-09

## 확인 완료

- WSL 2.7.14.0, Ubuntu 24.04 LTS, WSL2 실행 확인.
- 실제 개발 checkout: `/home/alexist/work/OpenRFSoC`.
- `make check`: RTL lint·기능 시뮬레이션·generic 합성, 이상적 RC SPICE 검사, 도구 확인 통과.
- LibreLane 3.0.9와 SKY130A PDK 설치, `make smoke` 통과.
- `make pnr` 종료 코드 0, `Flow complete`, 카운터 GDS 생성.
- KLayout Python API로 최종 GDS를 다시 읽어 top cell과 크기 확인.
- WSLg socket 및 Xschem `top.sch`·KLayout GDS GUI 프로세스와 Windows 창 등록 확인.
- 이후 창이 투명한 WSLg 공유 메모리 오류를 확인했다. WSL VM 재시작으로
  복구했으며, 두 도구의 실제 화면 표시와 사용자 확인까지 완료했다.
- commit/push는 실행하지 않았다.

## 카운터 결과

실행 폴더: `physical/sky130/bringup_counter/runs/RUN_2026-11-09_21-13-09/`

| 항목 | 결과 |
|---|---|
| PDK revision | `8afc8346a57fe1ab7934ba5a6056ea8b43078e71` |
| Top cell | `bringup_counter` |
| GDS | `final/gds/bringup_counter.gds` |
| 파일 크기 | 585,366 bytes |
| Bounding box | 120 × 120 µm |
| 클록 제약 | 20 ns = 50 MHz |
| Magic / KLayout DRC 오류 | 0 / 0 |
| LVS 오류 | 0 |
| Antenna 위반 net / pin | 0 / 0 |
| Magic·KLayout GDS XOR 차이 | 0 |
| Setup / hold 위반 | 0 / 0 |
| 최악 setup / hold slack | +12.171975 / +0.109606 ns |
| 실행 error.log | 빈 파일 |

타이밍은 기본 SDC와 9개 timing corner 조합의 결과다. 실제 시스템의 I/O와
클록을 정의한 signoff 결과가 아니다.

GDS SHA-256:

```text
a4530acf06e52a54e7ecc6fd128d0e19790622924f0163a326e8d1731a190268
```

검증 요약과 결과 복사본은 `build/exports/RUN_2026-11-09_21-13-09/`에 있다.
원본 보고서는 실행 폴더의 `final/metrics.json`,
`55-openroad-stapostpnr/summary.rpt`, 단계별 DRC·LVS 보고서에 있다.
실행 로그는 `.local/logs/make-check.log`, `make-smoke.log`, `make-pnr.log`에 있다.

## 경고와 범위

기본 SDC 사용, 중복 Liberty 로딩, 배치 보정 중 floating net 2개,
일부 LEF58 rule 미지원, wire-length threshold 미설정에 따른 해당 검사 생략,
전원 공급 위치 `VSRC_LOC_FILES` 미설정에 따른 IR-drop 해석 한계 경고가 있었다.
전체 경고는 실행 폴더의 `warning.log`에 보존했다. 최종 연결성·LVS·DRC 통과와
별개로 제조용 프로젝트에서는 경고와 공정 signoff 규칙을 검토해야 한다.

이번 결과는 작은 디지털 카운터 블록이다. Pad/ESD, SRAM, CPU, AXI, DAC,
ADC, 패키지와 MPW top-level은 아직 구현·검증하지 않았다. 아날로그 공정 소자의
사용자 회로, 1 GSPS 성능, 추출 후 시뮬레이션도 이번 점검 범위에 포함하지 않았다.

## 후속 DAC 회로 검토 — 2026-11-09

`analog/dac14_2g/`에 14-bit 입력·2 GSPS·출력 대역 목표 500 MHz의 한 채널
초기 회로를 추가했다. Xschem 전류 셀, SKY130 소자를 사용한 전체 배열 SPICE,
5+9 분할 디코더 RTL, 재실행 명령과 그래프가 있다. 시스템 목표는 두 채널이다.
RTL lint와 16,384개 코드 검사를 통과했고, 기본 5 ps 시간 간격의 DC/네 가지
transient 조건을 실행했다. TT 499 MHz 출력의 0~1 GHz SFDR은 약 44.6 dBc다.
더 작은 적분 간격에서는 수렴 오류가 있어 수치는 잠정 결과다. 14-bit 동적
정밀도, 실제 디지털 2 GHz 타이밍, 레이아웃·GDS·DRC/LVS는 검증하지 않았다.
[설계·실행·한계에 대한 설명](../analog/dac14_2g/README.md)을 참고한다.

후속 [revision v1](../analog/dac14_2g/revision-v1.md)에서 ngspice의 동시 PWL
breakpoint 문제를 재현하고 `.tran`/`run`, `minbreak=1e-15`로 수정했다.
작은 steering switch를 사용한 회로는 큰 신호 전환을 개선했지만 major-carry
글리치에는 악화가 있어 함께 보고한다. 실제 14-bit 정밀도 및 제작 검증은 여전히 남아 있다.

## 안내

- [Verilog에서 GDS 생성하기](verilog-to-gds.md)
- [아날로그 GUI와 도구](../analog/README.md)
- [개발 환경과 파일 위치](development.md)

Windows checkout은 별도 복사본이며, 이후 수정은 Linux checkout을 기준으로 한다.
Windows 최초 설치 기록은 `C:/JeonghyunPark/Workspace/temp/openrfsoc-bootstrap/`에 있다.
