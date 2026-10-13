"""Integration checks: python -m unittest discover -s organizer -p 'test_*.py'."""

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "organizer" / "evaluate_teams.py"
REFERENCE = ROOT / "organizer" / "reference" / "bank.py"
STARTER = ROOT / "participant" / "project" / "bank.py"


class EvaluateTeamsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.event = Path(temporary.name) / "event"
        self.event.mkdir()

    def write_csv(self, name, fields, rows):
        with (self.event / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)

    def roster(self, *team_ids):
        self.write_csv(
            "teams.csv", ("team_id", "team_name", "members"),
            [(team_id, f"Jamoa {team_id}", "Ali; Vali") for team_id in team_ids],
        )

    def manual(self, *rows):
        self.write_csv(
            "manual_scores.csv", ("team_id", "report", "code_tests", "demo", "notes"),
            rows,
        )

    def submission(self, team_id, source=REFERENCE, text=None):
        project = self.event / "submissions" / team_id / "project"
        project.mkdir(parents=True)
        bank = project / "bank.py"
        if text is None:
            shutil.copyfile(source, bank)
        else:
            bank.write_text(text, encoding="utf-8")
        return project

    def evaluate(self, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(EVALUATOR), "--event", str(self.event), *arguments],
            capture_output=True, text=True, timeout=30, cwd=ROOT,
        )
        self.assertEqual(
            result.returncode, expected,
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def results(self, output=None):
        output = output or self.event / "results"
        document = json.loads((output / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        return {team["team_id"]: team for team in document["teams"]}

    def test_reference_starter_and_missing_submission_are_reported(self):
        self.roster("reference", "starter", "missing")
        source = REFERENCE.read_text(encoding="utf-8").replace(
            "def calculate_fee(amount):\n    return (amount + 99) // 100",
            "from data.rules import calculate_fee",
        )
        self.assertIn("from data.rules import calculate_fee", source)
        reference = self.submission(
            "reference",
            text=source + "\nPath(__file__).with_name('imported.txt').write_text('imported')\n",
        )
        helpers = reference / "data"
        helpers.mkdir()
        (helpers / "__init__.py").write_text("", encoding="utf-8")
        (helpers / "rules.py").write_text(
            "def calculate_fee(amount):\n    return (amount + 99) // 100\n",
            encoding="utf-8",
        )
        self.submission("starter", STARTER)
        self.manual(
            ("reference", 15, 10, 5, "To'liq bajarildi"),
            ("starter", 0, 0, 0, ""),
            ("missing", 0, 0, 0, "Topshirilmadi"),
        )
        before = {
            path.relative_to(reference): path.read_bytes() if path.is_file() else None
            for path in reference.rglob("*")
        }

        self.evaluate(expected=1)
        teams = self.results()

        self.assertEqual(set(teams), {"reference", "starter", "missing"})
        best = teams["reference"]
        self.assertEqual(best["team_name"], "Jamoa reference")
        self.assertEqual(best["status"], "checked")
        self.assertEqual(best["functional_score"], 70)
        self.assertTrue(best["regression_passed"])
        self.assertTrue(best["manual_ready"])
        self.assertEqual(best["total"], 100)
        self.assertEqual(best["rank"], 1)
        self.assertEqual(best["notes"], "To'liq bajarildi")
        self.assertIsInstance(best["checks"], dict)
        self.assertEqual(teams["starter"]["status"], "checked")
        self.assertEqual(teams["starter"]["functional_score"], 0)
        self.assertEqual(teams["missing"]["status"], "missing")
        self.assertIsNone(teams["missing"]["functional_score"])
        self.assertIsNone(teams["missing"]["total"])
        self.assertIsNone(teams["missing"]["rank"])

        output = self.event / "results"
        with (output / "results.csv").open(encoding="utf-8-sig", newline="") as stream:
            csv_teams = {row["team_id"]: row for row in csv.DictReader(stream)}
        self.assertEqual(set(csv_teams), set(teams))
        self.assertEqual(csv_teams["reference"]["total"], "100")
        leaderboard = (output / "leaderboard.md").read_text(encoding="utf-8")
        for team_id in teams:
            self.assertIn(team_id, leaderboard)
            self.assertTrue((output / "logs" / f"{team_id}.log").is_file())
        after = {
            path.relative_to(reference): path.read_bytes() if path.is_file() else None
            for path in reference.rglob("*")
        }
        self.assertEqual(after, before)

    def test_blank_manual_scores_stay_pending_but_zero_is_complete(self):
        self.roster("zero", "blank", "partial", "absent")
        for team_id in ("zero", "blank", "partial", "absent"):
            self.submission(team_id)
        self.manual(
            ("zero", 0, 0, 0, ""),
            ("blank", "", "", "", "Kutilmoqda"),
            ("partial", 15, "", 5, ""),
        )

        self.evaluate()
        teams = self.results()

        self.assertTrue(teams["zero"]["manual_ready"])
        self.assertEqual(teams["zero"]["total"], 70)
        self.assertEqual(teams["zero"]["rank"], 1)
        for team_id in ("blank", "partial", "absent"):
            with self.subTest(team=team_id):
                self.assertFalse(teams[team_id]["manual_ready"])
                self.assertIsNone(teams[team_id]["total"])
                self.assertIsNone(teams[team_id]["rank"])
        self.assertIsNone(teams["blank"]["report"])
        self.assertEqual(teams["partial"]["report"], 15)
        self.assertIsNone(teams["partial"]["code_tests"])

    def test_absent_manual_file_and_empty_custom_output_are_supported(self):
        self.roster("ready")
        self.submission("ready")
        output = self.event.parent / "custom-results"
        output.mkdir()

        self.evaluate("--output", str(output))
        team = self.results(output)["ready"]

        self.assertEqual(team["functional_score"], 70)
        self.assertFalse(team["manual_ready"])
        self.assertIsNone(team["total"])
        self.assertIsNone(team["rank"])
        self.assertFalse((self.event / "results").exists())

    def test_syntax_error_and_timeout_do_not_stop_later_team(self):
        self.roster("broken", "hanging", "later")
        self.submission("broken", text="def unfinished(\n")
        self.submission("hanging", text="while True:\n    pass\n")
        self.submission("later")

        self.evaluate("--timeout", "1", expected=1)
        teams = self.results()

        self.assertIn(teams["broken"]["status"], {"invalid", "error"})
        self.assertEqual(teams["hanging"]["status"], "timeout")
        self.assertEqual(teams["later"]["status"], "checked")
        self.assertEqual(teams["later"]["functional_score"], 70)
        for team_id in ("broken", "hanging"):
            self.assertIsNone(teams[team_id]["functional_score"])
            self.assertIsNone(teams[team_id]["rank"])
            log = self.event / "results" / "logs" / f"{team_id}.log"
            self.assertTrue(log.read_text(encoding="utf-8").strip())

    def test_mismatched_team_metadata_rejects_only_its_submission(self):
        self.roster("mismatch", "later")
        invalid = self.submission("mismatch")
        valid = self.submission("later")
        (invalid.parent / "TEAM.json").write_text(
            json.dumps({"team_id": "other"}), encoding="utf-8",
        )
        (valid.parent / "TEAM.json").write_text(
            json.dumps({"team_id": "later"}), encoding="utf-8",
        )

        self.evaluate(expected=1)
        teams = self.results()

        self.assertEqual(teams["mismatch"]["status"], "invalid")
        self.assertIsNone(teams["mismatch"]["functional_score"])
        self.assertIsNone(teams["mismatch"]["rank"])
        self.assertIn("TEAM.json", teams["mismatch"]["error"])
        self.assertEqual(teams["later"]["status"], "checked")
        self.assertEqual(teams["later"]["functional_score"], 70)

    def test_invalid_manual_scores_fail_before_creating_output(self):
        self.roster("team")
        self.submission("team")
        for scores in [
            (16, 0, 0), (0, 11, 0), (0, 0, 6),
            (-1, 0, 0), ("1.5", 0, 0), ("x", 0, 0),
        ]:
            with self.subTest(scores=scores):
                self.manual(("team", *scores, ""))
                self.evaluate(expected=2)
                self.assertFalse((self.event / "results").exists())

    def test_invalid_timeout_is_rejected_without_creating_output(self):
        self.roster("team")
        self.submission("team")
        for value in ("0", "-1", "nan", "inf", "no"):
            with self.subTest(timeout=value):
                self.evaluate("--timeout", value, expected=2)
                self.assertFalse((self.event / "results").exists())

    def test_populated_output_is_never_overwritten(self):
        self.roster("team")
        self.submission("team")
        self.evaluate()
        output = self.event / "results"
        before = {
            path.relative_to(output): path.read_bytes()
            for path in output.rglob("*") if path.is_file()
        }

        self.evaluate(expected=2)

        after = {
            path.relative_to(output): path.read_bytes()
            for path in output.rglob("*") if path.is_file()
        }
        self.assertEqual(after, before)

    def test_regression_failure_keeps_functional_score_but_has_no_rank(self):
        self.roster("regression")
        source = REFERENCE.read_text(encoding="utf-8") + """

_normal_toggle = Bank.toggle_block

def broken_toggle(self, card_id):
    if card_id == 'C1':
        return False
    return _normal_toggle(self, card_id)

Bank.toggle_block = broken_toggle
"""
        self.submission("regression", text=source)
        self.manual(("regression", 15, 10, 5, ""))

        self.evaluate()
        team = self.results()["regression"]

        self.assertEqual(team["status"], "checked")
        self.assertEqual(team["functional_score"], 70)
        self.assertFalse(team["regression_passed"])
        self.assertTrue(team["manual_ready"])
        self.assertIsNone(team["rank"])

    def test_ranks_use_total_then_functional_then_report_and_share_exact_ties(self):
        self.roster("lower_functional", "lower_report", "equal_b", "equal_a")
        for team_id in ("lower_report", "equal_b", "equal_a"):
            self.submission(team_id)
        self.submission(
            "lower_functional",
            text=REFERENCE.read_text(encoding="utf-8").replace(
                "return (amount + 99) // 100", "return amount // 100",
            ),
        )
        self.manual(
            ("lower_functional", 15, 5, 0, ""),
            ("lower_report", 5, 5, 0, ""),
            ("equal_b", 10, 0, 0, ""),
            ("equal_a", 10, 0, 0, ""),
        )

        self.evaluate()
        teams = self.results()

        self.assertEqual(teams["lower_functional"]["functional_score"], 60)
        self.assertEqual({team["total"] for team in teams.values()}, {80})
        self.assertEqual(teams["equal_a"]["rank"], 1)
        self.assertEqual(teams["equal_b"]["rank"], 1)
        self.assertGreater(teams["lower_report"]["rank"], 1)
        self.assertGreater(
            teams["lower_functional"]["rank"], teams["lower_report"]["rank"],
        )


if __name__ == "__main__":
    unittest.main()
