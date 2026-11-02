"""Generate non-executable design *proposals* from catalog metadata."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "motor": ("sensor_input", "motor_pwm", "encoder_counter", "control_fsm"),
    "sensor": ("sensor_interface", "sample_register", "uart_status"),
    "video": ("camera_capture", "frame_buffer", "filter_pipeline", "video_output"),
    "instrument": ("signal_sampler", "trigger", "capture_ram", "uart_readout"),
    "communication": ("uart_spi_i2c_controller", "register_bank", "interrupt_status"),
    "security": ("byte_stream", "crypto_accelerator", "result_register"),
}


def build_proposals(catalog):
    proposals = []
    for item in catalog.get("results", []):
        category = item["vendor_hint"]
        proposals.append({
            "id": item["id"], "reference": item["repository"], "source_url": item["url"],
            "source_tree_sha": item.get("source_tree_sha"),
            "license_spdx": item["license_spdx"], "reuse_policy": item["reuse_policy"],
            "profile": category, "suggested_ip": list(PROFILES.get(category, ())),
            "target_board": "UNASSIGNED", "approval_state": "pending_review",
            "rtl_source_status": "not_ported",
            "design_basis": "metadata_heuristic_only",
            "must_check": ["IO voltage and wiring", "pin constraints", "clock/reset",
                           "protocol timing", "RTL license", "module testbench",
                           "synthesis/implementation/board evidence"]})
    return {"schema_version": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "proposals": proposals}


def main():
    catalog = json.loads((ROOT / "catalog/discovered.json").read_text(encoding="utf-8"))
    result = build_proposals(catalog)
    (ROOT / "catalog/proposals.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Generated", len(result["proposals"]), "draft profiles")


if __name__ == "__main__":
    main()
