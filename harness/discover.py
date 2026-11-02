"""Search public GitHub *metadata* and inventory HDL evidence; never download source."""
import datetime as dt
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))
HDL = tuple(POLICY["scan_extensions"])


def api(url):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "fpga-soc-capstone-harness/1.0",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def license_policy(spdx):
    return "review_for_reuse" if spdx in POLICY["permissive_licenses"] else "reference_only"


def evidence(paths):
    hdl = [p for p in paths if p.lower().endswith(HDL)]
    checks = [p for p in paths if any(pattern.lower() in p.lower()
              for pattern in POLICY["evidence_patterns"])]
    return {"hdl_count": len(hdl), "hdl_examples": hdl[:12],
            "evidence_files": checks[:24],
            "has_constraints": any(p.lower().endswith((".xdc", ".qsf", ".lpf", ".pcf")) for p in paths),
            "has_testbench": any("testbench" in p.lower() or "tb_" in p.lower()
                                 or "_tb." in p.lower() for p in paths)}


def score(info, lic):
    value = min(info["hdl_count"], 10) * 2
    value += 12 if info["has_constraints"] else 0
    value += 12 if info["has_testbench"] else 0
    value += min(len(info["evidence_files"]), 8) * 2
    value += 10 if license_policy(lic) == "review_for_reuse" else 0
    return min(value, 100)


def discover():
    queries = json.loads((ROOT / "config/search_queries.json").read_text(encoding="utf-8"))
    results, errors, seen = [], [], set()
    for entry in queries:
        q = urllib.parse.urlencode({"q": entry["q"], "sort": "best-match",
                                     "per_page": POLICY["per_query"]})
        try:
            data = api("https://api.github.com/search/repositories?" + q)
        except (urllib.error.URLError, ValueError) as exc:
            # Do not silently destroy the previous catalog if search becomes unavailable.
            raise RuntimeError("Discovery search failed for " + entry["q"]) from exc
        for repo in data.get("items", []):
            name = repo.get("full_name", "")
            if not name or name in seen or repo.get("archived") or repo.get("fork"):
                continue
            seen.add(name)
            if len(seen) > POLICY["repo_limit"]:
                break
            branch = repo.get("default_branch") or "main"
            url = ("https://api.github.com/repos/" + urllib.parse.quote(name, safe="/")
                   + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1")
            try:
                tree = api(url)
                paths = [x["path"] for x in tree.get("tree", []) if x.get("type") == "blob"]
                if tree.get("truncated"):
                    errors.append({"repository": name, "reason": "tree_truncated"})
                info = evidence(paths[:POLICY["tree_path_limit"]])
            except (urllib.error.URLError, ValueError, KeyError) as exc:
                errors.append({"repository": name, "reason": type(exc).__name__})
                continue
            if not info["hdl_count"]:
                continue
            lic = (repo.get("license") or {}).get("spdx_id") or "UNKNOWN"
            results.append({
                "id": name.lower().replace("/", "--"), "repository": name,
                "url": repo["html_url"], "description": (repo.get("description") or "")[:800],
                "vendor_hint": entry["category"], "classification_method": "search_query_heuristic",
                "license_spdx": lic, "reuse_policy": license_policy(lic),
                "default_branch": branch, "source_tree_sha": tree.get("sha"),
                "last_upstream_update": repo.get("updated_at"), "board_verified": False,
                "evidence": info, "score": score(info, lic)})
            time.sleep(POLICY["request_delay_seconds"])
        if len(seen) > POLICY["repo_limit"]:
            break
    if not results:
        raise RuntimeError("No HDL repositories found; retained previous catalog.")
    results.sort(key=lambda r: (-r["score"], r["repository"].lower()))
    return {"schema_version": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "results": results[:POLICY["max_catalog_entries"]], "errors": errors}


def main():
    content = discover()
    target = ROOT / "catalog/discovered.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    print("Discovered", len(content["results"]), "repositories; errors:", len(content["errors"]))


if __name__ == "__main__":
    main()
