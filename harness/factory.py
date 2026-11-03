"""150-minute capstone factory. Require a genuinely new documented project each run.

Only a reviewed first-party RTL template can be marked implemented. When no
approved new RTL template exists, create a distinct design-only capstone brief
from a not-yet-used reviewed proposal. Never claim that concept RTL was tested.
If the qualified source pool is exhausted, fail visibly instead of fabricating
a success or duplicating an old capstone.
"""
import datetime as dt
import json
from pathlib import Path
import shutil
import re

from .generate import ROOT
from .research import load

FACTORY_HISTORY = ROOT / "catalog/factory_history.json"
REFERENCE_AUDIT = ROOT / "catalog/reviewed.json"
TEMPLATE_ID = "instrument_pulse_counter"
TEMPLATE_FILES = {
    "rtl/pulse_event_meter.v": ROOT / "library/rtl/pulse_event_meter.v",
    "tb/tb_pulse_event_meter.v": ROOT / "library/tb/tb_pulse_event_meter.v",
    "sw/pulse_meter_mmio.c": ROOT / "library/sw/pulse_meter_mmio.c",
}


def instrument_design(reference):
    return {
        "schema_version": 1, "id": TEMPLATE_ID,
        "title": "FPGA SoC 캡스톤 — 펄스·회전수 계측 주변장치",
        "summary": "Basys3 100MHz 클럭에서 2-FF 동기화 및 1초 이벤트 계측을 수행하는 독립 RTL. "
                   "MicroBlaze V + AXI GPIO 읽기 포트로 확장하는 SoC 설계안이며 "
                   "Vivado Block Design과 보드 실험은 미완료입니다.",
        "board": "Basys3, 100MHz, 3.3V I/O",
        "status": "original RTL + testbench implemented; MicroBlaze V connection proposed",
        "modules": [
            {"id":"clk_src","name":"basys3_clock_reset", "inputs":[], "outputs":["clk","rst"]},
            {"id":"cpu","name":"microblaze_v", "inputs":["clk","reset"], "outputs":["m_axi"]},
            {"id":"axi_gpio","name":"axi_gpio_status", "inputs":["s_axi","gpio_io_i"], "outputs":[]},
            {"id":"event_meter","name":"pulse_event_meter",
             "inputs":["clk","rst","pulse_in"], "outputs":["event_count","sample_valid"]},
            {"id":"input_stage","name":"external_3v3_pulse_interface",
             "inputs":[], "outputs":["pulse_out"]},
        ],
        "connections": [
            {"from":"clk_src.clk","to":"cpu.clk","note":"Conceptual 100MHz clock, IP/clocking not yet built"},
            {"from":"clk_src.rst","to":"cpu.reset","note":"Actual reset polarity must match CPU IP"},
            {"from":"clk_src.clk","to":"event_meter.clk","note":"Single domain"},
            {"from":"clk_src.rst","to":"event_meter.rst","note":"Synchronous active-high reset"},
            {"from":"cpu.m_axi","to":"axi_gpio.s_axi","note":"AXI interconnect omitted in this conceptual view"},
            {"from":"event_meter.event_count","to":"axi_gpio.gpio_io_i",
             "note":"32-bit GPIO input; AXI address from Vitis BSP, not guessed"},
            {"from":"input_stage.pulse_out","to":"event_meter.pulse_in",
             "note":"3.3V-conditioned asynchronous pulse, synchronized internally"}
        ],
        "source_files": list(TEMPLATE_FILES) + ["INTEGRATION.md"],
        "bom": [
            {"part":"Basys3","quantity":"1","interface":"3.3V I/O 100MHz","notes":"Official XDC must be checked"},
            {"part":"3.3V pulse generator or isolated conditioned sensor",
             "quantity":"1","interface":"digital pulse","notes":"No direct 5V/12V connection"}
        ],
        "verification_notice":"초기 자동 생성 시 독립 RTL만 테스트합니다. "
            "Vivado·MicroBlaze V·AXI 실물 프로젝트, 실제 핀, 합성·보드 검증 없음.",
        "safety_notice":"5V/12V 신호·모터전원·유도성 부하는 Basys3 FPGA 핀에 직접 연결 금지. "
            "전압 변환, 풀업, 전류 제한, 접지 또는 절연을 검증하세요.",
        "provenance":"Original first-party module; the referenced repository is metadata-only inspiration: "
                     + reference["source_url"] + " at " + str(reference.get("source_tree_sha")),
        "test_spec":{
            "rtl_top":"tb_pulse_event_meter", "rtl_files":["rtl/pulse_event_meter.v","tb/tb_pulse_event_meter.v"],
            "rtl_success":"PASS pulse_event_meter", "c_file":"sw/pulse_meter_mmio.c",
            "c_define":"PULSE_METER_SELFTEST", "c_success":"PASS pulse_meter_mmio self-test"
        }
    }


