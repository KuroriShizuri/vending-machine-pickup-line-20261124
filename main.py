"""Entry writer for the make.fun competition "One Line, One Minute:
The Vending Machine Pickup Line".

Writes the single judged line to ``entry.txt`` inside the output
directory (``$MAKEFUN_OUTPUT_DIR`` when set, ``/output`` otherwise).
The file holds the entry bytes exactly, with no trailing newline.

Commands:
    python3 main.py              write entry.txt
    python3 main.py --check      validate the entry, write nothing
    python3 main.py --self-test  validate + prove a write/read round-trip
"""

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

ENTRY = "You don't need exact change — just press B7 and I'll drop something sweet, because my coil's been stuck on you since you walked by."

MIN_CHARS = 1
MAX_CHARS = 200
FILENAME = "entry.txt"


def entry_bytes() -> bytes:
    return ENTRY.encode("utf-8")


def entry_sha256() -> str:
    return hashlib.sha256(entry_bytes()).hexdigest()


def find_problems(text: str) -> list[str]:
    problems = []
    n = len(text)
    if n < MIN_CHARS:
        problems.append(f"entry too short: {n} chars (min {MIN_CHARS})")
    if n > MAX_CHARS:
        problems.append(f"entry too long: {n} chars (max {MAX_CHARS})")
    if not text.strip():
        problems.append("entry is empty or whitespace only")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "\n" in text or "\r" in text:
        problems.append("entry contains a line break")
    if "  " in text:
        problems.append("entry contains a double space")
    for ch in text:
        if ord(ch) < 0x20:
            problems.append(
                f"entry contains control character U+{ord(ch):04X}")
            break
    return problems


def resolve_output_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def write_entry(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / FILENAME
    with open(target, "wb") as handle:
        handle.write(entry_bytes())
    return target


def read_back(path: Path) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def check_entry() -> int:
    problems = find_problems(ENTRY)
    if problems:
        print("check FAIL:", "; ".join(problems), file=sys.stderr)
        return 1
    print(f"check OK: {len(ENTRY)} chars, single line")
    return 0


def run_self_test() -> int:
    if check_entry():
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        target = write_entry(Path(tmp))
        on_disk = read_back(target)
        if on_disk != entry_bytes():
            print("self-test FAIL: bytes on disk differ", file=sys.stderr)
            return 1
        if on_disk.decode("utf-8") != ENTRY:
            print("self-test FAIL: text on disk differs", file=sys.stderr)
            return 1
    with tempfile.TemporaryDirectory() as tmp2:
        second = write_entry(Path(tmp2))
        if hashlib.sha256(read_back(second)).hexdigest() != entry_sha256():
            print("self-test FAIL: second write hash differs",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {len(ENTRY)} chars, sha256 {entry_sha256()[:12]}, "
          "two writes agree")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Write the competition entry to entry.txt.",
    )
    parser.add_argument("--out", metavar="DIR",
                        help="output directory (overrides $MAKEFUN_OUTPUT_DIR)")
    parser.add_argument("--check", action="store_true",
                        help="validate the entry only")
    parser.add_argument("--self-test", action="store_true",
                        help="validate and round-trip the entry in a temp dir")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return check_entry()
    if args.self_test:
        return run_self_test()
    if check_entry():
        return 1
    target = write_entry(resolve_output_dir(args.out))
    if read_back(target) != entry_bytes():
        print(f"read-back mismatch: {target}", file=sys.stderr)
        return 1
    print(f"wrote {target} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
