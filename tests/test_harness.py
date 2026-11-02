"""Offline unit tests: all fixtures are first-party; no web dependency."""
import json
import unittest
from pathlib import Path

from harness.discover import evidence, license_policy, score
from harness.draft import make_draft
from harness.generate import ROOT, safe_local, svg_diagram, validate_design
from harness.propose import build_proposals


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


if __name__ == "__main__":
    unittest.main()
