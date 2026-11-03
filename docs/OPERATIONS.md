# 30분 자동복구 · 1시간 조사 · 90분 검증 · 150분 캡스톤 운영 가이드

`continuous-pipeline.yml`은 자료 조사 1시간, 자료 검증·개선 90분, 캡스톤 생성 150분 주기로 실행합니다. 별도로 `sync-site.yml`이 **30분마다** 생성 산출물을 복구·검증하고, `verify.yml`이 **2시간마다** 전체 독립 회귀검사를 수행합니다. GitHub Actions 예약 시각은 지연될 수 있습니다.

자동화 단계 확인: GitHub Actions → **Continuous FPGA SoC research and capstone maintenance** → Run workflow `research`, `review`, `factory`, `all`.

`catalog/research_history.json`: 수집 기록 / `catalog/reviewed.json`: 메타데이터 검증 / `catalog/improvement_backlog.json`: 개선 계획 / `catalog/material_audit.json`: 기존 산출물 검증 기록 / `catalog/factory_history.json`: 과제화 이력.

- 30분마다 **기존 모든** 캡스톤의 HTML 링크, SVG, 연결표, 파일 해시, Verilog 테스트벤치, C 테스트를 반복 확인하고 안전한 생성물만 복구합니다.
- 2시간마다 별도 독립 회귀검사를 수행하고, 90분마다 외부 출처·기존 자료를 검증·개선합니다.
- 150분마다 새로운 과제 생성과 기존 산출물 재검증을 실행합니다.
- 실패는 `harness-failure-tracker.yml`에서 중복 없는 Issue로 추적하고, 동일 검사 재통과 시 닫습니다.
- 독립적인 내부 RTL이 없는 새로운 유형은 자동으로 거짓 소스를 생성하지 않고 개선 목록에 남깁니다.
- 자동 변경은 메타데이터/구조화 설계 초안/파생 산출물에 한정하며, 검증된 RTL·실제 XDC·보드 회로는 승인 없는 변형을 금지합니다.
- GitHub-hosted 실행이므로 로컬 PC는 필요하지 않지만 GitHub Actions는 정확한 주기 실행을 보장하지 않습니다.

GitHub Pages: Settings → Pages → Source GitHub Actions, Actions Variables에 `ENABLE_PAGES=true`. 별도로 설정하지 않으면 HTML은 저장소 `site/`에서 확인 가능합니다.

자세한 설명은 [SCHEDULED_PIPELINE.md](SCHEDULED_PIPELINE.md).

## HTML 확인

[전체 자료실 미리보기](https://htmlpreview.github.io/?https://github.com/Yuul-Jung/fpga-soc-harness-gpt/blob/main/site/index.html)에서 캡스톤 목록을 선택합니다. 각 과제는 `site/capstones/<id>/index.html`이며 전체 소스 ZIP과 구조도 SVG, BOM, 검증 결과를 포함합니다. GitHub Pages 설정: Settings → Pages → GitHub Actions, Actions Variables에서 `ENABLE_PAGES=true`로 설정하면 정식 URL을 사용할 수 있습니다. 정식 사이트 배포 성공은 GitHub Actions 결과에서 확인하십시오.
