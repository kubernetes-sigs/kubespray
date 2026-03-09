#!/usr/bin/env python3
"""Drift detector for plugins/strategy/graceful_rolling.py.

graceful_rolling.run() is a deliberate copy of free.StrategyModule.run()
(ansible-core) with five targeted modifications (marked ``# GR:``).  Because
the copy cannot be avoided — ansible-core provides no override points inside
the free strategy loop — this script makes the debt *visible*: it fails CI
whenever the upstream source changes so that a human can review the diff and
decide whether graceful_rolling.run() needs updating.

Usage:
    # Check only (exit 1 if hash has drifted):
    python tests/scripts/check_free_strategy_drift.py

    # Update the pinned hash after reviewing and accepting upstream changes:
    python tests/scripts/check_free_strategy_drift.py --update
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Path to the pinned-hash record, relative to the repo root.
_HASH_FILE = Path(__file__).resolve().parents[2] / "tests" / "scripts" / "free_strategy_run_hash.txt"

# The full path to the installed free strategy module.
_FREE_STRATEGY = (
    Path(importlib.util.find_spec("ansible").origin).parent
    / "plugins" / "strategy" / "free.py"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_run_source(path: Path) -> tuple[str, int, int]:
    """Return (source_text, first_line, last_line) of StrategyModule.run()."""
    src = path.read_text()
    tree = ast.parse(src)
    lines = src.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "StrategyModule":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "run":
                body = "\n".join(lines[item.lineno - 1 : item.end_lineno])
                return body, item.lineno, item.end_lineno
    raise RuntimeError(f"StrategyModule.run() not found in {path}")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Overwrite the pinned hash with the current upstream value.",
    )
    args = parser.parse_args()

    if not _FREE_STRATEGY.exists():
        print(f"ERROR: {_FREE_STRATEGY} not found — is ansible-core installed?", file=sys.stderr)
        return 2

    body, first_line, last_line = _extract_run_source(_FREE_STRATEGY)
    current_hash = _digest(body)

    import ansible
    ansible_version = getattr(ansible, "__version__", "unknown")

    if args.update:
        _HASH_FILE.write_text(f"{current_hash}  # ansible {ansible_version} free.run() L{first_line}-{last_line}\n")
        print(f"Updated {_HASH_FILE.name}:")
        print(f"  ansible {ansible_version}")
        print(f"  free.run() L{first_line}-{last_line}  ({last_line - first_line + 1} lines)")
        print(f"  SHA256: {current_hash}")
        return 0

    if not _HASH_FILE.exists():
        print(
            f"ERROR: {_HASH_FILE} missing.\n"
            f"Run with --update to create it for the first time.",
            file=sys.stderr,
        )
        return 2

    pinned_line = _HASH_FILE.read_text().strip()
    pinned_hash = pinned_line.split()[0]

    if current_hash == pinned_hash:
        print(f"OK: free.StrategyModule.run() unchanged  (ansible {ansible_version})")
        return 0

    print(
        "DRIFT DETECTED — free.StrategyModule.run() has changed since the hash was pinned.\n"
        "\n"
        "graceful_rolling.run() is a copy of this method with five GR: modifications.\n"
        "You must:\n"
        "  1. diff the new free.StrategyModule.run() against the old one:\n"
        "       git diff HEAD requirements.txt   # find the ansible-core version bump\n"
        "       python3 - <<'EOF'\n"
        "       import inspect; from importlib import import_module\n"
        "       m = import_module('ansible.plugins.strategy.free')\n"
        "       print(inspect.getsource(m.StrategyModule.run))\n"
        "       EOF\n"
        "  2. Apply any relevant changes to plugins/strategy/graceful_rolling.py,\n"
        "     keeping the GR: modifications intact.\n"
        "  3. Re-run with --update to accept the new hash:\n"
        "       python tests/scripts/check_free_strategy_drift.py --update\n"
        "\n"
        f"  Pinned:  {pinned_hash}  ({pinned_line})\n"
        f"  Current: {current_hash}  (ansible {ansible_version}, L{first_line}-{last_line})",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
