# FPGA SoC Capstone Harness

AMD/Xilinx · Intel/Altera · Lattice의 **CPU 외 주변장치·캡스톤 자료**를 자동 조사하고, 축적한 결과를 반복 검증하여 구조화된 캡스톤을 만드는 하네스입니다.

## Claude 독립 개발 인계서 (HTML)

- **[Claude 개발 인계서 — HTML](site/docs/CLAUDE_HANDOFF_fpga_soc_harness.html)** — 실제 저장소 구조, 1h/2h/4h 자동화, 산출물·검증 기준, 독립 개발 지침.
- **[인계서 원본 HTML](docs/CLAUDE_HANDOFF_fpga_soc_harness.html)** — 사이트 재생성 시 복사되는 기준 파일.
- **[공개 HTML 화면 미리보기](https://htmlpreview.github.io/?https://github.com/Yuul-Jung/fpga-soc-harness-gpt/blob/main/site/docs/CLAUDE_HANDOFF_fpga_soc_harness.html)** — GitHub Pages 미활성화 시 임시 확인용 외부 프리뷰.

ChatGPT 저장소는 참고 구현이며 Claude는 별도 폴더·별도 Git 저장소에서 독립 개발합니다. 자동 생성 프로그램은 매 실행마다 인계서 HTML을 보존하고 메인 자료실에 연결합니다.

## HTML 온라인 교재 열람

**전체 메인 HTML:** [정식 메인 페이지](https://yuul-jung.github.io/fpga-soc-harness-gpt/) · [종합 자료실 미리보기](https://htmlpreview.github.io/?https://github.com/Yuul-Jung/fpga-soc-harness-gpt/blob/main/site/index.html) · [원본 index.html](site/index.html)

**캡스톤 목록:** [과제별 HTML 미리보기](https://htmlpreview.github.io/?https://github.com/Yuul-Jung/fpga-soc-harness-gpt/blob/main/site/capstones/index.html) · [원본 목록](site/capstones/index.html)

**예제: 스마트 팬·PWM:** [상세 HTML 미리보기](https://htmlpreview.github.io/?https://github.com/Yuul-Jung/fpga-soc-harness-gpt/blob/main/site/capstones/smart_fan/index.html) · [원본](site/capstones/smart_fan/index.html)

GitHub Pages **기본 주소**: **https://yuul-jung.github.io/fpga-soc-harness-gpt/**. 현재 Pages의 브랜치 배포 방식에서 저장소 최상단 `index.html`이 자료실 `site/index.html`로 자동 이동하도록 구성했습니다. 공개 미리보기는 외부 서비스이므로 민감한 문서를 입력하지 마세요. (배포 작업 성공 로그에서 실제 HTTPS Pages URL을 확인했습니다.)

- 모든 `capstones/<id>/design.json`에서 `site/index.html`, `site/capstones/index.html`, `site/capstones/<id>/index.html`을 생성합니다.
- 과제별 HTML에 전체 RTL·C 소스, 모듈 계통도 SVG, 신호 연결표, BOM, 검증 결과, `source_bundle.zip`을 수록합니다.
- GitHub Actions 1h/2h/4h 실행 때 해당 HTML과 과거 자료를 다시 생성·검증합니다.
- 실사용 웹사이트 활성화: 저장소 **Settings → Pages → Source: GitHub Actions**, **Settings → Secrets and variables → Actions → Variables → ENABLE_PAGES=true** 설정.

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
