"""Validate generated capstone structure; run HDL/C tests when tools exist."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .generate import ROOT, SITE, safe_local, validate_design


def run_command(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=50, check=False)
    return {"command": cmd, "returncode": p.returncode,
            "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]}


def validate_project(folder):
    design = json.loads((folder / "design.json").read_text(encoding="utf-8"))
    validate_design(design, folder)
    output = SITE / "capstones" / design["id"]
    if not output.exists():
        raise FileNotFoundError("Generate site first: python3 -m harness.generate")
    manifest = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["source_files"]:
        src = safe_local(folder, item["path"])
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise ValueError("Generated source is stale: " + item["path"])

    report = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "static_design": "pass", "rtl_simulation": "not_run",
        "software_test": "not_run", "synthesis": "not_run",
        "implementation": "not_run", "timing": "not_run",
        "board_test": "not_run", "evidence": []}
    with tempfile.TemporaryDirectory() as tmp:
        if shutil.which("iverilog") and shutil.which("vvp"):
            out = str(Path(tmp) / "fan_tb.vvp")
            compilation = run_command(["iverilog", "-g2012", "-s", "tb_smart_fan_peripheral",
                "-o", out, str(folder / "rtl/smart_fan_peripheral.v"),
                str(folder / "tb/tb_smart_fan_peripheral.v")])
            report["evidence"].append(compilation)
            if compilation["returncode"] == 0:
                execution = run_command(["vvp", out])
                report["evidence"].append(execution)
                report["rtl_simulation"] = ("pass" if execution["returncode"] == 0
                                           and "PASS smart_fan_peripheral" in execution["stdout"]
                                           else "fail")
            else:
                report["rtl_simulation"] = "fail"
        if shutil.which("cc"):
            out = str(Path(tmp) / "fan_mmio_test")
            comp = run_command(["cc", "-std=c11", "-Wall", "-Wextra",
                "-DFAN_MMIO_SELFTEST", str(folder / "sw/fan_mmio.c"), "-o", out])
            report["evidence"].append(comp)
            if comp["returncode"] == 0:
                run = run_command([out])
                report["evidence"].append(run)
                report["software_test"] = ("pass" if run["returncode"] == 0
                                            and "PASS fan_mmio" in run["stdout"] else "fail")
            else:
                report["software_test"] = "fail"
    (output / "verification.json").write_text(json.dumps(
        report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if "fail" in (report["rtl_simulation"], report["software_test"]):
        raise RuntimeError("Simulation or C test failed: " + design["id"])
    return report


def main():
    for design in sorted((ROOT / "capstones").glob("*/design.json")):
        result = validate_project(design.parent)
        print(design.parent.name, "RTL:", result["rtl_simulation"],
              "C:", result["software_test"], "BOARD:", result["board_test"])


if __name__ == "__main__":
    main()
