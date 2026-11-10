# OpenRFSoC

RISC-V와 자체·무상 오픈소스 IP를 사용하는 혼합신호 ASIC 연구 프로젝트.
목표는 14-bit 입력·2 GSPS·출력 대역 약 500 MHz의 DAC 2채널이며,
가능하면 약 1 GSPS ADC를 통합한다. 상용 AXI IP 구매는 제외한다.
SKY130을 선호하며 최종 공정, 동적 정밀도와 ADC 분해능은 확정하지 않았다.

현재 단계는 개발 환경과 검증 예제, 한 채널 DAC의 회로 타당성 검토다.
CPU, AXI fabric, 완성된 DAC/ADC와 실제 RFSoC 데이터 경로는 아직 구현하지 않았다.

- [초기 사양과 완료 기준](docs/specification.md)
- [WSL2 설치 이후 개발 시작](docs/development.md)
- [설치 작업 상태](docs/setup-status.md)
- [Verilog 작성부터 GDS 생성까지](docs/verilog-to-gds.md)
- [14-bit / 2 GSPS DAC 초기 설계와 실행](analog/dac14_2g/README.md)
- [DAC 수렴 오류 수정과 회로 개선 전·후 비교](analog/dac14_2g/revision-v1.md)
- [도구 버전 고정](env/versions.json)

## 빠른 시작

Windows 재부팅 후 Ubuntu 24.04 LTS를 처음 실행해 사용자 계정을 만든다.
그다음 일반 PowerShell에서:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\JeonghyunPark\Workspace\OpenRFSoC\scripts\windows\resume-setup.ps1
```

Linux 작업 폴더가 준비되면 Ubuntu에서:

```bash
cd ~/work/OpenRFSoC
bash scripts/eda.sh
make check
make smoke
make pnr
```

## 구조

| 경로 | 내용 |
|---|---|
| `rtl/` | 공정에 독립적인 자체 디지털 RTL |
| `dv/` | 디지털 테스트벤치 |
| `firmware/` | 향후 RISC-V 펌웨어 |
| `analog/` | 아날로그 회로와 SPICE 테스트벤치 |
| `physical/` | 공정별 물리 구현 설정 |
| `third_party/` | 외부 IP의 출처·버전·라이선스 관리 |
| `env/`, `scripts/` | 도구 버전과 설치·실행·점검 스크립트 |
| `docs/` | 사양, 개발 절차와 검증 상태 |

현재 포함된 counter와 RC 회로는 도구 점검용이다. 테스트 통과나 GDS 생성은
1 GSPS 변환기 동작, 최종 칩 타이밍 또는 테이프아웃 준비 완료를 뜻하지 않는다.
