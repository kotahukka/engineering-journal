#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
from typing import List, Tuple

DOCS_ROOT = pathlib.Path("docs")
INDEX_FILE = DOCS_ROOT / "index.md"
MAX_ITEMS = 8

START = "<!-- RECENT_DOCS_START -->"
END = "<!-- RECENT_DOCS_END -->"


def title_of(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def collect_docs() -> List[Tuple[float, pathlib.Path]]:
    files: List[Tuple[float, pathlib.Path]] = []
    for p in DOCS_ROOT.rglob("*.md"):
        if p.name == "index.md":
            continue
        files.append((p.stat().st_mtime, p))
    files.sort(reverse=True)
    return files[:MAX_ITEMS]


def main() -> None:
    if not INDEX_FILE.exists():
        raise SystemExit(f"Missing {INDEX_FILE}")

    docs = collect_docs()
    lines = []
    for _, p in docs:
        title = title_of(p)
        link = str(p).replace("\\", "/")  # windows safety
        lines.append(f"- [{title}]({link})")

    index_text = INDEX_FILE.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        flags=re.S,
    )
    block = START + "\n" + "\n".join(lines) + "\n" + END

    if not pattern.search(index_text):
        raise SystemExit(f"Missing markers in {INDEX_FILE}:\n{START}\n{END}")

    new_text = pattern.sub(block, index_text)
    INDEX_FILE.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
