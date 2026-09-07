#!/usr/bin/env python3
"""Compose this bundle from ./bundle.md and report what it contributes.

Proves two things at once, with no API call:
  1. The bundle still COMPOSES after `context/gitea-awareness.md` is deleted and
     the `context.include` entry is removed (load_bundle would raise otherwise).
  2. Exactly how many always-on context files this bundle contributes to a
     session head -- the number that must go 1 -> 0.

Usage:
    python3 compose_check.py [bundle-source]     # default: ./bundle.md
"""

from __future__ import annotations

import asyncio
import sys

from amplifier_foundation import load_bundle


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else "./bundle.md"
    bundle = asyncio.run(load_bundle(source, strict=True))

    # A namespaced context include ("gitea:context/x.md") is parked in
    # _pending_context until source_base_paths is populated; Bundle.context is
    # EMPTY until resolve_pending_context() runs. Reading .context without this
    # call reports 0 for a bundle that really does mount a file -- a confident,
    # plausible, wrong answer that still exits 0.
    pending = dict(getattr(bundle, "_pending_context", {}))
    bundle.resolve_pending_context()

    print(f"source                       : {source}")
    print("composed                     : OK (load_bundle strict=True returned)")
    print(f"bundle.description           : {bundle.description}")
    print(f"tools                        : {len(bundle.to_mount_plan().get('tools', []))}")
    print(f"pending context includes     : {len(pending)}")
    for name in pending:
        print(f"  - {name}")
    print(f"context files contributed    : {len(bundle.context)}")
    for name, path in bundle.context.items():
        print(f"  - {name} -> {path}  (exists={path.exists()})")
    if not bundle.context:
        print("  (none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
