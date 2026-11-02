"""Biennial-hour source *metadata* audit, improvement plan and gate assessment.

No remote RTL code or third-party build scripts are executed. Source-file
presence is evidence only, never a functional/board validation result.
"""
import datetime as dt
import json
import re
from pathlib import Path
import urllib.error
import urllib.parse

from .discover import ROOT, POLICY, api, license_policy
from .research import load

CATALOG = ROOT / "catalog/discovered.json"
REPORT = ROOT / "catalog/reviewed.json"
BACKLOG = ROOT / "catalog/improvement_backlog.json"
KNOWN_BOARD = (
    ("basys3", "Basys3", "AMD/Xilinx"),
    ("zybo", "Zybo", "AMD/Xilinx"),
    ("arty", "Arty", "AMD/Xilinx"),
    ("de10", "DE10", "Intel/Altera"),
    ("de1_soc", "DE1-SoC", "Intel/Altera"),
    ("de1-soc", "DE1-SoC", "Intel/Altera"),
    ("ulx3s", "ULX3S", "Lattice"),
    ("ecp5", "ECP5", "Lattice"),
    ("ice40", "iCE40", "Lattice"),
)
KEYS = {
    "motor": ("motor", "pwm", "servo", "encoder", "stepper", "robot", "pid"),
    "sensor": ("sensor", "distance", "ultrasonic", "humidity", "temperature", "adc"),
    "instrument": ("oscilloscope", "logic analyzer", "analyzer", "capture", "spectr", "counter"),
    "video": ("video", "vga", "ov7670", "camera", "frame", "sobel", "hdmi"),
    "communication": ("spi", "uart", "i2c", "ethernet", "axi", "avalon", "rs485"),
    "security": ("aes", "crypto", "security", "rfid", "encrypt", "trng"),
    "automation": ("home", "greenhouse", "irrigation", "automation", "parking", "relay")
}


def guess_family(item):
    text = (" ".join([item.get("repository", ""), item.get("description", "")]
                   + item.get("evidence", {}).get("hdl_examples", [])
                   + item.get("evidence", {}).get("evidence_files", []))).lower()
    for marker, name, vendor in KNOWN_BOARD:
        if marker in text:
            return name, vendor, "evidence_filename_or_description"
    return (item.get("board_hint") or "UNSPECIFIED",
            item.get("vendor_family") or "UNSPECIFIED", "research_hint_unverified")


def classify(item):
    # Repository purpose is more informative than filenames of generic IP
    # components. Example: adc.v in an oscilloscope should not turn the
    # whole project into a sensor-interface project.
    main = (item.get("repository", "") + " " +
            item.get("description", "")).lower()
    files = " ".join(item.get("evidence", {}).get("hdl_examples", [])).lower()
    strengths = {domain: sum((3 if term in main else 0)
                              + (1 if term in files else 0)
                              for term in terms) for domain, terms in KEYS.items()}
    best = max(strengths, key=strengths.get)
    if strengths[best] == 0:
        return item.get("vendor_hint") or "unknown", 0, "query_hint_only"
    return best, strengths[best], "file_and_description_keywords"


