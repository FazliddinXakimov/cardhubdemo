"""Har jamoaning topshirgan loyihasini alohida tekshirish va baholarni jamlash."""

import argparse
import csv
import html
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .prepare_teams import load_roster
else:
    from prepare_teams import load_roster

CHECKER = Path(__file__).with_name("run_checks.py")
LIMITS = {"report": 15, "code_tests": 10, "demo": 5}
IGNORED = {"__pycache__", ".git", ".venv", "venv", ".DS_Store"}


def load_manual(path, teams):
    """Bo'sh baho hali qo'yilmagan; 0 esa hakam bergan haqiqiy baho."""
    scores = {}
    if not path.exists():
        return scores
    team_ids = {team["team_id"] for team in teams}
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        expected = {"team_id", "report", "code_tests", "demo", "notes"}
        if len(reader.fieldnames or []) != len(expected) or set(reader.fieldnames) != expected:
            raise ValueError("manual_scores.csv ustunlari: team_id,report,code_tests,demo,notes")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Baholash CSVsi: {reader.line_num}-qatorda ustunlar soni noto'g'ri.")
            team_id = row["team_id"].strip()
            if team_id not in team_ids or team_id in scores:
                raise ValueError(f"Baholash CSVsi: noma'lum yoki takrorlangan ID: {team_id}")
            grade = {"notes": row["notes"].strip()}
            for key, maximum in LIMITS.items():
                raw = row[key].strip()
                if raw and (not raw.isascii() or not raw.isdigit() or int(raw) > maximum):
                    raise ValueError(f"{team_id}: {key} uchun 0..{maximum} butun ball yoki bo'sh qiymat kerak.")
                grade[key] = int(raw) if raw else None
            scores[team_id] = grade
    return scores


def validate_submission(folder, team_id):
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError("Jamoa topshirig'i oddiy papka bo'lishi kerak.")
    project = folder / "project"
    if not (project / "bank.py").is_file():
        raise ValueError("project/bank.py topilmadi. Jamoa arxivini submissions/<team_id>/ ichiga oching.")
    for path in folder.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("Topshiriqda ramziy havola yoki maxsus fayl bor.")
    metadata = folder / "TEAM.json"
    if metadata.exists():
        value = json.loads(metadata.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("team_id") != team_id:
            raise ValueError("TEAM.json dagi ID jamoa papkasiga mos emas.")
    return project


def run_checker(project, log_path, timeout):
    """Asl topshiriqqa tegmasdan, vaqtinchalik nusxani alohida jarayonda ishlatish."""
    with tempfile.TemporaryDirectory(prefix="cardlab-check-") as temporary:
        temporary = Path(temporary)
        copied = temporary / "project"
        shutil.copytree(project, copied, ignore=lambda _directory, names: set(names) & IGNORED)
        result_path = temporary / "checks.json"
        command = [sys.executable, "-B", str(CHECKER), str(copied), "--json-output", str(result_path)]
        # Jamoa kodi uchun server kalitlari va boshqa muhit sozlamalari kerak emas.
        environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "LANG") if key in os.environ}
        environment.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=copied, stdout=log, stderr=subprocess.STDOUT,
                                       env=environment, start_new_session=os.name == "posix")
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                reason = f"Tekshirish {timeout:g} soniyalik muddatdan oshdi."
                return "timeout", None, reason
            finally:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif process.poll() is None:
                    process.kill()
                process.wait()
        if not result_path.exists():
            return "error", None, f"Tekshiruvchi natija yozmadi (chiqish kodi: {returncode}). Logni ko'ring."
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if not isinstance(result, dict) or result.get("schema_version") != 1:
            return "error", None, "Tekshiruvchi noto'g'ri natija shaklini qaytardi."
        if result.get("status") == "error":
            return "error", result, result.get("error") or "Loyihani yuklab bo'lmadi."
        score = result.get("functional_score")
        if (returncode not in (0, 1) or result.get("status") != "checked"
                or type(score) is not int or not 0 <= score <= 70
                or type(result.get("regression_passed")) is not bool
                or not isinstance(result.get("groups"), list)):
            return "error", None, "Tekshiruv tugallanmagan yoki natija shakli noto'g'ri."
        return "checked", result, None


def evaluate_team(team, event, scores, logs, timeout):
    team_id = team["team_id"]
    grade = scores.get(team_id, {})
    result = dict(team, status="missing", functional_score=None, regression_passed=False,
                  total=None, rank=None, checks=None, error=None, warnings=[],
                  log=f"logs/{team_id}.log", notes=grade.get("notes", ""))
    result.update({key: grade.get(key) for key in LIMITS})
    result["manual_ready"] = all(result[key] is not None for key in LIMITS)
    folder = event / "submissions" / team_id
    log_path = logs / f"{team_id}.log"
    if not folder.exists() and not folder.is_symlink():
        result["error"] = "Jamoa hali ish topshirmagan."
    else:
        try:
            project = validate_submission(folder, team_id)
        except (ValueError, OSError) as error:
            result.update(status="invalid", error=str(error))
        else:
            if not (folder / "HISOBOT.md").is_file():
                result["warnings"].append("HISOBOT.md topshirilmagan.")
            if not (folder / "TEAM.json").is_file():
                result["warnings"].append("TEAM.json yo'q; jamoa papka nomi bo'yicha aniqlandi.")
            try:
                status, checks, error = run_checker(project, log_path, timeout)
                result.update(status=status, checks=checks, error=error)
            except (OSError, ValueError) as error:
                result.update(status="error", error=str(error))
            if result["status"] == "checked":
                result["functional_score"] = result["checks"]["functional_score"]
                result["regression_passed"] = result["checks"]["regression_passed"]
                if not result["regression_passed"]:
                    result["warnings"].append("Regressiya xatosi: hakam qayta ko'rib chiqishi kerak; yakuniy o'rin berilmadi.")
                if result["manual_ready"] and result["regression_passed"]:
                    result["total"] = result["functional_score"] + sum(result[key] for key in LIMITS)
    if result["error"]:
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n" + result["error"] + "\n")
    return result


