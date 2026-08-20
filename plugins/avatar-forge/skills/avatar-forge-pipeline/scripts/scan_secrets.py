#!/usr/bin/env python3
"""Fail when Avatar Forge artifacts appear to contain credentials or private payloads."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MAX_FILE_BYTES = 2 * 1024 * 1024
SKIP_PARTS = {".git", "node_modules", "dist", ".next", ".vinext", ".wrangler", "__pycache__"}
PATTERNS = {
    "Tencent SecretId": re.compile(r"\bAKID[A-Za-z0-9]{24,}\b"),
    "API key": re.compile(r"\bsk[_-](?!test(?:-|_)|example|placeholder)[A-Za-z0-9_-]{20,}\b", re.IGNORECASE),
    "Bearer credential": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}\b", re.IGNORECASE),
    "assigned secret": re.compile(
        r"\b(?:LYCHEE_TTS_API_KEY|MIMO_API_KEY|RUNNINGHUB_API_KEY|COS_SECRET_ID|COS_SECRET_KEY)\b\s*[:=]\s*[\"'](?!test(?:-|_)|example|placeholder|your)[A-Za-z0-9_./+~-]{16,}",
        re.IGNORECASE,
    ),
    "dotenv secret": re.compile(
        r"^\s*(?:LYCHEE_TTS_API_KEY|MIMO_API_KEY|RUNNINGHUB_API_KEY|COS_SECRET_ID|COS_SECRET_KEY)\s*=\s*(?!test(?:-|_)|example|placeholder|your)[A-Za-z0-9_./+~-]{16,}\s*$",
        re.IGNORECASE,
    ),
    "signed COS URL": re.compile(r"[?&]q-signature=[0-9a-f]{40}\b", re.IGNORECASE),
    "embedded audio Base64": re.compile(r"data:audio/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/]{40,}={0,2}", re.IGNORECASE),
}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and not any(part in SKIP_PARTS for part in path.parts):
            yield path


def scan(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in iter_files(root):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((path, line_number, label))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    root = args.path.resolve()
    if not root.exists():
        parser.error(f"path does not exist: {root}")
    findings = scan(root)
    for path, line_number, label in findings:
        print(f"{path}:{line_number}: {label}", file=sys.stderr)
    if findings:
        print(f"FAILED: {len(findings)} potential secret(s) found", file=sys.stderr)
        return 1
    print(f"PASS: no credential material found under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
