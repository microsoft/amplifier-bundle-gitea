#!/usr/bin/env python3
"""Head census: render the always-on <context_file> head with the SHIPPED renderer.

Why this exists
---------------
The lane must state the always-on context_file count before and after removing
`gitea:context/gitea-awareness.md`, and a count that changes without being named
is how a silent regression enters.

Method (costs $0, no API call)
------------------------------
BEFORE is taken from a REAL session's own `mentions:resolved` event
(source=bundle_context, turn 1) -- the authoritative list of context files the
app bundle actually mounted. Those exact resolved paths are then re-rendered
through the SHIPPED renderer (`amplifier_foundation.mentions.format_context_block`
over a `ContentDeduplicator`), which is the same function that produced the head
in that session. AFTER re-renders the identical set minus the one path this PR
removes.

This is a render measurement, not a second live API session: the $0 spend
authority for this item permits "a session render and a head census" and does not
fund a paid run.

Usage
-----
    python3 head_census.py <session-events.jsonl>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from amplifier_foundation.mentions import ContentDeduplicator
from amplifier_foundation.mentions import format_context_block

TARGET_MENTION = "gitea:context/gitea-awareness.md"


def first_bundle_context_resolution(events_path: Path) -> list[tuple[str, Path]]:
    """Return [(mention, resolved_path)] from the first bundle_context mentions:resolved."""
    with events_path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "mentions:resolved":
                continue
            data = event.get("data", {})
            if data.get("source") != "bundle_context":
                continue
            return [
                (r["mention"], Path(r["resolved_path"])) for r in data["resolutions"]
            ]
    raise SystemExit(f"no bundle_context mentions:resolved event in {events_path}")


def render(entries: list[tuple[str, Path]]) -> str:
    dedup = ContentDeduplicator()
    mention_to_path: dict[str, Path] = {}
    for mention, path in entries:
        dedup.add_file(path, path.read_text(encoding="utf-8"))
        mention_to_path[mention] = path
    return format_context_block(dedup, mention_to_path)


def report(label: str, entries: list[tuple[str, Path]]) -> tuple[int, int]:
    rendered = render(entries)
    blocks = rendered.count("<context_file ")
    print(f"{label}")
    print(f"  context_file blocks : {blocks}")
    print(f"  rendered head chars : {len(rendered)}")
    for i, (mention, _) in enumerate(entries, 1):
        marker = "  <-- TARGET" if mention == TARGET_MENTION else ""
        print(f"    {i:2d}. {mention}{marker}")
    print()
    return blocks, len(rendered)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    entries = first_bundle_context_resolution(Path(sys.argv[1]))

    before_blocks, before_chars = report("BEFORE (real session, as mounted)", entries)

    after_entries = [e for e in entries if e[0] != TARGET_MENTION]
    if len(after_entries) == len(entries):
        print(f"FAIL: {TARGET_MENTION} was not in the BEFORE set -- nothing to remove.")
        return 1
    after_blocks, after_chars = report(f"AFTER  (same set minus {TARGET_MENTION})", after_entries)

    print("DELTA")
    print(f"  context_file blocks : {before_blocks} -> {after_blocks}  ({after_blocks - before_blocks})")
    print(f"  rendered head chars : {before_chars} -> {after_chars}  ({after_chars - before_chars})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
