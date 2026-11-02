"""Turn researched candidate profiles into clearly marked *conceptual* Design IR drafts.

No third-party code is copied and no proposed port is represented as a verified HDL port.
"""
import json
from pathlib import Path
import re

from .generate import ROOT, SITE, esc, page, svg_diagram, table


def make_draft(proposal):
    raw = proposal["id"].lower()
    ident = re.sub(r"[^a-z0-9_-]", "-", raw)[:100].strip("-")
    if not ident:
        raise ValueError("Invalid proposed project ID")
    names = proposal["suggested_ip"]
    modules = []
    nets = []
    for i, name in enumerate(names):
        mid = re.sub(r"[^a-z0-9_]", "_", name.lower())
        modules.append({"id": mid, "name": name,
                        "inputs": ["in_data"] if i else [],
                        "outputs": ["out_data"] if i < len(names)-1 else []})
        if i:
            nets.append({"from": modules[i-1]["id"] + ".out_data",
                         "to": mid + ".in_data",
                         "note": "Conceptual link only, not an actual RTL signal"})
    return {
        "schema_version": 1, "id": ident, "source_url": proposal["source_url"],
        "source_tree_sha": proposal.get("source_tree_sha"),
        "license_spdx": proposal["license_spdx"],
        "reuse_policy": proposal["reuse_policy"],
        "status": "CONCEPT_ONLY_NOT_PORTED",
        "hardware_board": "UNASSIGNED",
        "source_code_included": False,
        "modules": modules, "connections": nets,
        "warning": "These names and connections are educational architecture proposals, not verified upstream source modules or physical wires."
    }


def render_drafts(proposals):
    links = []
    for p in proposals:
        design = make_draft(p)
        out = SITE / "drafts" / design["id"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "design_draft.json").write_text(
            json.dumps(design, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "concept.svg").write_text(svg_diagram(design), encoding="utf-8")
        url = p["source_url"]
        external = url if url.startswith("https://github.com/") else "#"
        body = "<h1>" + esc(p["reference"]) + "</h1>"
        body += '<section><h2>참고 원본</h2><p><a rel="noopener" href="' + esc(external) + '">' + esc(url) + '</a></p>'
        body += '<p>Source tree SHA: <code>' + esc(p.get("source_tree_sha")) + "</code></p>"
        body += "<p>라이선스: " + esc(p["license_spdx"]) + " / " + esc(p["reuse_policy"]) + "</p></section>"
        body += '<section><h2>자동 생성한 설계 구상도 (미검증)</h2><p class="warning">' + esc(design["warning"]) + '</p>'
        body += '<img src="concept.svg" alt="Concept-only architecture">'
        body += '<p><a href="design_draft.json">Design IR 초안 JSON</a></p>'
        body += table(["제안 IP", "개념 입력", "개념 출력"], [
            [esc(m["name"]), esc(", ".join(m["inputs"])), esc(", ".join(m["outputs"]))]
            for m in design["modules"]]) + "</section>"
        body += '<section><h2>진행 상태</h2><p>대상 보드 미선정 / 원본 포팅 미실시 / RTL 미생성 / 회로 배선 및 보드 검증 미실시</p></section>'
        (out / "index.html").write_text(page(
            p["reference"] + " draft", body, "../../index.html"), encoding="utf-8")
        links.append([f'<a href="drafts/{esc(design["id"])}/index.html">{esc(p["reference"])}</a>',
                      esc(p["profile"]), esc(p["approval_state"])])
    return links


def main():
    from .generate import main as generate
    generate()


if __name__ == "__main__":
    main()