INTEGRATION = """# FPGA SoC pulse counter — first-party starter

Architecture: synchronized external pulse -> 32-bit counter snapshot -> AXI GPIO
input -> MicroBlaze V application reads DATA register. The AXI GPIO, CPU,
clock/reset and board pins are **conceptual only** until a reproducible
Vivado/Vitis design and XDC are added.

## Files
- rtl/pulse_event_meter.v — synthesizable counter, one-second window at 100MHz
- tb/tb_pulse_event_meter.v — Icarus Verilog self-checking simulation
- sw/pulse_meter_mmio.c — application helper, with native C self-test

## Timing
WINDOW_CYCLES=100000000 at 100 MHz means one update per 1 second.
At WINDOW_CYCLES=64 in simulation, a 64-clock test window is used.
event_count is a pulse count per window, not necessarily RPM.
For a sensor producing P pulses per revolution, RPM is
event_count * 60 / P, if the window is one second.

## Physical constraints
FPGA I/O is 3.3V. Route external pulses through a compatible conditioned
driver. Physical pin assignments, interrupt registration and real address map
must come from a tested board design; no invented address or XDC.

## Run in repository root
```bash
iverilog -g2012 -s tb_pulse_event_meter -o /tmp/counter.vvp \
  capstones/instrument_pulse_counter/rtl/pulse_event_meter.v \
  capstones/instrument_pulse_counter/tb/tb_pulse_event_meter.v
vvp /tmp/counter.vvp
cc -std=c11 -DPULSE_METER_SELFTEST \
  capstones/instrument_pulse_counter/sw/pulse_meter_mmio.c -o /tmp/counter_sw
/tmp/counter_sw
```
"""


def build_candidate(reviews):
    candidates = [r for r in reviews
                  if r.get("category") == "instrument"
                  and r.get("readiness") == "metadata_reviewed_for_design_proposal"
                  and r.get("reuse_policy") == "review_for_reuse"
                  and int(r.get("quality_score", 0)) >= 40]
    return sorted(candidates, key=lambda r: (-r["quality_score"], r["reference"]))[0] if candidates else None


