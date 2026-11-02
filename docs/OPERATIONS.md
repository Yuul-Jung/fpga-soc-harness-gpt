# 1/2/4시간 운영 가이드

매시간 :07 KST GitHub 검색, 2시간마다 :17 KST 검증·개선, 4시간마다 :27 KST 과제 생성·과거자료 재검증을 실행합니다. `continuous-pipeline.yml`이 유일한 예약 워크플로입니다.

자동화 단계 확인: GitHub Actions → **Continuous FPGA SoC research and capstone maintenance** → Run workflow `research`, `review`, `factory`, `all`.

`catalog/research_history.json`: 수집 기록 / `catalog/reviewed.json`: 메타데이터 검증 / `catalog/improvement_backlog.json`: 개선 계획 / `catalog/material_audit.json`: 기존 산출물 검증 기록 / `catalog/factory_history.json`: 과제화 이력.

- 2시간마다 **기존 모든** 캡스톤의 HTML 링크, SVG, 연결표, 파일 해시, Verilog 테스트벤치, C 테스트를 반복 확인합니다.
- 4시간마다 새로운 과제 템플릿이 검증됐는지 판단하고, 기존 산출물을 모두 재검증·재생성합니다.
- 독립적인 내부 RTL이 없는 새로운 유형은 자동으로 거짓 소스를 생성하지 않고 개선 목록에 남깁니다.
- 자동 변경은 메타데이터/구조화 설계 초안/파생 산출물에 한정하며, 검증된 RTL·실제 XDC·보드 회로는 승인 없는 변형을 금지합니다.
- GitHub-hosted 실행이므로 로컬 PC는 필요하지 않지만 GitHub Actions는 정확한 주기 실행을 보장하지 않습니다.

GitHub Pages: Settings → Pages → Source GitHub Actions, Actions Variables에 `ENABLE_PAGES=true`. 별도로 설정하지 않으면 HTML은 저장소 `site/`에서 확인 가능합니다.

자세한 설명은 [SCHEDULED_PIPELINE.md](SCHEDULED_PIPELINE.md).
