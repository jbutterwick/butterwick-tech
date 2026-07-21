#!/usr/bin/env python3
"""Normalize generated HTML and XML so builds do not add trailing whitespace."""

from __future__ import annotations

import argparse
from pathlib import Path


def normalize_html_tree(root: Path) -> int:
    changed = 0
    generated_text_files = (
        path for path in root.rglob("*") if path.suffix in {".html", ".xml"}
    )
    for path in sorted(generated_text_files):
        original = path.read_text(encoding="utf-8")
        normalized = "\n".join(line.rstrip() for line in original.splitlines()) + "\n"
        if normalized != original:
            path.write_text(normalized, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("public"))
    args = parser.parse_args()
    changed = normalize_html_tree(args.root.resolve())
    print(f"Normalized {changed} generated HTML/XML file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
