"""Creative, reproducible capstone design briefs; no fictitious RTL or test evidence.

Distinct input pairs, output, decision policy and communication path make
new functional combinations. Implemented IP remains separately gated.
"""
import itertools
import json
from pathlib import Path

from .generate import ROOT

# Curated, functionally distinct teaching projects before combinatorial variants.
IDEAS = [
    ("warehouse_access", "스마트 창고 출입·문열림 이력", "PIR 움직임", "마그네틱 도어 스위치", "LED·부저", "움직임과 문열림 순서를 비교해 출입 이벤트를 기록", "UART 이벤트"),
    ("smart_parking", "차량 접근 감지형 주차 차단기", "HC-SR04 거리", "수동 승인 버튼", "SG90 서보", "거리 유효값과 승인 신호를 함께 확인해 차단기 개폐", "상태 레지스터"),
    ("greenhouse_fan", "온습도 연동 온실 환기", "DHT22 온습도", "수동 모드 스위치", "PWM 팬", "상·하한 히스테리시스와 수동 우선 정책으로 팬 제어", "UART 기록"),
    ("bike_safety_light", "자전거 속도 반응형 안전등", "로터리 엔코더", "조도 센서", "LED PWM", "회전 이벤트와 어두움 조건에 따라 점멸 주기 제어", "상태 레지스터"),
    ("water_leak_alarm", "누수·접촉 이중 확인 경보", "누수 감지 모듈", "TTP223 터치", "능동 부저", "누수 이벤트 래치와 사용자 확인으로 경보 해제", "UART 이벤트"),
    ("night_corridor", "사람 접근형 야간 복도 조명", "PIR 움직임", "BH1750 조도", "LED PWM", "움직임·저조도 동시 만족 시 일정 시간 조명 유지", "상태 레지스터"),
    ("smart_blind", "빛·온도 연동 자동 블라인드", "BH1750 조도", "DHT22 온도", "SG90 서보", "과조도와 고온 조건을 분리해 블라인드 각도 결정", "UART 이벤트"),
    ("motor_vibration_guard", "모터 진동 보호 및 정지 제어", "진동 스위치", "회전 펄스", "DC 모터 드라이버", "이상 진동 누적 시 모터 구동 차단·재시작 인터록", "상태 레지스터"),
    ("smart_planter", "토양 건조·강우 상태 알림", "토양 수분 센서", "빗물 감지 센서", "LED 상태등", "건조 지속과 강우 감지에 따라 물주기 알림 우선순위 결정", "UART 이벤트"),
    ("queue_counter", "양방향 통과 인원 계수기", "IR 빔 센서 A", "IR 빔 센서 B", "7세그먼트 표시", "두 빔의 통과 순서로 입장·퇴장 계수를 분리", "상태 레지스터"),
    ("door_timeout", "문열림 시간 초과 경보", "마그네틱 도어 스위치", "PIR 움직임", "능동 부저", "문열림 지속시간과 사람 존재를 조합해 단계별 경보", "UART 이벤트"),
    ("pulse_quality", "산업 펄스 이상 감시기", "펄스 입력", "진동 스위치", "LED 상태등", "누락·과속·연속 진동 이벤트를 분류하고 오류 래치", "상태 레지스터"),
]
SENSORS = [
    "PIR 움직임", "HC-SR04 거리", "DHT22 온도", "DHT22 습도",
    "BH1750 조도", "로터리 엔코더", "TTP223 터치", "진동 스위치",
    "마그네틱 도어 스위치", "토양 수분 센서", "빗물 감지 센서", "펄스 입력",
]
ACTUATORS = [
    "LED PWM", "능동 부저", "SG90 서보", "DC 모터 드라이버",
    "7세그먼트 표시", "UART 경보", "릴레이 제어", "TFT 상태 표시",
]
POLICIES = [
    "이중 조건 일치 시 동작", "순차 이벤트 검출 후 동작",
    "지속시간 초과 시 경보", "상·하한 히스테리시스 제어",
    "수동 승인 후 자동 제어", "이벤트 횟수 누적 후 동작",
    "오류 래치 후 명시적 복구", "타임아웃 및 센서 불일치 검출",
]
TELEMETRY = ["UART 이벤트", "상태 레지스터", "7세그먼트 상태", "LED 오류 코드"]


def candidates():
    for item in IDEAS:
        yield item
    # Deterministic round-robin permutations; every tuple changes real behavior.
    count = len(SENSORS) * (len(SENSORS) - 1) * len(ACTUATORS) * len(POLICIES) * len(TELEMETRY)
    for ordinal in range(count):
        index = (ordinal * 1009) % count  # 1009 coprime with this product.
        telemetry = TELEMETRY[index % len(TELEMETRY)]
        index //= len(TELEMETRY)
        policy = POLICIES[index % len(POLICIES)]
        index //= len(POLICIES)
        actuator = ACTUATORS[index % len(ACTUATORS)]
        index //= len(ACTUATORS)
        other_index = index % (len(SENSORS) - 1)
        first_index = index // (len(SENSORS) - 1)
        second_index = other_index + (other_index >= first_index)
        a, b = SENSORS[first_index], SENSORS[second_index]
        slug = f"fusion_{first_index:02d}_{second_index:02d}_{ACTUATORS.index(actuator):02d}_{POLICIES.index(policy):02d}_{TELEMETRY.index(telemetry):02d}"
        yield (slug, f"복합 주변장치 제어 — {a} + {b} → {actuator}",
               a, b, actuator, policy, telemetry)


