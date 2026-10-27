#!/usr/bin/env python3
"""Validate local Markdown links and structured route targets in .ai/."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCOPES = (".ai/context", ".ai/retrieval", ".ai/instructions", ".ai/skills", ".ai/topology")
YAML_LIST_KEYS = {"paths", "entrypoints", "implementation", "guardrails", "start_with"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
YAML_KEY = re.compile(r"^(\s*)([A-Za-z0-9_-]+):\s*(?:#.*)?$")
YAML_ITEM = re.compile(r"^(\s*)-\s+(.+?)\s*$")


def is_external(target: str) -> bool:
    return target.startswith("//") or bool(urlsplit(target).scheme)


def local_target_path(source: Path, target: str) -> Path | None:
    target = target.strip()
    if not target or target.startswith("#") or is_external(target):
        return None

    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]

    target = unquote(urlsplit(target).path)
    if not target:
        return None
    if target.startswith("/"):
        return ROOT / target.lstrip("/")
    return source.parent / target


def markdown_errors() -> list[str]:
    errors = []
    for scope in SCOPES:
        for source in (ROOT / scope).rglob("*.md"):
            if source.name == "repo_map.md":
                continue
            text = source.read_text(encoding="utf-8-sig")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in MARKDOWN_LINK.finditer(line):
                    target = local_target_path(source, match.group(1))
                    if target is not None and not target.exists():
                        errors.append(
                            f"{source.relative_to(ROOT)}:{line_number}: "
                            f"missing Markdown target {match.group(1)!r}"
                        )
    return errors


def route_errors() -> list[str]:
    errors = []
    for source in (ROOT / ".ai/retrieval").glob("*.yaml"):
        list_indent = None
        for line_number, line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(), start=1):
            key_match = YAML_KEY.match(line)
            if key_match:
                indent, key = len(key_match.group(1)), key_match.group(2)
                list_indent = indent if key in YAML_LIST_KEYS else None
                continue

            item_match = YAML_ITEM.match(line)
            if item_match is None or list_indent is None or len(item_match.group(1)) <= list_indent:
                continue

            value = item_match.group(2).split(" #", maxsplit=1)[0].strip().strip("\"'")
            if not value or value.startswith("devops-playbook/") or "<" in value or ">" in value:
                continue

            target = ROOT / value.rstrip("/")
            if not target.exists():
                errors.append(
                    f"{source.relative_to(ROOT)}:{line_number}: "
                    f"missing route target {value!r}"
                )
    return errors


def main() -> int:
    errors = markdown_errors() + route_errors()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"Found {len(errors)} invalid intelligence path(s).", file=sys.stderr)
        return 1

    print("All local intelligence Markdown links and route targets exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
