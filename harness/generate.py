"""Render standalone HTML/SVG/netlist and copy only local approved source files."""
import csv
import hashlib
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def esc(obj):
    return html.escape(str(obj), quote=True)


def page(title, content, relative_home="index.html"):
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + esc(title) + """</title><style>
:root{color-scheme:light}body{font:16px/1.65 system-ui,sans-serif;background:#f5f7fa;color:#1e293b;margin:0}
header{background:#163b5b;color:white;padding:16px max(16px,calc((100vw - 980px)/2))}
header a{color:#fff}main{max-width:980px;margin:auto;padding:24px 16px 80px}
section{background:white;border:1px solid #dce4ed;border-radius:12px;padding:20px;margin:18px 0}
h1,h2,h3{line-height:1.3}table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{border:1px solid #dce4ed;padding:8px;text-align:left;vertical-align:top}
th{background:#edf3f7}.scroll{overflow-x:auto}a{color:#1263a1}
small,.muted{color:#607086}svg{max-width:100%;height:auto}code{background:#eef2f7;padding:2px 5px}
.warning{border-left:4px solid #a36b1f;padding-left:12px}
</style></head><body><header><a href="""" + esc(relative_home) + """">FPGA SoC Capstone Harness</a></header>
<main>""" + content + "</main></body></html>"


def table(headers, rows):
    head = "".join("<th>" + esc(h) + "</th>" for h in headers)
    body = "".join("<tr>" + "".join("<td>" + c + "</td>" for c in row) + "</tr>" for row in rows)
    return '<div class="scroll"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>"


def safe_local(base, relative):
    p = (base / relative).resolve()
    if not p.is_relative_to(base.resolve()) or not p.is_file():
        raise ValueError("Missing or unsafe source path: " + relative)
    return p


def validate_design(design, base):
    nodes = {m["id"]: m for m in design["modules"]}
    if len(nodes) != len(design["modules"]):
        raise ValueError("Duplicate module ID")
    for net in design["connections"]:
        for endpoint, direction in (("from", "outputs"), ("to", "inputs")):
            node, sep, port = net[endpoint].partition(".")
            if not sep or node not in nodes or port not in nodes[node][direction]:
                raise ValueError("Invalid " + endpoint + " port " + net[endpoint])
    for path in design["source_files"]:
        safe_local(base, path)


