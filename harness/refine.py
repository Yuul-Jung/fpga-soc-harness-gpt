"""Use the two-hour audit to improve proposals without claiming third-party code works."""
import datetime as dt
import json
from .research import ROOT, load
from .propose import build_proposals


def refine():
    catalog = load(ROOT / "catalog/discovered.json", {"results": []})
    reviews = load(ROOT / "catalog/reviewed.json", {"reviews": []})
    previous = load(ROOT / "catalog/proposals.json", {"proposals": []})
    old = {p["reference"].lower(): p for p in previous["proposals"]}
    reviewed = {r["reference"].lower(): r for r in reviews["reviews"]}
    result = build_proposals(catalog)
    for proposed in result["proposals"]:
        key = proposed["reference"].lower()
        audit = reviewed.get(key)
        if audit:
            proposed["reviewed_category"] = audit["category"]
            proposed["quality_score"] = audit["quality_score"]
            proposed["audit_readiness"] = audit["readiness"]
            proposed["improvements"] = audit["improvements"]
            proposed["reviewed_at"] = audit["checked_at"]
            proposed["board_hint"] = audit["board"]
            proposed["vendor_family"] = audit["vendor_family"]
            proposed["metadata_verified_only"] = True
        # Human reviews/decisions must not be silently erased by hourly tasks.
        current = old.get(key, {})
        if current.get("approval_state") in ("human_approved", "rejected"):
            proposed["approval_state"] = current["approval_state"]
            if "review_note" in current:
                proposed["review_note"] = current["review_note"]
    result["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result


def main():
    target = ROOT / "catalog/proposals.json"
    updated = refine()
    target.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("REFINE", len(updated["proposals"]), "design proposals")


if __name__ == "__main__":
    main()
