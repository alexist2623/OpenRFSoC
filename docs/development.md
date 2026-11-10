# Windows + WSL2 개발 환경

## 재부팅 후 최초 설정

1. Windows를 재부팅한다. 현재 설치 과정에서는 자동 재부팅하지 않았다.
2. 시작 메뉴의 **Ubuntu 24.04 LTS**를 실행한다. 최초 등록을 기다린 뒤 Linux
   사용자 이름과 비밀번호를 직접 정한다. 비밀번호는 저장소에 기록하지 않는다.
3. 일반 PowerShell에서 다음 명령을 실행한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\JeonghyunPark\Workspace\OpenRFSoC\scripts\windows\resume-setup.ps1
```

이 스크립트는 Ubuntu 안에서 기본 패키지와 Nix를 설치하고, Windows 저장소의
커밋 이력과 아직 커밋하지 않은 초기 파일을 `$HOME/work/OpenRFSoC`에 복사한다.
원격 저장소는 기존 GitHub 주소를 사용한다. 자동 commit/push는 하지 않는다.
Linux 대상 디렉터리가 이미 있으면 덮어쓰지 않고 종료한다. 기존 Linux
checkout에서 `bash scripts/bootstrap_linux.sh`를 실행하면 이어서 진행한다.

Ubuntu의 `sudo` 암호 요청에는 위에서 정한 Linux 비밀번호를 입력한다.
처음에는 Nix 도구 다운로드에 시간이 걸린다. 도구와 PDK가 수 GB 이상을
사용할 수 있으므로 `.local/`, Nix store와 PDK 캐시를 Git에 넣지 않는다.

Ubuntu가 시작되지 않으면 `wsl --status`와 `wsl --list --verbose`를 확인한다.
재부팅 이후에도 가상화 오류가 남으면 Windows VirtualMachinePlatform 활성화와
펌웨어 가상화 설정을 확인한다. 배포판을 unregister하거나 삭제하지 않는다.

## 평소 실행

Ubuntu 터미널에서:

```bash
cd ~/work/OpenRFSoC
bash scripts/eda.sh
make check
make smoke
make pnr
```

- `make check`: 파일 검증, Verilator lint, Icarus의 자체 검사 테스트벤치,
  Yosys generic 합성, 이상적 RC의 ngspice 측정과 도구 버전 기록.
- `make smoke`: LibreLane의 공식 SKY130 예제. 필요한 PDK를 Ciel로 내려받는다.
- `make pnr`: 카운터 RTL-to-GDS 실험. 50 MHz는 이 작은 예제의 제약이다.
  실제 RFSoC 목표 클록·면적·I/O 제약을 검증하는 작업이 아니다.
- `make doctor`: `.local/environment-report.json`에 설치된 실제 도구 버전을 기록한다.

한 명령만 실행하려면 `bash scripts/eda.sh make check`를 사용한다.
새 RTL을 연결하는 방법은 [Verilog에서 GDS까지](verilog-to-gds.md)를 참고한다.
자신의 설정은 `make pnr DESIGN_CONFIG=physical/sky130/my_top/config.json`으로 실행한다.
아날로그 회로도 GUI는 `bash scripts/xschem.sh`로 실행한다.
Nix 환경의 도구 버전은 `env/versions.json`의 LibreLane commit과 그 commit의
`flake.lock`에 의해 고정된다. 도구 업데이트는 해당 revision을 바꾸고 검증한다.
기존 Nix 설치가 있다면 공식 안내에 따라 FOSSi binary cache를 설정할 수 있다.
캐시를 쓰지 않아도 같은 도구를 빌드하지만 시간이 더 오래 걸릴 수 있다.

## WSLg 아이콘만 보이고 창이 투명할 때

2026-11-09에 Xschem·KLayout의 프로세스와 작업 표시줄 아이콘은 있었지만
실제 창이 표시되지 않는 문제가 발생했다. 창 제목에 `[WARN:COPY MODE]`,
`/mnt/wslg/weston.log`에 공유 메모리의 `Input/output error`와
`use_gfxredir = 0`이 기록되어 있었다. GDS 파일 자체의 오류는 아니었다.

Linux 작업과 편집 중인 파일을 저장한 뒤 PowerShell에서 `wsl --shutdown`을
실행하고 Ubuntu를 다시 열면 WSL VM과 WSLg가 재시작된다. Windows 재부팅은
필요하지 않았다. 이 명령은 모든 WSL 배포판과 Linux 앱을 종료하므로 실행 중인
시뮬레이션·합성이 있을 때는 먼저 끝내야 한다.

이 PC에서는 재시작 후 `use_gfxredir = 1`로 복구됐으며, Xschem 회로도와
KLayout GDS의 실제 화면 표시 및 사용자 확인까지 완료했다. 초기의 프로세스·창
등록 확인만으로 화면이 정상이라고 판단한 기록은 이 검증으로 보완한다.
문제가 재발하면 [Microsoft WSL 관련 이슈](https://github.com/microsoft/WSL/issues/41903)를 참고한다.

## 파일 위치

실제 작업 기준은 Linux checkout 하나로 한다. `/mnt/c`의 Windows checkout과
Linux checkout을 동시에 편집하지 않는다. Linux 파일을 VS Code의 WSL 연결로
열면 된다. Windows 원본은 Git으로 필요할 때 갱신한다.

PDK 기본 캐시는 `$HOME/.cache/openrfsoc/pdks`다. 위치 변경은
`make pnr PDK_ROOT=/다른/Linux/경로`로 지정한다. 물리 실행 결과의 `runs/`와
일반 `build/`는 무시되며, 제출할 GDS와 검증 결과는 검토한 릴리스에 별도로 보관한다.
SRAM, DAC, ADC와 최종 파운드리 pad는 아직 구성하지 않았다.

## 공식 자료

- WSL: https://learn.microsoft.com/en-us/windows/wsl/install
- Linux 파일 배치: https://learn.microsoft.com/en-us/windows/wsl/filesystems
- LibreLane Nix 설치: https://librelane.readthedocs.io/en/stable/installation/nix_installation/installation_win.html
- LibreLane 고정 소스: https://github.com/librelane/librelane/tree/4eccba312aff517e52cd9068bf86623a868e27c1
- IHP 아날로그 흐름: https://ihp-open-pdk-docs.readthedocs.io/en/latest/analog.html