def create_design_only_capstone(proposals):
    """Create one new educational design brief without pretending it has RTL."""
    from .draft import make_draft

    for proposal in proposals:
        if proposal.get("audit_readiness") != "metadata_reviewed_for_design_proposal":
            continue
        draft = make_draft(proposal)
        project_id = "study_" + draft["id"][:80]
        folder = ROOT / "capstones" / project_id
        if folder.exists():
            continue
        blocks = draft["modules"]
        if len(blocks) < 2:
            continue
        design = {
            "schema_version": 1,
            "id": project_id,
            "title": "FPGA SoC 캡스톤 설계 과제 — " + proposal["reference"],
            "summary": "주변장치 설계 및 구현 과제. 공개 저장소 메타데이터를 "
                       "참고하여 작성한 자체 교육용 구조안이며, 실제 RTL 포팅·"
                       "시뮬레이션·Vivado·보드 시험은 아직 수행하지 않았습니다.",
            "board": "Basys3 후보 (핀·전압·리소스 적합성 미검증)",
            "status": "DESIGN_ONLY_NOT_IMPLEMENTED (RTL·보드 검증 없음)",
            "modules": blocks,
            "connections": draft["connections"],
            "source_files": ["INTEGRATION.md"],
            "bom": [
                {"part": "Basys3", "quantity": "1",
                 "interface": "3.3V FPGA I/O", "notes": "실제 XDC·자원 검토 필요"},
                {"part": "연결 대상 주변모듈 (미선정)", "quantity": "1",
                 "interface": "미확정", "notes": "데이터시트·전압 검증 전 연결 금지"},
            ],
            "verification_notice": "설계 구상만 작성됨. RTL, C, AXI, 합성, 타이밍, "
                                   "보드 검증 모두 미실시.",
            "safety_notice": "5V 신호를 FPGA 3.3V 핀에 직접 연결하지 말 것. "
                             "실제 IC·모듈별 전원/풀업/레벨 변환 검토 필요.",
            "provenance": "Metadata-only educational inspiration: " +
                          proposal["source_url"] + " at " +
                          str(proposal.get("source_tree_sha")),
        }
        lines = [
            "# " + design["title"],
            "",
            "## 현재 단계: 설계 구상 (미구현)",
            "실제 RTL, 테스트벤치, C 드라이버, AXI IP, XDC, 합성 및 보드 테스트가 없습니다.",
            "아래 블록과 신호명은 교육용 개념명이며 원본 RTL 포트가 아닙니다.",
            "",
            "## 기능 블록 및 개념 신호",
        ]
        lines += ["- " + b["name"] + ": 입력 " + ", ".join(b["inputs"]) +
                  " / 출력 " + ", ".join(b["outputs"]) for b in blocks]
        lines += [
            "", "## 다음 구현 순서",
            "1. 원본 데이터시트와 라이선스, 3.3V 신호 적합성 확인",
            "2. 클럭/리셋/포트 폭/타이밍 요구사항 확정",
            "3. 기능 RTL과 자기검증 테스트벤치 신규 작성",
            "4. 독립 RTL 시뮬레이션 통과 후 AXI 또는 스트림 연결 검토",
            "5. Vivado 합성·타이밍·실물 보드 검증을 각각 기록",
            "", "## 참고 자료 (소스 코드 복제 없음)",
            proposal["source_url"],
            "Source tree SHA: " + str(proposal.get("source_tree_sha")),
            "License: " + str(proposal.get("license_spdx")),
            "Reuse policy: " + str(proposal.get("reuse_policy")),
        ]
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "INTEGRATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (folder / "design.json").write_text(
            json.dumps(design, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return project_id
    return None


def run(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    old = load(FACTORY_HISTORY, {"runs": []})
    reviews = load(REFERENCE_AUDIT, {"reviews": []}).get("reviews", [])
    proposals = load(ROOT / "catalog/proposals.json", {"proposals": []}).get("proposals", [])
    folder = ROOT / "capstones" / TEMPLATE_ID
    created = []
    needs_research = []
    if not folder.exists():
        candidate = build_candidate(reviews)
        if candidate:
            folder.mkdir(parents=True)
            for relative, source in TEMPLATE_FILES.items():
                if not source.exists():
                    raise FileNotFoundError("First-party template missing: " + str(source))
                dest = folder / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
            (folder / "INTEGRATION.md").write_text(INTEGRATION, encoding="utf-8")
            (folder / "design.json").write_text(
                json.dumps(instrument_design(candidate), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            created.append(TEMPLATE_ID)
        else:
            near = [{"name": r["reference"], "category": r.get("category"),
                     "readiness": r.get("readiness"), "license": r.get("reuse_policy"),
                     "score": r.get("quality_score")}
                    for r in reviews if "oscillo" in r["reference"].lower()
                    or r.get("category") == "instrument"]
            needs_research.append("No eligible candidate; review gates: " +
                                  json.dumps(near[:5], ensure_ascii=False))
    else:
        # Preserve reviewed RTL/design and do not overwrite existing implementation.
        needs_research.append("Template already exists: regenerate and regress existing project")
    if not created:
        design_only = create_design_only_capstone(proposals)
        if design_only:
            created.append(design_only)
            needs_research.append("New capstone is a design brief only; no RTL test claim.")
    if not created:
        raise RuntimeError(
            "Required >=1 new capstone per factory cycle, but no eligible unique "
            "proposal or first-party template remains. Add vetted candidates; "
            "never duplicate old projects or fake verification."
        )
    history = {"schema_version": 1, "runs": (old.get("runs", []) + [{
        "timestamp": now.isoformat(), "new_projects": created,
        "reviewed_existing": sorted(p.parent.name for p in
            (ROOT / "capstones").glob("*/design.json")),
        "notes": needs_research
    }])[-240:]}
    FACTORY_HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    return history["runs"][-1]


def main():
    report = run()
    print("FACTORY created:", report["new_projects"],
          "existing:", len(report["reviewed_existing"]),
          "notes:", report["notes"])


if __name__ == "__main__":
    main()