def create_creative_capstone(root=None):
    """Create exactly one NEW project, preserving existing ones."""
    root = Path(root) if root is not None else ROOT
    for slug, title, a, b, actuator, policy, telemetry in candidates():
        ident = "creative_" + slug
        folder = root / "capstones" / ident
        if folder.exists():
            continue
        modules = [
            {"id": "sensor_a", "name": a + " (설계용 인터페이스)", "inputs": [], "outputs": ["sample"]},
            {"id": "sensor_b", "name": b + " (설계용 인터페이스)", "inputs": [], "outputs": ["sample"]},
            {"id": "controller", "name": "capstone_controller (신규 제안)", "inputs": ["sample_a", "sample_b"], "outputs": ["command", "status"]},
            {"id": "actuator", "name": actuator + " (출력 드라이버)", "inputs": ["command"], "outputs": []},
            {"id": "telemetry", "name": telemetry + " (진단 출력)", "inputs": ["status"], "outputs": []},
        ]
        nets = [
            {"from": "sensor_a.sample", "to": "controller.sample_a", "note": "Conceptual only; define real width, valid and CDC"},
            {"from": "sensor_b.sample", "to": "controller.sample_b", "note": "Conceptual only; define real width, valid and CDC"},
            {"from": "controller.command", "to": "actuator.command", "note": "No physical driver implemented"},
            {"from": "controller.status", "to": "telemetry.status", "note": "Status mapping not yet implemented"},
        ]
        design = {
            "schema_version": 1, "id": ident, "title": title,
            "summary": f"자체 창작 캡스톤: {a}와 {b}를 조합해 {policy} 정책으로 {actuator}를 제어하고 {telemetry}로 상태를 제공한다. 독립적인 신규 과제 설계서이며 구현 검증은 별도 단계다.",
            "board": "Basys3 / MicroBlaze V 확장 후보 (실제 핀·전압·자원 미확정)",
            "status": "DESIGN_ONLY_NOT_IMPLEMENTED (RTL·합성·보드 검증 미실시)",
            "modules": modules, "connections": nets,
            "source_files": ["INTEGRATION.md"],
            "bom": [
                {"part": "Basys3", "quantity": "1", "interface": "3.3V FPGA I/O", "notes": "핀·XDC·리소스 확인 필요"},
                {"part": a, "quantity": "1", "interface": "모듈별 확인 필요", "notes": "전원과 FPGA 입력 전압 구분"},
                {"part": b, "quantity": "1", "interface": "모듈별 확인 필요", "notes": "데이터시트·풀업·레벨 확인"},
                {"part": actuator, "quantity": "1", "interface": "드라이버/전원 확인 필요", "notes": "부하를 FPGA 핀에 직접 연결하지 않음"},
            ],
            "verification_notice": "교육용 설계안만 생성. 실제 RTL, 시뮬레이션, AXI, 합성, 타이밍, 보드 시험 미실시.",
            "safety_notice": "Basys3 GPIO 3.3V, XADC 단극성 입력 0~1V. 5V 신호·모터·릴레이·서보 부하 직결 금지. 실제 보드별 전압 변환 및 구동회로 검증 필요.",
            "provenance": "Original educational concept; no external source code or image copied.",
        }
        lines = [
            "# " + title, "",
            "## 구현 수준", "독립 캡스톤 설계안. RTL·테스트벤치·C·AXI·Vivado·실물 보드는 미구현/미검증.", "",
            "## 기능 요구사항",
            f"- 입력 1: {a} (전기적 특성·출력 신호·샘플 유효 조건을 확인한 뒤 연결)",
            f"- 입력 2: {b} (서로 다른 샘플 주기와 비동기 이벤트를 구분)",
            f"- 제어 정책: {policy}. Reset과 타임아웃/센서 오류의 안전 상태 정의",
            f"- 출력: {actuator} (전원/구동 회로 별도 검토)",
            f"- 진단: {telemetry} (유효값, 오류, 마지막 이벤트와 상태 구분)", "",
            "## 회로 구조 (모듈명은 신규 제안, 실제 RTL 포트 아님)",
            f"{a} → sensor_a.sample → capstone_controller.sample_a",
            f"{b} → sensor_b.sample → capstone_controller.sample_b",
            f"capstone_controller.command → {actuator}",
            f"capstone_controller.status → {telemetry}", "",
            "## 구현 절차",
            "1. 모듈별 실제 데이터시트·핀·3.3V 호환성 및 외부 부하 전원 검토",
            "2. 두 입력의 샘플 시점, 이벤트 펄스, 클럭 도메인·Reset 정의",
            "3. Controller FSM과 입력 유효성·타임아웃·우선순위 규칙 확정",
            "4. 독립 RTL 및 자기검증 테스트벤치 작성 후 시뮬레이션",
            "5. 필요한 경우 AXI GPIO/사용자 AXI IP로 MicroBlaze V 연결",
            "6. Vivado 합성·타이밍·XDC·실물 보드 검증을 각각 별도 기록", "",
            "## 검증 시나리오",
            "- Reset 후 출력 안전 상태",
            "- 입력 1만 발생 / 입력 2만 발생 / 두 입력 동시 발생",
            "- 입력 변화 순서 반대 / 바운스 / 입력 무효 및 타임아웃",
            "- 출력 구동 중 재입력 / 긴급 중지 / 복귀 동작",
            "- 표시 및 레지스터 값과 실제 이벤트의 일치", "",
            "## 안전 및 출처", design["safety_notice"],
            "독립적으로 작성한 설계안. 외부 코드·이미지 복제 없음.",
        ]
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "INTEGRATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (folder / "design.json").write_text(json.dumps(design, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return ident
    raise RuntimeError("All distinct creative combinations exhausted; extend functional catalog")


if __name__ == "__main__":
    print(create_creative_capstone())
