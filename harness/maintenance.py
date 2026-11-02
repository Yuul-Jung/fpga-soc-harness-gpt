"""Every two/four hours: inspect *all previous* artifacts, regenerate safe views,
retest existing first-party RTL, and report failures without changing source RTL.
"""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

from .generate import ROOT, SITE, main as regenerate
from .validate import validate_project
from .research import load

REPORT = ROOT / "catalog/material_audit.json"
HISTORY = ROOT / "catalog/material_audit_history.json"


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        attr = "href" if tag == "a" else "src" if tag in ("img", "script") else None
        if attr and props.get(attr):
            self.refs.append(props[attr])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def surface_manifest():
    if not SITE.is_dir():
        return {}
    return {str(p.relative_to(SITE)): sha(p)
            for p in SITE.rglob("*") if p.is_file()
            and p.name != "verification.json"}


def inspect_site():
    errors = []
    items = 0
    if not (SITE / "index.html").exists():
        errors.append("site/index.html missing")
        return errors, items
    for htmlfile in SITE.rglob("*.html"):
        items += 1
        p = LocalLinks()
        try:
            p.feed(htmlfile.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            errors.append(str(htmlfile.relative_to(ROOT)) + ": " + str(exc))
            continue
        for value in p.refs:
            u = urllib.parse.urlsplit(value)
            if u.scheme or u.netloc or not u.path or value.startswith("#"):
                continue
            linked = (htmlfile.parent / urllib.parse.unquote(u.path)).resolve()
            if not linked.is_relative_to(SITE.resolve()) or not linked.exists():
                errors.append(str(htmlfile.relative_to(SITE)) + " broken link: " + value)
    for f in SITE.rglob("*.svg"):
        items += 1
        try:
            ET.parse(f)
        except ET.ParseError as exc:
            errors.append("invalid SVG " + str(f.relative_to(SITE)) + ": " + str(exc))
    for f in SITE.rglob("connections.json"):
        items += 1
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            nodes = {m["id"]: m for m in j["modules"]}
            for net in j["connections"]:
                for role, direction in (("from", "outputs"), ("to", "inputs")):
                    mid, port = net[role].split(".", 1)
                    if mid not in nodes or port not in nodes[mid][direction]:
                        errors.append(str(f.relative_to(SITE)) + " invalid link: " + net[role])
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(str(f.relative_to(SITE)) + ": " + str(exc))
    return errors, items


def perform(stage="review", now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    before = surface_manifest()
    # Safe repair: regenerate *only* HTML/SVG/JSON/BOM and first-party copies
    # using approved local design.json, without touching source RTL/design.
    regenerate()
    after = surface_manifest()
    repaired_or_updated = [p for p in after if before.get(p) != after[p]]
    problems, html_svg_items = inspect_site()
    capstone_results = []
    for path in sorted((ROOT / "capstones").glob("*/design.json")):
        try:
            result = validate_project(path.parent)
            capstone_results.append({
                "id": path.parent.name, "rtl": result["rtl_simulation"],
                "software": result["software_test"], "board": result["board_test"],
                "result": "pass" if result["static_design"] == "pass"
                and result["rtl_simulation"] != "fail"
                and result["software_test"] != "fail" else "fail"})
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            problems.append("capstone " + path.parent.name + ": " + str(exc))
            capstone_results.append({"id": path.parent.name, "result": "fail"})
    report = {
        "schema_version": 1, "stage": stage, "timestamp": now.isoformat(),
        "existing_capstones_rechecked": len(capstone_results),
        "pages_and_diagrams_checked": html_svg_items,
        "generated_outputs_regenerated": len(repaired_or_updated),
        "changed_generated_paths": repaired_or_updated[:100],
        "source_rtl_modified": False,
        "capstones": capstone_results, "errors": problems,
        "status": "PASS" if not problems else "FAIL",
        "next_improvements": [
            "Verify real hardware pin maps and IO voltage before board experiment",
            "Add board-specific Vivado/Quartus/Radiant synthesis evidence",
            "Do not change first-party RTL without a reviewed PR"
        ]
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    old = load(HISTORY, {"runs": []})
    HISTORY.write_text(json.dumps({
        "schema_version": 1,
        "runs": (old["runs"] + [{
            "timestamp": now.isoformat(), "stage": stage,
            "status": report["status"], "existing_capstones": len(capstone_results),
            "errors": problems, "generated_outputs_regenerated": len(repaired_or_updated)
        }])[-240:]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if problems:
        raise RuntimeError("Existing source/document/diagram audit failed: " + "; ".join(problems[:5]))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["research", "review", "factory"], default="review")
    args = parser.parse_args()
    report = perform(stage=args.stage)
    print("MAINTENANCE", report["status"], "capstones:",
          report["existing_capstones_rechecked"], "HTML/SVG:",
          report["pages_and_diagrams_checked"], "regenerated:",
          report["generated_outputs_regenerated"])


if __name__ == "__main__":
    main()
