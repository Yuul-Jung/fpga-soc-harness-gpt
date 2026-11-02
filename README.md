# FPGA SoC Capstone Harness

AMD/Xilinx · Intel/Altera · Lattice의 **CPU 외 주변장치·캡스톤 자료**를 자동 조사하고, 출처가 남는 설계 규격 및 실행 가능한 실습 자료를 축적하는 하네스입니다.

## 3개 계층
1. **Reference**: GitHub 검색 → 라이선스·소스 파일·검증 근거 추적 → 후보 카탈로그
2. **Design IR**: 검토된 응용 설계를 JSON의 모듈·포트·넷·제약·검증 조건으로 표현
3. **Capstone**: 결정적 생성기로 HTML·SVG 구조도·넷리스트·BOM·RTL/테스트벤치/소프트웨어 소스를 게시

## 실행 (Python 3.10+, 표준 라이브러리)
```bash
python3 -m harness.discover
python3 -m harness.propose
python3 -m harness.generate
python3 -m harness.validate
python3 -m unittest discover -s tests -v
```
선택적 RTL 시뮬레이션: `sudo apt install iverilog`. 생성 사이트는 `site/index.html`부터 탐색합니다.

## 자동 동작
- 매주 GitHub Actions가 공개 GitHub 저장소를 검색하고 후보·기술 제안·HTML 색인을 갱신합니다.
- **후보 발견은 소스 검증이 아닙니다.** 라이선스 미확정/GPL 소스는 메타데이터 참조로만 보관합니다.
- 공개 프로젝트 소스를 자동 다운로드·재배포·실행하지 않습니다.
- 실행 가능한 소스는 본 저장소의 승인된 자체 설계 템플릿에서만 생성·배포합니다.
- 하드웨어 검증을 실행하지 않았는데 '보드 동작 검증 완료'라고 기록하지 않습니다.

## 첫 번째 캡스톤
`capstones/smart_fan/` — Basys3 100 MHz 클럭 기반 PWM + Tach 센서 카운터; AXI GPIO를 통한 MicroBlaze V SoC 확장 **설계 예시**. 실제 AXI 프로젝트·핀 배정·보드 테스트는 아직 미구현입니다.

구조/승인 규정: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/VALIDATION_GATES.md](docs/VALIDATION_GATES.md)

## 주의
리포지토리의 MIT 라이선스는 **이 저장소에서 새로 작성한 하네스/예제에만 적용**됩니다. 제3자 원본의 라이선스를 변경하지 않습니다. 모터/팬/센서는 FPGA I/O 핀에서 직접 구동하지 않고 3.3V 호환 인터페이스와 외부 드라이버·전원 보호가 필요합니다.