def svg_diagram(design):
    nodes = design["modules"]
    positions = {n["id"]: (20 + (i % 2) * 320, 24 + (i // 2) * 118)
                 for i, n in enumerate(nodes)}
    height = 48 + ((len(nodes) + 1) // 2) * 118
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 ' + str(height) +
             '" role="img" aria-label="Structured SoC block diagram">',
             '<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="#6b8197"/></marker></defs>']
    for net in design["connections"]:
        src = net["from"].split(".", 1)[0]
        dst = net["to"].split(".", 1)[0]
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        label = esc(net["from"] + " → " + net["to"])
        parts.append('<line x1="' + str(x1+140) + '" y1="' + str(y1+25) +
                     '" x2="' + str(x2+140) + '" y2="' + str(y2+25) +
                     '" stroke="#8296ab" stroke-width="1.3" marker-end="url(#arrow)"><title>' +
                     label + '</title></line>')
    for m in nodes:
        x, y = positions[m["id"]]
        parts.append(f'<rect x="{x}" y="{y}" width="280" height="52" rx="7" fill="#e6f0fa" stroke="#4277a8"/>')
        parts.append(f'<text x="{x+12}" y="{y+22}" fill="#173b58" font-size="14" font-weight="600">{esc(m["name"])}</text>')
        parts.append(f'<text x="{x+12}" y="{y+40}" fill="#47657c" font-size="11">{esc(m["id"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_capstone(folder):
    design = json.loads((folder / "design.json").read_text(encoding="utf-8"))
    validate_design(design, folder)
    dest = SITE / "capstones" / design["id"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "system.svg").write_text(svg_diagram(design), encoding="utf-8")
    (dest / "connections.json").write_text(json.dumps(
        {"schema_version": 1, "modules": design["modules"],
         "connections": design["connections"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (dest / "bom.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["part", "quantity", "interface", "notes"])
        writer.writeheader()
        for part in design.get("bom", []):
            writer.writerow({k: part.get(k, "") for k in writer.fieldnames})
    sources = []
    for relative in design["source_files"]:
        path = safe_local(folder, relative)
        out = dest / "source" / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, out)
        sources.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "origin": "first_party_local"})
    (dest / "source_manifest.json").write_text(json.dumps(
        {"design_id": design["id"], "source_files": sources}, indent=2) + "\n", encoding="utf-8")
    status_path = dest / "verification.json"
    # Do not erase a real test result when regenerating documentation.
    if not status_path.exists():
        status_path.write_text(json.dumps({
            "static_design": "generated", "rtl_simulation": "not_run",
            "synthesis": "not_run", "implementation": "not_run", "board_test": "not_run",
            "evidence": []}, indent=2) + "\n", encoding="utf-8")
    module_rows = [[esc(m["id"]), esc(m["name"]), esc(", ".join(m["inputs"])),
                    esc(", ".join(m["outputs"]))] for m in design["modules"]]
    net_rows = [[esc(n["from"]), esc(n["to"]), esc(n.get("note", ""))]
                for n in design["connections"]]
    file_rows = [[f'<a href="source/{esc(p)}">{esc(p)}</a>'] for p in design["source_files"]]
    bom_rows = [[esc(p.get(k, "")) for k in ("part", "quantity", "interface", "notes")]
                for p in design.get("bom", [])]
    content = "<h1>" + esc(design["title"]) + "</h1><p>" + esc(design["summary"]) + "</p>"
    content += '<section><h2>구조도 · 실제 포트명 기준</h2><img src="system.svg" alt="SoC block diagram">'
    content += '<p><a href="connections.json">기계 판독 가능한 접속 계통도 JSON</a></p>'
    content += table(["모듈 ID", "코드 모듈 / IP", "입력", "출력"], module_rows) + "</section>"
    content += "<section><h2>신호 연결표</h2>" + table(["출발", "도착", "연결 유의"], net_rows) + "</section>"
    content += "<section><h2>실행소스</h2>" + table(["파일"], file_rows) + "</section>"
    content += "<section><h2>하드웨어 / BOM</h2>" + table(
        ["부품", "수량", "인터페이스", "설명"], bom_rows) + '<p><a href="bom.csv">BOM.csv 다운로드</a></p></section>'
    content += '<section><h2>검증 및 제약</h2><p class="warning">' + esc(
        design["verification_notice"]) + '</p><p><a href="verification.json">현재 검증 결과 보기</a></p>'
    content += "<p>" + esc(design["safety_notice"]) + "</p></section>"
    content += '<section><h2>참고 출처</h2><p>' + esc(design["provenance"]) + "</p></section>"
    (dest / "index.html").write_text(page(design["title"], content, "../../index.html"), encoding="utf-8")
    return design


def main():
    SITE.mkdir(exist_ok=True)
    catalog = json.loads((ROOT / "catalog/discovered.json").read_text(encoding="utf-8"))
    dirs = sorted((ROOT / "capstones").glob("*/design.json"))
    designs = [render_capstone(path.parent) for path in dirs]
    from .draft import render_drafts
    proposal_file = ROOT / "catalog/proposals.json"
    proposals = json.loads(proposal_file.read_text(encoding="utf-8"))
    draft_rows = render_drafts(proposals.get("proposals", []))
    rows = [[f'<a href="capstones/{esc(d["id"])}/index.html">{esc(d["title"])}</a>',
             esc(d["board"]), esc(d["status"])] for d in designs]
    reference_rows = []
    for item in catalog.get("results", []):
        safe_url = item["url"] if item["url"].startswith("https://github.com/") else "#"
        reference_rows.append([f'<a rel="noopener" href="{esc(safe_url)}">{esc(item["repository"])}</a>',
                               esc(item["vendor_hint"]), esc(item["license_spdx"]),
                               esc(item["reuse_policy"]), esc(item["score"])])
    content = "<h1>FPGA SoC 주변장치·캡스톤 자료실</h1>"
    content += "<p>조사 자료, 검토 제안, 자체 제작 RTL 및 검증을 구분합니다. 검색 결과의 동작은 검증되지 않았습니다.</p>"
    content += "<section><h2>실습 캡스톤</h2>" + table(
        ["과제", "대상", "상태"], rows) + "</section>"
    content += "<section><h2>자동 변환된 설계 구상도 (원본 RTL 미포팅)</h2>" + table(
        ["후보 소스", "구상 유형", "승인 단계"], draft_rows) + "</section>"
    content += "<section><h2>자동 수집 참고자료</h2><p>GitHub 소스 미복제 · 기초 검색 근거</p>" + table(
        ["공개 원본", "유형(추정)", "SPDX", "재사용 정책", "자료 점수"], reference_rows) + "</section>"
    (SITE / "index.html").write_text(page("FPGA SoC Capstone Harness", content), encoding="utf-8")
    print("Generated HTML for", len(designs), "capstone(s) and", len(reference_rows), "references")


if __name__ == "__main__":
    main()
