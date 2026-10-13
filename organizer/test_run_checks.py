"""Tashkilotchi tekshiruvchisining CLI va JSON shartnomasi."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "organizer" / "run_checks.py"


class CheckerCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.output = self.work / "results" / "natija.json"

    def run_checker(self, project):
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(project),
             "--json-output", str(self.output)],
            capture_output=True, text=True, timeout=15,
        )
        report = json.loads(self.output.read_text(encoding="utf-8"))
        return process, report

    def test_reference_gets_full_score_and_group_details(self):
        process, report = self.run_checker(ROOT / "organizer" / "reference")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"], "checked")
        self.assertEqual(report["functional_score"], 70)
        self.assertEqual(report["max_functional_score"], 70)
        self.assertTrue(report["all_passed"])
        self.assertTrue(report["regression_passed"])
        self.assertIsNone(report["error"])
        self.assertEqual([group["id"] for group in report["groups"]],
                         [f"B{i}" for i in range(1, 9)] + ["Regression"])
        self.assertEqual(report["tests_run"], sum(g["tests_run"] for g in report["groups"]))
        self.assertTrue(all(g["passed"] for g in report["groups"]))
        self.assertIn("Funksional ball: 70/70", process.stdout)

    def test_starter_is_checked_zero_not_a_loading_error(self):
        process, report = self.run_checker(ROOT / "participant" / "project")
        self.assertEqual(process.returncode, 1)
        self.assertEqual(report["status"], "checked")
        self.assertEqual(report["functional_score"], 0)
        self.assertFalse(report["all_passed"])
        self.assertTrue(report["regression_passed"])
        self.assertIsNone(report["error"])
        self.assertTrue(all(not g["passed"] for g in report["groups"][:-1]))
        self.assertGreater(sum(g["failures"] + g["errors"] for g in report["groups"]), 0)

    def test_import_and_interface_errors_have_structured_results(self):
        project = self.work / "team"
        project.mkdir()
        module = project / "bank.py"
        cases = [
            (None, "FileNotFoundError"),
            ("class Bank(:\n", "SyntaxError"),
            ("raise RuntimeError('buzilgan loyiha')\n", "RuntimeError"),
            ("raise SystemExit(7)\n", "SystemExit"),
            ("Bank = 1\n", "TypeError"),
            ("class Bank: pass\nBankError = int\n", "TypeError"),
            ("class Bank: pass\nclass BankError(ValueError): pass\n", "TypeError"),
        ]
        for source, expected_error in cases:
            with self.subTest(error=expected_error, source=source):
                if source is not None:
                    module.write_text(source, encoding="utf-8")
                process, report = self.run_checker(project)
                self.assertEqual(process.returncode, 2, process.stderr)
                self.assertEqual(report["status"], "error")
                self.assertIsNone(report["functional_score"])
                self.assertEqual(report["tests_run"], 0)
                self.assertEqual(report["groups"], [])
                self.assertFalse(report["all_passed"])
                self.assertFalse(report["regression_passed"])
                self.assertTrue(report["error"].startswith(expected_error + ":"))
                self.assertNotIn("Traceback", process.stderr)

    def test_existing_positional_cli_still_works(self):
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(ROOT / "organizer" / "reference")],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Funksional ball: 70/70", process.stdout)

    def test_output_write_error_is_reported_without_traceback(self):
        self.output.mkdir(parents=True)
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(ROOT / "organizer" / "reference"),
             "--json-output", str(self.output)],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn("JSON natijani saqlab bo'lmadi", process.stderr)
        self.assertNotIn("Traceback", process.stderr)


if __name__ == "__main__":
    unittest.main()
