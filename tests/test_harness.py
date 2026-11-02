"""Offline unit tests: all fixtures are first-party; no web dependency."""
import json
import unittest
import zipfile
from pathlib import Path

from harness.discover import evidence, license_policy, score
from harness.draft import make_draft
from harness.generate import ROOT, SITE, safe_local, svg_diagram, validate_design, main as generate_site
from harness.maintenance import inspect_site
from harness.propose import build_proposals
from harness.research import compose_queries, load, ROOT as SEARCH_ROOT
from harness.review import audit
from harness.factory import instrument_design


class HarnessTests(unittest.TestCase):
    def test_license_gate(self):
        self.assertEqual(license_policy("MIT"), "review_for_reuse")
        self.assertEqual(license_policy("GPL-3.0"), "reference_only")
        self.assertEqual(license_policy("UNKNOWN"), "reference_only")

    def test_inventory_and_score(self):
        files = ["rtl/motor_pwm.v", "rtl/tb_motor_pwm.sv", "constraints/basys3.xdc", "README.md"]
        result = evidence(files)
        self.assertEqual(result["hdl_count"], 2)
        self.assertTrue(result["has_constraints"])
        self.assertTrue(result["has_testbench"])
        self.assertGreater(score(result, "MIT"), score(result, "UNKNOWN"))

    def test_design_ir(self):
        folder = ROOT / "capstones/smart_fan"
        design = json.loads((folder / "design.json").read_text(encoding="utf-8"))
        validate_design(design, folder)
        diagram = svg_diagram(design)
        self.assertIn("smart_fan_peripheral", diagram)
        self.assertIn("tach_pulses_per_sec", diagram)
        self.assertIn("external_fan_interface", diagram)

    def test_untrusted_file_path_blocked(self):
        with self.assertRaises(ValueError):
            safe_local(ROOT / "capstones/smart_fan", "../../README.md")

    def test_bad_net_rejected(self):
        folder = ROOT / "capstones/smart_fan"
        design = json.loads((folder / "design.json").read_text(encoding="utf-8"))
        design["connections"].append({"from": "cpu.not_a_port", "to": "peripheral.duty"})
        with self.assertRaises(ValueError):
            validate_design(design, folder)

    def test_proposals_are_unapproved(self):
        mock = {"results": [{"id": "repo", "repository": "org/repo",
            "url": "https://github.com/org/repo", "source_tree_sha": "abc",
            "license_spdx": "MIT", "reuse_policy": "review_for_reuse",
            "vendor_hint": "motor"}]}
        proposal = build_proposals(mock)["proposals"][0]
        self.assertEqual(proposal["approval_state"], "pending_review")
        self.assertEqual(proposal["rtl_source_status"], "not_ported")
        draft = make_draft(proposal)
        self.assertEqual(draft["status"], "CONCEPT_ONLY_NOT_PORTED")
        self.assertFalse(draft["source_code_included"])
        self.assertEqual(draft["hardware_board"], "UNASSIGNED")
        self.assertEqual(len(draft["connections"]), len(draft["modules"]) - 1)

    def test_rotating_search_diversity(self):
        matrix = load(SEARCH_ROOT / "config/research_matrix.json", {})
        q0 = compose_queries(matrix, 10001, [], 8)
        q1 = compose_queries(matrix, 10002, [], 8)
        self.assertEqual(len(q0), 8)
        self.assertNotEqual([e["q"] for e in q0], [e["q"] for e in q1])
        self.assertGreaterEqual(len({e["category"] for e in q0}), 4)

    def test_source_review_is_metadata_only(self):
        item = {"id":"x", "repository":"example/fpga-oscilloscope",
            "url":"https://github.com/example/fpga-oscilloscope",
            "description":"oscilloscope VGA capture trigger Verilog",
            "source_tree_sha":"abc", "license_spdx":"MIT",
            "vendor_hint":"instrument", "score":65,
            "evidence":{"hdl_count":5, "hdl_examples":["rtl/top.v"],
                        "evidence_files":["README.md", "board.qsf"],
                        "has_constraints": True, "has_testbench": False}}
        r = audit(item, remote_status="source_tree_sha_confirmed")
        self.assertEqual(r["category"], "instrument")
        self.assertFalse(r["source_rtl_tested"])
        self.assertFalse(r["board_tested"])
        self.assertIn("Create first-party self-checking simulation tests",r["improvements"])
        self.assertEqual(r["readiness"],"metadata_reviewed_for_design_proposal")
        design = instrument_design(r)
        self.assertEqual(design["id"], "instrument_pulse_counter")
        self.assertEqual(design["test_spec"]["rtl_top"], "tb_pulse_event_meter")


    def test_browsable_main_and_per_capstone_html(self):
        # Generated pages must be directly linked and show full RTL sources.
        generate_site()
        index = (SITE / "index.html").read_text(encoding="utf-8")
        collection = (SITE / "capstones/index.html").read_text(encoding="utf-8")
        detail = (SITE / "capstones/smart_fan/index.html").read_text(encoding="utf-8")
        self.assertIn("capstones/smart_fan/index.html", index)
        self.assertIn("smart_fan/index.html", collection)
        self.assertIn("전체 실행소스 ZIP", detail)
        self.assertIn("module smart_fan_peripheral", detail)
        self.assertIn("verification.json", detail)
        self.assertIn("system.svg", detail)
        self.assertIn("BOM.csv", detail)
        self.assertIn("← 전체 캡스톤 목차로", detail)
        with zipfile.ZipFile(SITE / "capstones/smart_fan/source_bundle.zip") as bundle:
            self.assertIn("smart_fan/rtl/smart_fan_peripheral.v", bundle.namelist())
            self.assertIn("smart_fan/design.json", bundle.namelist())
        errors, count = inspect_site()
        self.assertGreaterEqual(count, 3)
        self.assertEqual(errors, [])



if __name__ == "__main__":
    unittest.main()
