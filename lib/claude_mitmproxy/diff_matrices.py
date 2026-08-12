#!/usr/bin/env python3
"""Diff two per-patch match matrices, reporting only cells that changed.

Rows and columns come and go between runs -- a promoted fixture adds a
column, a retired patch drops a row -- and those differences are not what
the diff is for. Only the intersection is compared; what only one side has
is listed as unshared and left alone.

Usage: diff_matrices.py BEFORE.txt AFTER.txt
"""

from __future__ import annotations

import re
import sys


def parse(path):
    lines = [ln for ln in open(path).read().splitlines() if ln and "WARNING" not in ln]
    cols = re.split(r" {2,}", lines[0].strip())
    rows = {}
    for line in lines[1:]:
        name, *cells = re.split(r" {2,}", line.strip())
        rows[name] = dict(zip(cols, cells))
    return rows


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    assert len(argv) == 2, "usage: diff_matrices.py BEFORE.txt AFTER.txt"
    a, b = parse(argv[0]), parse(argv[1])
    for name in sorted(set(a) & set(b)):
        for col in sorted(set(a[name]) & set(b[name])):
            if a[name][col] != b[name][col]:
                print(f"{name} {col}: {a[name][col]} -> {b[name][col]}")
    print("compared", len(set(a) & set(b)), "rows;", sorted(set(a) ^ set(b)), "unshared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
