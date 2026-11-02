"""Render standalone HTML/SVG/netlist and copy only local approved source files."""
import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def esc(obj):
    return html.escape(str(obj), quote=True)


def page(title, content, relative_home="index.html", sidebar_links=None):
    """Self-contained responsive textbook page, with visible navigation."""
    items = sidebar_links or [
        ("전체 자료실", relative_home), ("캡스톤 과제", relative_home + "#capstones"),
        ("설계 구상", relative_home + "#drafts"),
        ("참고 소스", relative_home + "#references")]
    nav = "".join(
        '<a href="' + esc(url) + '">' + esc(label) + '</a>'
        for label, url in items)
    css = """<style>
:root{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;color-scheme:light}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#f5f7fa;color:#192e45;font-size:15px;line-height:1.7}
a{color:#12639f;text-decoration:none}a:hover{text-decoration:underline}
header{background:#183b58;color:#fff;padding:13px 20px;position:sticky;top:0;z-index:5}
header a{color:#fff;font-weight:700}header small{font-weight:400;color:#cfdfec;margin-left:14px}
.shell{display:grid;grid-template-columns:208px minmax(0,1fr);max-width:1300px;margin:auto}
aside{border-right:1px solid #e0e7ef;padding:26px 14px;position:sticky;top:51px;align-self:start;max-height:calc(100vh - 52px);overflow:auto}
aside strong{display:block;font-size:13px;color:#5b7186;margin:0 10px 12px}
aside a{display:block;padding:7px 10px;border-radius:6px;font-size:13px;color:#34516b;overflow-wrap:anywhere}
aside a:hover{background:#e7eff7;text-decoration:none}
main{min-width:0;max-width:1050px;padding:28px 28px 90px;width:100%}
h1{font-size:clamp(1.55rem,2.7vw,2.2rem);line-height:1.35;margin:0 0 12px}
h2{font-size:1.2rem;margin:0 0 16px}h3{font-size:1rem;margin:0 0 10px}
section{background:#fff;border:1px solid #dce6ee;border-radius:10px;padding:22px;margin:20px 0}
.hero{padding:25px;border:1px solid #dbe5ee;background:#fff;border-radius:12px;margin-bottom:20px}
.hero p{margin:8px 0 0}.muted,small{color:#5c7185}.eyebrow{font-size:12px;font-weight:700;letter-spacing:.09em;color:#486c8c;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:13px}
.tile{border:1px solid #d9e4ed;border-radius:9px;padding:16px;background:#fff;display:block;color:inherit}
.tile:hover{border-color:#6c98bb;text-decoration:none}
.tile strong{display:block;font-size:15px;color:#24577f;overflow-wrap:anywhere}
.tile span{font-size:12px;color:#64798b}.tile p{font-size:13px;line-height:1.5;margin:6px 0 0}
.metric{font-size:27px;font-weight:750;line-height:1.2;color:#214f78}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin:16px 0}
.stats .tile{padding:12px 14px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #dce4ed;padding:9px 10px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eff4f8}.scroll{overflow-x:auto}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em}
p code,td code{background:#edf3f8;padding:2px 5px;border-radius:4px}
pre{white-space:pre;overflow:auto;max-height:650px;background:#f4f6f8;border:1px solid #d7e0e8;border-radius:7px;padding:14px;font-size:12px;line-height:1.55;color:#18354c}
pre code{font-size:inherit}details{margin:10px 0;border:1px solid #dce5ed;border-radius:8px;padding:11px 13px}
summary{font-weight:650;cursor:pointer;overflow-wrap:anywhere}
img,svg{max-width:100%;height:auto}img.diagram{display:block;width:100%;max-width:780px;margin:auto;border:1px solid #e3e9ef;border-radius:8px;background:white}
.notice{border-left:3px solid #c18b34;padding:10px 13px;background:#fff8ed;color:#684b20;margin:12px 0}
.meta{font-size:13px;color:#566d82}
.links{display:flex;flex-wrap:wrap;gap:9px;margin:12px 0}.links a{border:1px solid #bfd1df;background:#f6fafd;padding:6px 11px;border-radius:6px;font-size:13px}
footer{margin-top:26px;color:#718194;font-size:12px}
@media(max-width:780px){.shell{display:block}aside{position:static;max-height:none;border:0;border-bottom:1px solid #dfe6ee;padding:10px 14px;display:flex;flex-wrap:wrap;gap:2px}aside strong{width:100%;margin:0 8px 3px}aside a{padding:5px 8px}main{padding:18px 13px 65px}section{padding:15px}header small{display:none}}
</style>"""
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + esc(title) + '</title>' + css + '</head><body>'
            '<header><a href="' + esc(relative_home) + '">FPGA SoC CAPSTONE</a>'
            '<small>RTL · 주변장치 · 실습자료</small></header>'
            '<div class="shell"><aside><strong>자료 탐색</strong>' + nav + '</aside>'
            '<main>' + content + '<footer>설계 구상과 실제 FPGA 보드 검증은 구분됩니다. '
            '출처·소스·검증 결과를 반드시 확인하세요.</footer></main></div></body></html>')


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
