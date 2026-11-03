"""Mandatory V/S/O publication audit for every generated FPGA SoC capstone.

V: rendered SVG matches Design IR module IDs and connection count.
S: complete sections, structured signals/BOM/evidence and honest statuses.
O: course navigation and all project index links remain connected.
This audit is read-only; no RTL or board evidence is fabricated or modified.
"""
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .generate import ROOT, SITE


def audit(root=ROOT, site=SITE):
    errors = []
    projects = sorted((root / "capstones").glob("*/design.json"))
    home = site / "index.html"
    catalog = site / "capstones/index.html"
    if not home.is_file() or not catalog.is_file():
        return ["Missing main or capstone HTML catalog"]
    home_text = home.read_text(encoding="utf-8")
    catalog_text = catalog.read_text(encoding="utf-8")
    for design_path in projects:
        try:
            design = json.loads(design_path.read_text(encoding="utf-8"))
            pid = design["id"]
            dest = site / "capstones" / pid
            required = ("index.html", "system.svg", "design.json", "connections.json",
                        "bom.csv", "source_manifest.json", "verification.json",
                        "source_bundle.zip")
            for name in required:
                if not (dest / name).is_file():
                    errors.append(pid + ": missing structured publication artifact " + name)
            if not all((dest / name).is_file() for name in required):
                continue

            # V: use deterministic XML, not an unverified AI drawing.
            svg = ET.parse(dest / "system.svg")
            texts = " ".join(x.text or "" for x in svg.findall(".//{*}text"))
            if len(svg.findall(".//{*}rect")) < len(design["modules"]):
                errors.append(pid + ": SVG missing module blocks")
            if len(svg.findall(".//{*}line")) < len(design["connections"]):
                errors.append(pid + ": SVG missing connection arrows")
            for module in design["modules"]:
                if module["id"] not in texts or module["name"] not in texts:
                    errors.append(pid + ": SVG module labels drift: " + module["id"])

            # S: structure and validation stages must match the canonical IR.
            published = json.loads((dest / "design.json").read_text(encoding="utf-8"))
            wiring = json.loads((dest / "connections.json").read_text(encoding="utf-8"))
            manifest = json.loads((dest / "source_manifest.json").read_text(encoding="utf-8"))
            status = json.loads((dest / "verification.json").read_text(encoding="utf-8"))
            if published != design:
                errors.append(pid + ": published Design IR differs from source")
            if wiring.get("modules") != design["modules"] or wiring.get("connections") != design["connections"]:
                errors.append(pid + ": connection table differs from source Design IR")
            if manifest.get("design_id") != pid:
                errors.append(pid + ": source manifest ID mismatch")
            if len(manifest.get("source_files", [])) != len(design["source_files"]):
                errors.append(pid + ": source manifest incomplete")
            with (dest / "bom.csv").open(encoding="utf-8", newline="") as stream:
                header = csv.reader(stream).__next__()
            if header != ["part", "quantity", "interface", "notes"]:
                errors.append(pid + ": BOM schema mismatch")
            for key in ("rtl_simulation", "software_test", "synthesis",
                        "implementation", "timing", "board_test"):
                if status.get(key) not in ("pass", "fail", "not_run", "skip"):
                    errors.append(pid + ": missing/invalid verification status " + key)

            page = (dest / "index.html").read_text(encoding="utf-8")
            if '<img class="diagram" src="system.svg"' not in page:
                errors.append(pid + ": no rendered SVG visible in HTML")
            if page.count("<table") < 3:
                errors.append(pid + ": missing module, connection or verification tables")
            for section in ("overview", "diagram", "signals", "hardware",
                            "source", "verification", "provenance"):
                if f'id="{section}"' not in page:
                    errors.append(pid + ": missing HTML section " + section)
            for asset in ("system.svg", "connections.json", "design.json",
                          "verification.json", "source_bundle.zip"):
                if asset not in page:
                    errors.append(pid + ": missing link to " + asset)

            # O: both main page and category page must navigate to this capstone.
            target = pid + "/index.html"
            if "capstones/" + target not in home_text or target not in catalog_text:
                errors.append(pid + ": missing main/category catalog navigation")
            if 'href="../index.html"' not in page or 'href="../../index.html"' not in page:
                errors.append(pid + ": missing back navigation")
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError, StopIteration) as exc:
            errors.append(design_path.parent.name + ": publication gate exception: " + str(exc))
    if not projects:
        errors.append("No capstones found for publication")
    return errors


def main():
    problems = audit()
    count = len(list((ROOT / "capstones").glob("*/design.json")))
    print(f"PUBLICATION V/S/O GATE: projects={count}, errors={len(problems)}")
    for issue in problems:
        print("::error::" + issue)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
