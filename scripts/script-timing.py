#!/usr/bin/env python3
"""Check a pitch script's narration fits its time slots.

Sections are `## M:SS–M:SS · Title` headings; narration is lines starting with `> `.
Everything else (stage directions, notes) is ignored.

Usage: scripts/script-timing.py docs/pitch/af-hacks-script.md [--wpm 150]
"""
import argparse
import re
import sys

HEADING = re.compile(r"^##\s+(\d+):(\d{2})\s*[–-]\s*(\d+):(\d{2})\s*·\s*(.+)$")


def sections(text):
    current = None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            a, b, c, d, title = m.groups()
            current = {"title": title.strip(), "slot": (int(c) * 60 + int(d)) - (int(a) * 60 + int(b)), "words": 0}
            yield current
        elif current and line.startswith("> "):
            current["words"] += len(re.findall(r"[\w$%'’.-]+", line[2:]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--wpm", type=float, default=150)
    args = p.parse_args()
    rows = list(sections(open(args.path, encoding="utf-8").read()))
    total_words = total_slot = 0
    over = False
    for r in rows:
        spoken = r["words"] / args.wpm * 60
        flag = "OVER" if spoken > r["slot"] else ""
        over |= bool(flag)
        print(f"{r['title'][:34]:34} {r['words']:4} words  {spoken:5.1f}s spoken / {r['slot']:3}s slot  {flag}")
        total_words += r["words"]
        total_slot += r["slot"]
    print(f"{'TOTAL':34} {total_words:4} words  {total_words / args.wpm * 60:5.1f}s spoken / {total_slot:3}s slot")
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
