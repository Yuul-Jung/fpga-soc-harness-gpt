# FPGA SoC Capstone Harness

AMD/Xilinx · Intel/Altera · Lattice의 **CPU 외 주변장치·캡스톤 자료**를 자동 조사하고, 축적한 결과를 반복 검증하여 구조화된 캡스톤을 만드는 하네스입니다.

## 1h → 2h → 4h 자동 순환

| 단계 | 실행 주기 | 주요 결과 |
|---|---|---|
| Creative Research | 매시간 | 새로운 GitHub 자료 검색·중복 제거, SHA·라이선스 이력, **기존 자료 전체 회귀검증 및 파생 문서 자동 보수** |
| Review & Improve | 2시간마다 | 과거 자료 전체 재검토, 소스·제약·테스트벤치/라이선스 평가, 기존 HTML/구조도/소스 회귀 검증 및 안전한 문서 수정 |
| Capstone Factory | 4시간마다 | 검증된 내부 IP 템플릿 기반 과제화; **기존 과제 전체도 항상 재검증·개선** |

모든 자동 실행은 GitHub Actions에서 수행하며 PC가 꺼져 있어도 동작합니다. GitHub 예약 작업은 실행 시각 지연/누락 가능성이 있습니다.

- 상세 일정: [docs/SCHEDULED_PIPELINE.md](docs/SCHEDULED_PIPELINE.md)
- 설계 원칙: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 기술 검증 기준: [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)
- 사용/배포: [docs/OPERATIONS.md](docs/OPERATIONS.md)

## 산출물의 단일 진실 소스

`capstones/<id>/design.json` → `site/capstones/<id>/index.html` +
`system.svg`(모듈 구조도) + `connections.json`(포트 넷 연결) +
`bom.csv` + `source/` + `verification.json`.

자료 소스 이력: `catalog/discovered.json`, `catalog/reviewed.json`, `catalog/improvement_backlog.json`, `catalog/material_audit.json`.

## 실행 (Python 3.11+, Icarus Verilog 권장)

```bash
python3 -m harness.research
python3 -m harness.review --offline
python3 -m harness.refine
python3 -m harness.factory
python3 -m harness.maintenance --stage factory
python3 -m unittest discover -s tests -v
```

RTL 테스트 Ubuntu 도구: `sudo apt install iverilog`. 생성된 사이트는 `site/index.html`에서 시작합니다.

## 자동으로 수정할 것과 수정하지 않을 것
- **자동 수집/갱신:** 공개 메타데이터, 출처, 자료 요약, 후보 정렬, 점수, 개선 목록.
- **자동 검증/수정:** 기존 HTML·SVG 구조도·접속표·BOM·소스 해시 검증, 안전한 파생 산출물 재생성.
- **검증된 템플릿으로 과제화:** 내부 RTL, 테스트벤치, C 예제, Design IR, HTML, 구조화 연결정보.
- **자동 덮어쓰기 금지:** 제3자 RTL, 기존 사람이 작성한 RTL·XDC, 실제 보드 핀·전압, 검증되지 않은 Vivado 블록 설계.
- 원본 IP와 보드 실물 동작을 입증하지 않은 경우 실행 성공으로 표기하지 않습니다.

GitHub Pages 배포는 저장소 Settings에서 별도 활성화해야 합니다. 자동 생성된 SVG는 디지털 **모듈 계통도**이며 실제 KiCad 회로도/ERC 인증은 별도의 목표입니다.

본 저장소의 MIT 라이선스는 자체 작성 코드에만 적용하며 제3자 소스 저작권은 별도 유지합니다.