def audit(item, remote_status="not_checked", now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    ev = item.get("evidence") or {}
    hdl = int(ev.get("hdl_count", 0))
    doc = any("readme" in p.lower() or "report" in p.lower()
              for p in ev.get("evidence_files", []))
    constraints = bool(ev.get("has_constraints"))
    tb = bool(ev.get("has_testbench"))
    domain, strength, basis = classify(item)
    board, family, board_basis = guess_family(item)
    license_id = item.get("license_spdx") or "UNKNOWN"
    good_license = license_policy(license_id) == "review_for_reuse"
    score = min(100, hdl * 2, 20) + (20 if constraints else 0) + (
        20 if tb else 0) + (15 if doc else 0) + (15 if strength >= 2 else 0) + (
        10 if good_license else 0)
    improvements = []
    if not constraints:
        improvements.append("Find trustworthy board master pin constraints; do not invent pins")
    if not tb:
        improvements.append("Create first-party self-checking simulation tests")
    if not doc:
        improvements.append("Collect independent interface, wiring and timing documentation")
    if not good_license:
        improvements.append("Keep upstream as reference-only until SPDX/redistribution review")
    if strength < 2:
        improvements.append("Check application/CPU-centric classification by reading actual files")
    if board_basis != "evidence_filename_or_description":
        improvements.append("Confirm exact FPGA board, clock and IO voltage")
    improvements += ["Extract port widths and reset polarity before RTL adaptation",
                     "Separate RTL simulation, synthesis, timing and physical board evidence"]
    has_qualifying_metadata = hdl > 0 and doc and strength > 0
    can_propose = has_qualifying_metadata and remote_status != "upstream_changed"
    return {
        "id": item["id"], "reference": item["repository"], "source_url": item["url"],
        "source_tree_sha": item.get("source_tree_sha"), "checked_at": now.isoformat(),
        "board": board, "board_basis": board_basis, "vendor_family": family,
        "category": domain, "category_strength": strength,
        "category_basis": basis, "license_spdx": license_id,
        "reuse_policy": license_policy(license_id), "rtl_files": hdl,
        "has_constraints": constraints, "has_testbench": tb, "has_documentation": doc,
        "quality_score": score, "remote_tree_status": remote_status,
        "readiness": "metadata_reviewed_for_design_proposal" if can_propose else "needs_research",
        "source_rtl_tested": False, "board_tested": False,
        "improvements": improvements}


def review(offline=False, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    catalog = load(CATALOG, {"results": []})
    prior = load(REPORT, {"reviews": []})
    older = {r["reference"].lower(): r for r in prior.get("reviews", [])}
    items = catalog.get("results", [])
    # Check remote heads of the most recently discovered/least-audited candidates.
    # Fair rotation: revisit the repositories checked longest ago first.
    ordered = sorted(items, key=lambda x: (
        older.get(x["repository"].lower(), {}).get("upstream_verified_at") or "",
        -x.get("score", 0), x["repository"].lower()))
    remote_states = {}
    remote_checked = set()
    remote_errors = []
    if not offline:
        for item in ordered[:min(8, len(ordered))]:
            repo = item["repository"]
            branch = item.get("default_branch") or "main"
            url = ("https://api.github.com/repos/" + urllib.parse.quote(repo, safe="/")
                   + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1")
            try:
                tree = api(url)
                remote_states[repo.lower()] = (
                    "upstream_changed" if tree.get("sha") != item.get("source_tree_sha")
                    else "source_tree_sha_confirmed")
                remote_checked.add(repo.lower())
            except (urllib.error.URLError, ValueError, KeyError) as exc:
                remote_states[repo.lower()] = "verification_unavailable"
                remote_errors.append({"repository": repo, "error": type(exc).__name__})
    reviews = []
    for item in items:
        key = item["repository"].lower()
        state = remote_states.get(key, older.get(key, {}).get("remote_tree_status", "not_checked"))
        entry = audit(item, remote_status=state, now=now)
        entry["upstream_verified_at"] = (
            now.isoformat() if key in remote_checked
            else older.get(key, {}).get("upstream_verified_at"))
        reviews.append(entry)
    reviews.sort(key=lambda x: (-x["quality_score"], x["reference"].lower()))
    audits = {"schema_version": 1, "generated_at": now.isoformat(),
              "metadata_only": True, "remote_audit_errors": remote_errors,
              "reviews": reviews}
    backlog = {"schema_version": 1, "generated_at": now.isoformat(), "actions": [
        {"reference": r["reference"], "quality_score": r["quality_score"],
         "readiness": r["readiness"], "tasks": r["improvements"]}
        for r in reviews]}
    return audits, backlog


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    audited, improvements = review(offline=args.offline)
    REPORT.write_text(json.dumps(audited, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    BACKLOG.write_text(json.dumps(improvements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("REVIEW", len(audited["reviews"]), "source audits;",
          len(audited["remote_audit_errors"]), "remote errors; RTL not executed")


if __name__ == "__main__":
    main()
