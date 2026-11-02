"""Continuous, deterministic hypothesis-driven GitHub repository research.

Hourly query generation deliberately rotates application, vendor/board, and
engineering evidence angles. This improves discovery diversity without claiming
a generative AI model is running. Only public repository metadata is ingested.
"""
import datetime as dt
import json
import math
import os
from pathlib import Path
import urllib.error
import urllib.parse

from .discover import ROOT, POLICY, api, evidence, score, license_policy

MATRIX = ROOT / "config/research_matrix.json"
HISTORY = ROOT / "catalog/research_history.json"


def load(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return fallback


def compose_queries(matrix, iteration, existing, limit=8):
    domains = matrix["domains"]
    boards = matrix["boards"]
    modes = matrix["research_modes"]
    counts = {d["category"]: 0 for d in domains}
    for item in existing:
        category = item.get("vendor_hint")
        if category in counts:
            counts[category] += 1
    # Pick underrepresented domains, with a rolling offset as tie breaker.
    order = sorted(range(len(domains)), key=lambda i: (counts[domains[i]["category"]],
                                                         (i - iteration) % len(domains)))
    result, used = [], set()
    for step in range(limit - 2):
        d = domains[order[step % len(order)]]
        b = boards[(iteration + step * 5) % len(boards)]
        m = modes[(iteration // 2 + step) % len(modes)]
        term = d["terms"][(iteration // 7 + step) % len(d["terms"])]
        q = " ".join([b[0], term, m["suffix"]])
        if q not in used:
            used.add(q)
            result.append({"q": q, "category": d["category"], "board_hint": b[0],
                           "vendor_family": b[1], "strategy": m["name"]})
    # Anchor queries discover projects missing board names or using generic terms.
    for k in (iteration, iteration + 1):
        a = matrix["anchor_queries"][k % len(matrix["anchor_queries"])]
        if a["q"] not in used:
            result.append({**a, "board_hint": "UNSPECIFIED",
                           "vendor_family": "CROSS_VENDOR", "strategy": "anchor"})
    return result[:limit]


def utc_hour(value):
    return int(value.timestamp() // 3600)


def run(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    previous = load(ROOT / "catalog/discovered.json", {"results": []})
    old = previous.get("results", [])
    history = load(HISTORY, {"runs": []})
    matrix = load(MATRIX, {})
    queries = compose_queries(matrix, utc_hour(now), old)
    found, issues = [], []
    seen = set()
    success_queries = 0
    inspected = 0
    for query in queries:
        args = urllib.parse.urlencode({"q": query["q"], "per_page": POLICY["per_query"],
                                       "sort": "updated", "order": "desc"})
        try:
            response = api("https://api.github.com/search/repositories?" + args)
            success_queries += 1
        except (urllib.error.URLError, ValueError) as exc:
            issues.append({"query": query["q"], "error": type(exc).__name__})
            continue
        for item in response.get("items", []):
            name = item.get("full_name", "")
            if (not name or name.lower() in seen or item.get("archived") or item.get("fork")
                    or inspected >= POLICY["repo_limit"]):
                continue
            inspected += 1
            seen.add(name.lower())
            branch = item.get("default_branch") or "main"
            url = ("https://api.github.com/repos/" + urllib.parse.quote(name, safe="/")
                   + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1")
            try:
                tree = api(url)
                paths = [e["path"] for e in tree.get("tree", []) if e.get("type") == "blob"]
                info = evidence(paths)
                if tree.get("truncated"):
                    issues.append({"repo": name, "error": "truncated_git_tree"})
                if not info["hdl_count"]:
                    continue
            except (urllib.error.URLError, ValueError, KeyError) as exc:
                issues.append({"repo": name, "error": type(exc).__name__})
                continue
            license_id = (item.get("license") or {}).get("spdx_id") or "UNKNOWN"
            found.append({
                "id": name.lower().replace("/", "--"), "repository": name,
                "url": item["html_url"], "description": (item.get("description") or "")[:800],
                "vendor_hint": query["category"], "board_hint": query["board_hint"],
                "vendor_family": query["vendor_family"], "research_strategy": query["strategy"],
                "classification_method": "query_hypothesis_not_hardware_verification",
                "license_spdx": license_id, "reuse_policy": license_policy(license_id),
                "default_branch": branch, "source_tree_sha": tree.get("sha"),
                "last_upstream_update": item.get("updated_at"), "board_verified": False,
                "evidence": info, "score": score(info, license_id)})
        if inspected >= POLICY["repo_limit"]:
            break

    if not success_queries:
        raise RuntimeError("All public search requests failed; existing catalog unchanged")
    timestamp = now.isoformat()
    merged = {i["repository"].lower(): i for i in old if i.get("repository")}
    new_count = 0
    for item in found:
        key = item["repository"].lower()
        previous_item = merged.get(key, {})
        if key not in merged:
            new_count += 1
        item["first_seen"] = previous_item.get("first_seen", timestamp)
        item["last_seen"] = timestamp
        item["discovery_count"] = previous_item.get("discovery_count", 0) + 1
        # Keep audit-review annotations on refresh, never upstream success flags.
        merged[key] = {**previous_item, **item}
    results = sorted(merged.values(), key=lambda x: (-x.get("score", 0), x["repository"].lower()))
    result = {"schema_version": 2, "generated_at": timestamp,
              "total_unique": len(results), "new_count": new_count,
              "results": results, "errors": issues}
    new_history = {"schema_version": 1, "runs": (history.get("runs", []) + [{
        "timestamp": timestamp, "queries": queries, "new_count": new_count,
        "results_found": len(found), "total_unique": len(results),
        "failed_queries": len(issues)
    }])[-240:]}
    return result, new_history


def main():
    catalog, history = run()
    target = ROOT / "catalog/discovered.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RESEARCH", catalog["new_count"], "new;", catalog["total_unique"],
          "known;", len(catalog["errors"]), "warnings")


if __name__ == "__main__":
    main()