def assign_ranks(results):
    ranked = sorted((row for row in results if row["total"] is not None),
                    key=lambda row: (-row["total"], -row["functional_score"], -row["report"], row["team_id"]))
    previous, rank = None, None
    for position, row in enumerate(ranked, 1):
        key = (row["total"], row["functional_score"], row["report"])
        if key != previous:
            rank = position
        row["rank"] = rank
        previous = key
    return ranked + [row for row in results if row["total"] is None]


def csv_value(value):
    # Jadval dasturida jamoa nomi yoki izoh formula sifatida bajarilmasin.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def cell(value):
    if value is None:
        return "—"
    text = html.escape(str(value)).replace("\r", " ").replace("\n", " ")
    for special in ("\\", "|", "*", "_", "[", "]", "`"):
        text = text.replace(special, "\\" + special)
    return text


def state(row):
    labels = {"missing": "Topshirilmagan", "invalid": "Tuzilishi noto'g'ri", "error": "Tekshiruv xatosi", "timeout": "Vaqt tugadi"}
    if row["status"] != "checked":
        return labels[row["status"]]
    if not row["regression_passed"]:
        return "Hakam tekshiruvi kerak"
    return "Baholandi" if row["manual_ready"] else "Hakam bahosi kutilmoqda"


def write_reports(destination, results):
    payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "teams": results}
    (destination / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["rank", "team_id", "team_name", "status", "functional_score", "report", "code_tests", "demo", "total",
              "regression_passed", "manual_ready", "notes", "error"]
    with (destination / "results.csv").open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: csv_value(row[key]) for key in fields} for row in results)
    lines = ["# CardLab — jamoalar natijalari", "",
             "Funksional: 70, hisobot: 15, testlar va kod: 10, namoyish: 5 ball. `—` hali baholanmagan qiymat.", "",
             "O'rin faqat tekshiruv tugagan, regressiya testlari o'tgan va hakamning uchala bahosi kiritilgan jamoalarga beriladi.",
             "Tenglik: jami ball, funksional ball, hisobot bali; barchasi teng bo'lsa, teng o'rin.", "",
             "| O'rin | Jamoa | Funksional /70 | Hisobot /15 | Test/kod /10 | Namoyish /5 | Jami /100 | Holat |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    for row in results:
        values = [row["rank"], f'{row["team_id"]} · {row["team_name"]}', row["functional_score"],
                  row["report"], row["code_tests"], row["demo"], row["total"], state(row)]
        lines.append("| " + " | ".join(cell(value) for value in values) + " |")
    lines.extend(["", "## Tekshiruv tafsilotlari", ""])
    for row in results:
        lines.append(f'- **{cell(row["team_id"])}**: [tekshiruv logi]({row["log"]}).')
        messages = [row["error"], *row["warnings"], row["notes"]]
        lines.extend(f"  {cell(message)}" for message in messages if message)
    (destination / "leaderboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Vaqt musbat son bo'lishi kerak.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True, help="prepare_teams.py yaratgan tadbir papkasi")
    parser.add_argument("--output", type=Path, help="Yangi yoki bo'sh natijalar papkasi (standart: EVENT/results)")
    parser.add_argument("--timeout", type=positive_seconds, default=20, help="Har jamoaga tekshiruv soniyalari (standart: 20)")
    args = parser.parse_args(argv)
    try:
        event = args.event.resolve()
        teams = load_roster(event / "teams.csv")
        scores = load_manual(event / "manual_scores.csv", teams)
        destination = args.output or event / "results"
        if destination.is_symlink() or (destination.exists() and (not destination.is_dir() or any(destination.iterdir()))):
            raise ValueError("Natijalar papkasi bo'sh bo'lishi kerak. Yangi --output yo'lini tanlang.")
        destination = destination.resolve()
        submissions = event / "submissions"
        if submissions.is_symlink() or (submissions.exists() and not submissions.is_dir()):
            raise ValueError("submissions oddiy papka bo'lishi kerak.")
        if destination == submissions or submissions in destination.parents:
            raise ValueError("Natijalarni submissions ichiga yozib bo'lmaydi.")
        destination.mkdir(parents=True, exist_ok=True)
        logs = destination / "logs"
        logs.mkdir()
        results = []
        for team in teams:
            result = evaluate_team(team, event, scores, logs, args.timeout)
            results.append(result)
            score = result["functional_score"]
            print(f'{team["team_id"]}: {state(result)}; funksional {score if score is not None else "—"}/70', flush=True)
        write_reports(destination, assign_ranks(results))
        print(f"Natijalar: {destination / 'leaderboard.md'}")
        return 0 if all(row["status"] == "checked" for row in results) else 1
    except (OSError, ValueError, csv.Error) as error:
        print(f"Xato: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
