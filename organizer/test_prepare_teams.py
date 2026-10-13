"""Team package isolation, roster validation and safe output publishing checks."""

import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from organizer import prepare_teams


class PrepareTeamsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.roster = self.root / "roster.csv"
        self.output = self.root / "event"

    def write_roster(self, text="team_id,team_name,members\nalpha,Alpha,Ali\nbeta,Beta,Vali\n"):
        self.roster.write_text(text, encoding="utf-8")
        return self.roster

    def test_bundles_are_separate_personalized_and_allowlisted(self):
        self.write_roster()
        self.assertEqual(prepare_teams.prepare_teams(self.roster, self.output), 2)
        banks = []
        for team_id, name, members in (("alpha", "Alpha", "Ali"), ("beta", "Beta", "Vali")):
            with ZipFile(self.output / "packages" / f"{team_id}.zip") as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(
                    set(archive.namelist()),
                    {f"{team_id}/{name}" for name in prepare_teams.PARTICIPANT_FILES}
                    | {f"{team_id}/TEAM.json", f"{team_id}/TEAM.md"},
                )
                self.assertFalse(any("organizer" in entry or "reference" in entry for entry in archive.namelist()))
                self.assertEqual(
                    json.loads(archive.read(f"{team_id}/TEAM.json")),
                    {"team_id": team_id, "team_name": name, "members": members},
                )
                report = archive.read(f"{team_id}/HISOBOT.md").decode()
                for value in (team_id, name, members, "## Topilgan va tuzatilgan xatolar"):
                    self.assertIn(value, report)
                instructions = archive.read(f"{team_id}/TEAM.md").decode()
                for value in (f"`{team_id}/`", "`project/`", "`HISOBOT.md`", "`TEAM.json`"):
                    self.assertIn(value, instructions)
                banks.append(archive.read(f"{team_id}/project/bank.py"))
        self.assertEqual(banks[0], banks[1])
        self.assertEqual(banks[0], (prepare_teams.ROOT / "participant/project/bank.py").read_bytes())
        self.assertEqual(list((self.output / "submissions").iterdir()), [])
        self.assertEqual(prepare_teams.load_roster(self.output / "teams.csv"), prepare_teams.load_roster(self.roster))
        with (self.output / "manual_scores.csv").open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            self.assertEqual(reader.fieldnames, list(prepare_teams.MANUAL_COLUMNS))
            self.assertEqual(
                list(reader),
                [{"team_id": team_id, "report": "", "code_tests": "", "demo": "", "notes": ""} for team_id in ("alpha", "beta")],
            )

    def test_bom_quoted_members_and_reordered_headers(self):
        self.write_roster('\ufeffmembers,team_name,team_id\n"Ali, Vali",  O\u02bbzbek jamoasi  ,  uz_1  \n')
        self.assertEqual(prepare_teams.load_roster(self.roster), [
            {"team_id": "uz_1", "team_name": "O\u02bbzbek jamoasi", "members": "Ali, Vali"}
        ])

    def test_invalid_rosters_fail_without_creating_output(self):
        invalid = [
            "", "team_id,team_name,members\n", "team_id,team_name\na,Alpha\n",
            "team_id,team_name,team_name\na,Alpha,Ali\n",
            "team_id,team_name,members,extra\na,Alpha,Ali,x\n",
            "team_id,team_name,members\na,Alpha,Ali,Vali\n",
            "team_id,team_name,members\na,Alpha\n",
            'team_id,team_name,members\na,Alpha,"Ali\n',
            "team_id,team_name,members\na,Alpha,Ali\na,Other,Vali\n",
            "team_id,team_name,members\na,Alpha,Ali\nA,Other,Vali\n",
            "team_id,team_name,members\na,  ,Ali\n",
        ]
        for text in invalid:
            with self.subTest(roster=text):
                self.write_roster(text)
                with self.assertRaises(ValueError):
                    prepare_teams.prepare_teams(self.roster, self.output)
                self.assertFalse(self.output.exists())

    def test_unsafe_ids_are_rejected(self):
        for team_id in ("../escape", "a/b", "a\\b", "/absolute", "-first", "_first", "UPPER", "jamoä", "a b", "a" * 49, ""):
            with self.subTest(team_id=team_id):
                self.write_roster(f"team_id,team_name,members\n{team_id},Alpha,Ali\n")
                with self.assertRaises(ValueError):
                    prepare_teams.load_roster(self.roster)

    def test_existing_output_is_not_overwritten(self):
        self.write_roster()
        prepare_teams.prepare_teams(self.roster, self.output)
        before = {path.relative_to(self.output): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        with self.assertRaises(ValueError):
            prepare_teams.prepare_teams(self.roster, self.output)
        after = {path.relative_to(self.output): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_empty_output_directory_is_accepted(self):
        self.write_roster()
        self.output.mkdir()
        self.assertEqual(prepare_teams.prepare_teams(self.roster, self.output), 2)

    def test_file_and_symlink_output_are_rejected(self):
        self.write_roster()
        self.output.write_text("keep me")
        with self.assertRaises(ValueError):
            prepare_teams.prepare_teams(self.roster, self.output)
        self.assertEqual(self.output.read_text(), "keep me")
        self.output.unlink()
        target = self.root / "target"
        target.mkdir()
        self.output.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            prepare_teams.prepare_teams(self.roster, self.output)
        self.assertEqual(list(target.iterdir()), [])

    def test_missing_source_does_not_leave_partial_event(self):
        self.write_roster()
        with patch.object(prepare_teams, "PARTICIPANT_FILES", ["project/bank.py", "does-not-exist"]):
            with self.assertRaises(OSError):
                prepare_teams.prepare_teams(self.roster, self.output)
        self.assertFalse(self.output.exists())

    def test_failure_during_packaging_does_not_leave_partial_event(self):
        self.write_roster()
        with patch.object(prepare_teams, "ZipFile", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                prepare_teams.prepare_teams(self.roster, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".cardlab-teams-*")), [])


if __name__ == "__main__":
    unittest.main()
