"""Sync provider-neutral agent specs into host-specific adapter directories."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def sync_claude_agents(source: Path, claude_agents_dir: Path) -> list[Path]:
    claude_agents_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(source.glob("*.md")):
        target = claude_agents_dir / path.name
        shutil.copyfile(path, target)
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync universal agent specs to adapter-specific directories.")
    parser.add_argument("--source", default="agent_specs/agents")
    parser.add_argument("--claude-agents-dir", default=".claude/agents")
    args = parser.parse_args()

    written = sync_claude_agents(Path(args.source), Path(args.claude_agents_dir))
    print(f"synced {len(written)} Claude agent adapter files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
