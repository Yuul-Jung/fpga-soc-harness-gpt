"""Reproducible first-party RTL and C tests with per-capstone test specs."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .generate import ROOT, SITE, safe_local, validate_design

DEFAULT_FAN_TEST = {
    "rtl_top": "tb_smart_fan_peripheral",
    "rtl_files": ["rtl/smart_fan_peripheral.v", "tb/tb_smart_fan_peripheral.v"],
    "rtl_success": "PASS smart_fan_peripheral",
    "c_file": "sw/fan_mmio.c",
    "c_define": "FAN_MMIO_SELFTEST",
    "c_success": "PASS fan_mmio self-test",
}


def run_command(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    return {"command": cmd, "returncode": p.returncode,
            "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]}


def validate_project(folder):
    design = json.loads((folder / "design.json").read_text(encoding="utf-8"))
    validate_design(design, folder)
    out = SITE / "capstones" / design["id"]
    if not out.is_dir():
        raise FileNotFoundError("Run python3 -m harness.generate first")
    manifest = json.loads((out / "source_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["source_files"]:
        src = safe_local(folder, item["path"])
        if hashlib.sha256(src.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Published source hash drift: " + item["path"])
    test = design.get("test_spec")
    if test is None and design["id"] == "smart_fan":
        test = DEFAULT_FAN_TEST
    prior_path = out / "verification.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else {}
    # Manual physical verification is never inferred or overwritten by a CI rerun.
    preserved = {k: prior[k] for k in ("manual_board_evidence", "manual_timing_report")
                 if k in prior}
    report = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "static_design": "pass", "rtl_simulation": "not_run",
        "software_test": "not_run", "synthesis": "not_run",
        "implementation": "not_run", "timing": "not_run",
        "board_test": "not_run", "evidence": [], **preserved}
    if test:
        with tempfile.TemporaryDirectory() as tmp:
            if shutil.which("iverilog") and shutil.which("vvp"):
                exe = str(Path(tmp) / "project.vvp")
                cmd = ["iverilog", "-g2012", "-s", test["rtl_top"], "-o", exe]
                cmd += [str(safe_local(folder, p)) for p in test["rtl_files"]]
                comp = run_command(cmd)
                report["evidence"].append(comp)
                if comp["returncode"] == 0:
                    run = run_command(["vvp", exe])
                    report["evidence"].append(run)
                    report["rtl_simulation"] = (
                        "pass" if run["returncode"] == 0
                        and test["rtl_success"] in run["stdout"] else "fail")
                else:
                    report["rtl_simulation"] = "fail"
            if shutil.which("cc"):
                exe = str(Path(tmp) / "project_sw")
                cmd = ["cc", "-std=c11", "-Wall", "-Wextra", "-D" + test["c_define"],
                       str(safe_local(folder, test["c_file"])), "-o", exe]
                comp = run_command(cmd)
                report["evidence"].append(comp)
                if comp["returncode"] == 0:
                    run = run_command([exe])
                    report["evidence"].append(run)
                    report["software_test"] = (
                        "pass" if run["returncode"] == 0
                        and test["c_success"] in run["stdout"] else "fail")
                else:
                    report["software_test"] = "fail"
    prior_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    if "fail" in (report["rtl_simulation"], report["software_test"]):
        raise RuntimeError("First-party simulation or C self-test failed: " + design["id"])
    return report


def main():
    for path in sorted((ROOT / "capstones").glob("*/design.json")):
        report = validate_project(path.parent)
        print("VALIDATE", path.parent.name, "RTL:", report["rtl_simulation"],
              "C:", report["software_test"], "BOARD:", report["board_test"])


if __name__ == "__main__":
    main()
