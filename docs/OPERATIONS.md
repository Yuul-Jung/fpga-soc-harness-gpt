# 운영 절차

## 자동 수집 주기
매주 월요일 08:30 KST(UTC 일요일 23:30) GitHub Actions `discover.yml`. GitHub 일정 실행은 지연될 수 있으며 개인 PC 전원을 켜 놓을 필요가 없습니다.

검색 항목: `config/search_queries.json`. 한 번의 검색 최대 후보 수: `config/policy.json`. `GITHUB_TOKEN`은 GitHub Actions 기본 토큰을 사용합니다. 외부에서 받은 스크립트는 실행하지 않습니다.

## 후보 → 독립 캡스톤
1. `catalog/discovered.json`에서 RTL·테스트벤치·핀제약·라이선스 근거 확인
2. `catalog/proposals.json`의 자동 분류와 IP 추천을 **초안**으로 검토
3. 사용하려는 원본 라이선스, 출처 SHA, 보드 IO, CPU/버스 구조와 부품 전압 검토
4. 승인된 설계를 `capstones/<id>/design.json`으로 작성하고 본 저장소에서 작성한 RTL/테스트벤치를 등록
5. `python3 -m harness.generate` → HTML, SVG, connections.json, BOM, 원본 해시 manifest
6. `python3 -m harness.validate` → 시뮬레이션·C 테스트 결과 기록
7. Vivado/Quartus/Radiant 환경별 합성, 핀 제약, 실제 보드 실험은 별도 검증 증빙으로 관리

## HTML 배포
`site/index.html`이 정적 인덱스입니다. GitHub Pages를 자동 배포하려면 저장소 Settings → Pages → Source를 GitHub Actions로 설정하고, Settings → Secrets and variables → Actions → Variables에서 `ENABLE_PAGES`를 `true`로 설정합니다. 활성화 이전에는 Pages 작업이 건너뛰어집니다.

## 안전 및 자동수정 정책
- 자료 수집은 후보·제안·HTML 미리보기만 자동 갱신합니다.
- 확정 RTL, 실제 XDC/QSF/LPF, Vivado IP 설정과 PCB 계통도는 자동 덮어쓰지 않습니다.
- 승인 없는 원본 복사, 외부 저장소 빌드 실행, 완성되지 않은 SoC의 동작 성공 표기를 금지합니다.
- 기술 변환을 자동화할 때도 변환 규격/테스트가 정의된 내부 RTL 라이브러리 기반으로 진행하며, 새로운 버스/핀 연결은 PR 검증을 거칩니다.
- CI에서 통과한 RTL 시뮬레이션은 실제 FPGA 보드 검증이 아닙니다.
