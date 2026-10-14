"""Har bir jamoaga alohida, bir xil boshlang'ich loyiha tayyorlash."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.package import PARTICIPANT_FILES  # noqa: E402


ROSTER_COLUMNS = ("team_id", "team_name", "members")
MANUAL_COLUMNS = ("team_id", "report", "code_tests", "demo", "notes")
TEAM_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}", re.ASCII)


def load_roster(path: str | Path) -> list[dict[str, str]]:
    """Read a UTF-8 roster; reject malformed rows and ambiguous team identities."""
    teams: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            headers = next(reader, None)
            if (
                headers is None
                or len(headers) != len(ROSTER_COLUMNS)
                or set(headers) != set(ROSTER_COLUMNS)
            ):
                raise ValueError("CSV ustunlari: team_id,team_name,members bo'lishi kerak.")
            for values in reader:
                if not values:  # CSV permits completely empty lines.
                    continue
                if len(values) != len(headers):
                    raise ValueError(f"CSV {reader.line_num}-qatorida ustunlar soni noto'g'ri.")
                team = {key: value.strip() for key, value in zip(headers, values)}
                team_id = team["team_id"]
                if TEAM_ID_PATTERN.fullmatch(team_id) is None:
                    raise ValueError(
                        f"CSV {reader.line_num}-qatori: team_id kichik lotin harflari, "
                        "raqam, '-' va '_'dan iborat bo'lsin; harf yoki raqam bilan "
                        "boshlansin va 1–48 belgidan oshmasin."
                    )
                if team_id.casefold() in seen:
                    raise ValueError(f"Takrorlangan team_id: {team_id}")
                if not team["team_name"]:
                    raise ValueError(f"{team_id}: team_name bo'sh bo'lishi mumkin emas.")
                if any("\x00" in value for value in team.values()):
                    raise ValueError(f"{team_id}: CSV qiymatlarida NUL belgisi bo'lmasin.")
                seen.add(team_id.casefold())
                teams.append(team)
    except (csv.Error, UnicodeError) as error:
        raise ValueError(f"CSV UTF-8 formatida to'g'ri yozilishi kerak: {error}") from error
    if not teams:
        raise ValueError("CSVda kamida bitta jamoa bo'lishi kerak.")
    return teams


def _require_empty_destination(destination: Path) -> None:
    if destination.is_symlink():
        raise ValueError(f"Natija papkasi symlink bo'lmasin: {destination}")
    if destination.exists() and (
        not destination.is_dir() or next(destination.iterdir(), None) is not None
    ):
        raise ValueError(f"Natija uchun yangi yoki bo'sh papka tanlang: {destination}")


def _participant_contents() -> dict[str, bytes]:
    """Load the distribution allowlist once, before any event files are written."""
    participant = (ROOT / "participant").resolve()
    contents: dict[str, bytes] = {}
    for name in PARTICIPANT_FILES:
        relative = PurePosixPath(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in name
            or str(relative) != name
            or name in contents
            or name in {"TEAM.json", "TEAM.md"}
        ):
            raise ValueError(f"Ishtirokchi fayl yo'li noto'g'ri: {name}")
        source = (participant / name).resolve()
        if not source.is_relative_to(participant):
            raise ValueError(f"Ishtirokchi fayli papkadan tashqariga chiqmoqda: {name}")
        contents[name] = source.read_bytes()
    if "HISOBOT.md" not in contents or "project/bank.py" not in contents:
        raise ValueError("Ishtirokchi fayllarida HISOBOT.md va project/bank.py bo'lishi kerak.")
    return contents


def _personalized_report(template: str, team: dict[str, str]) -> str:
    identity = (
        f"Jamoa ID: `{team['team_id']}`\n\n"
        f"Jamoa nomi: {team['team_name']}\n\n"
        f"Ishtirokchilar: {team['members']}\n\n"
    )
    # Keep every exercise/report section from the shared participant template.
    body = (template.replace("Jamoa IDsi:\n", "", 1)
            .replace("Jamoa nomi:\n", "", 1).replace("Ishtirokchilar:\n", "", 1))
    if body.startswith("# Jamoa hisoboti\n"):
        body = body[len("# Jamoa hisoboti\n"):].lstrip("\n")
    return "# Jamoa hisoboti\n\n" + identity + body


def _team_instructions(team: dict[str, str]) -> str:
    team_id = team["team_id"]
    return (
        f"# {team['team_name']}\n\n"
        f"Jamoa ID: `{team_id}`\n\n"
        f"Ishtirokchilar: {team['members']}\n\n"
        "## Boshlash\n\n"
        "`START_HERE.md`ni o'qing. Jamoangiz `project/` ichidagi loyihani "
        "tuzatadi (1-shart), Include commission funksiyasini qo'shadi (2-shart) "
        "va `HISOBOT.md`ni to'ldiradi. Barcha jamoalar bir xil "
        "boshlang'ich kod bilan ishlaydi.\n\n"
        "## Ishni topshirish\n\n"
        f"Ish oxirida butun `{team_id}/` papkasini tashkilotchiga topshiring "
        "(papkani ZIP qilib yuborish ham mumkin). Papka nomini va "
        "`TEAM.json`dagi jamoa ID sini o'zgartirmang.\n\n"
        "Papka ichida quyidagilar bo'lishi shart:\n\n"
        "- `project/` — tuzatilgan loyiha va yozgan testlaringiz;\n"
        "- `HISOBOT.md` — to'ldirilgan hisobot;\n"
        "- `TEAM.json` — jamoa ma'lumotlari.\n\n"
        "Har bir jamoaning ishi yakunda alohida tekshiriladi.\n"
    )


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def prepare_teams(roster_path: str | Path, output_dir: str | Path) -> int:
    """Build a complete event folder without replacing any existing event data."""
    teams = load_roster(roster_path)
    destination = Path(output_dir).absolute()
    _require_empty_destination(destination)
    contents = _participant_contents()
    report_template = contents["HISOBOT.md"].decode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Build alongside the destination so publishing the complete directory is atomic.
    with tempfile.TemporaryDirectory(prefix=".cardlab-teams-", dir=destination.parent) as temp:
        staged = Path(temp) / "event"
        (staged / "packages").mkdir(parents=True)
        (staged / "submissions").mkdir()
        _write_csv(staged / "teams.csv", ROSTER_COLUMNS, teams)
        _write_csv(
            staged / "manual_scores.csv",
            MANUAL_COLUMNS,
            [{"team_id": team["team_id"]} for team in teams],
        )
        for team in teams:
            team_id = team["team_id"]
            with ZipFile(staged / "packages" / f"{team_id}.zip", "w", ZIP_DEFLATED) as archive:
                for name, content in contents.items():
                    if name == "HISOBOT.md":
                        content = _personalized_report(report_template, team).encode("utf-8")
                    archive.writestr(f"{team_id}/{name}", content)
                archive.writestr(
                    f"{team_id}/TEAM.json",
                    json.dumps(team, ensure_ascii=False, indent=2) + "\n",
                )
                archive.writestr(f"{team_id}/TEAM.md", _team_instructions(team))
        _require_empty_destination(destination)
        os.replace(staged, destination)
    return len(teams)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", required=True, type=Path, help="team_id,team_name,members ustunli CSV")
    parser.add_argument("--output", required=True, type=Path, help="Yangi yoki bo'sh tadbir papkasi")
    args = parser.parse_args()
    try:
        count = prepare_teams(args.roster, args.output)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"{count} jamoa uchun arxivlar tayyor: {args.output / 'packages'}")
    print(f"Topshirilgan jamoa papkalarini shu yerga joylang: {args.output / 'submissions'}")


if __name__ == "__main__":
    main()
