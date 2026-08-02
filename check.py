#!/usr/bin/env python3
"""Validate the trip HTML files before they deploy to GitHub Pages.

There is no CI on this repo and pushing to main publishes immediately, so this
script is the only gate. Checks:

  1. HTML tag balance
  2. Syntax of every embedded <script> block (needs node on PATH)
  3. Every accommodation card's data-opt has matching labels[] and nums[] entries
     -- a card missing from nums silently vanishes from the budget total

Usage: python check.py
Exits 1 if anything fails.
"""
import pathlib
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

VOID = {'br', 'img', 'meta', 'link', 'input', 'hr', 'path', 'polyline',
        'line', 'circle', 'area', 'source', 'col', 'embed', 'track', 'wbr'}

errors = []


class Balance(HTMLParser):
    """Track open tags and report the first mismatch per element."""

    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            errors.append(f"mismatched </{tag}>, expected </{self.stack[-1]}>")
            while self.stack and self.stack.pop() != tag:
                pass


def check_balance(path, src):
    parser = Balance()
    parser.feed(src)
    if parser.stack:
        errors.append(f"{path}: unclosed tags {parser.stack}")


def check_js(path, src):
    js = '\n'.join(re.findall(r'<script>(.*?)</script>', src, re.S))
    if not js.strip():
        return
    tmp = None
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                         encoding='utf-8') as handle:
            handle.write(js)
            tmp = handle.name
        result = subprocess.run(['node', '--check', tmp],
                                capture_output=True, text=True)
        if result.returncode:
            errors.append(f"{path}: JS syntax error\n{result.stderr.strip()}")
    except FileNotFoundError:
        print("warning: node not on PATH, skipping JS syntax check",
              file=sys.stderr)
    finally:
        if tmp:
            pathlib.Path(tmp).unlink(missing_ok=True)


def check_card_tables(path, src):
    """Each card's data-opt must exist in both labels{} and nums{}."""
    cards = re.findall(r'data-loc="(\w+)"\s+data-opt="(\d+)"', src)
    if not cards:
        return

    tables = {}
    for name in ('labels', 'nums'):
        match = re.search(rf'const {name}\s*=\s*\{{(.*?)\n\}};', src, re.S)
        if match:
            tables[name] = match.group(1)

    for name in ('labels', 'nums'):
        if name not in tables:
            errors.append(f"{path}: has cards but no const {name}={{...}} table")

    for loc, opt in cards:
        for name, body in tables.items():
            entry = re.search(rf'\b{loc}\s*:\s*\{{([^}}]*)\}}', body)
            if not entry:
                errors.append(f"{path}: location '{loc}' missing from {name}")
            elif not re.search(rf'(^|[,{{\s]){opt}\s*:', entry.group(1)):
                errors.append(
                    f"{path}: card {loc}/{opt} missing from {name} "
                    f"(it will drop out of the budget total)")


def main():
    root = pathlib.Path(__file__).parent
    files = sorted(root.glob('*.html'))
    if not files:
        print("no HTML files found", file=sys.stderr)
        return 1

    for path in files:
        src = path.read_text(encoding='utf-8')
        name = path.name
        check_balance(name, src)
        check_js(name, src)
        check_card_tables(name, src)

    if errors:
        print('\n'.join(errors))
        return 1
    print(f"OK: {len(files)} HTML files consistent")
    return 0


if __name__ == '__main__':
    sys.exit(main())
