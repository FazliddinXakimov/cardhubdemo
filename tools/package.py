"""Faqat belgilangan materiallardan ikkita tarqatish arxivini yaratish."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_FILES = [
    "START_HERE.md", "BT.pdf", "BT.md", "HISOBOT.md", "transfer.bpmn", "transfer-bpmn.svg",
    "project/README.md", "project/app.py", "project/bank.py", "project/test_smoke.py",
    "project/web.py", "project/style.css",
]


def package():
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    participant = destination / "cardlab-participant.zip"
    organizer = destination / "cardlab-organizer.zip"
    with ZipFile(participant, "w", ZIP_DEFLATED) as archive:
        for name in PARTICIPANT_FILES:
            archive.write(ROOT / "participant" / name, "cardlab-participant/" + name)
    with ZipFile(organizer, "w", ZIP_DEFLATED) as archive:
        archive.write(ROOT / "README.md", "cardlab-organizer/README.md")
        for name in ["Dockerfile", "compose.yaml", ".dockerignore"]:
            archive.write(ROOT / name, "cardlab-organizer/" + name)
        for name in PARTICIPANT_FILES:
            archive.write(ROOT / "participant" / name, "cardlab-organizer/participant/" + name)
        for folder in ["organizer", "tools"]:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and path.suffix in (".md", ".py") and "__pycache__" not in path.parts and "data" not in path.parts:
                    archive.write(path, "cardlab-organizer/" + str(path.relative_to(ROOT)))
    with ZipFile(participant) as archive:
        expected = {"cardlab-participant/" + name for name in PARTICIPANT_FILES}
        assert set(archive.namelist()) == expected
        assert archive.testzip() is None
    with ZipFile(organizer) as archive:
        assert archive.testzip() is None
    for path in (participant, organizer):
        print(f"{path.name}: {path.stat().st_size:,} bayt")


if __name__ == "__main__":
    package()
