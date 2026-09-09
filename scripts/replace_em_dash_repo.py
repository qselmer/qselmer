from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = chr(0x2014)
REPLACEMENT = "-"


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def main() -> None:
    changed_files: list[str] = []
    replacements = 0

    for path in tracked_files():
        if not path.is_file():
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        count = text.count(TARGET)
        if not count:
            continue
        path.write_text(text.replace(TARGET, REPLACEMENT), encoding="utf-8")
        changed_files.append(str(path.relative_to(ROOT)))
        replacements += count

    print(f"Replaced {replacements} em-dash characters across {len(changed_files)} tracked UTF-8 files.")
    for name in changed_files:
        print(name)


if __name__ == "__main__":
    main()
