"""Verify the artifact repo: the first `sdlc-ci` check. Exits 1 and lists every problem it finds.

- guardrails/ exists and holds at least one standards file
- every JSON and YAML file parses
- no merge-conflict markers in any text file
- ADR files are named NNNN-title.md and declare a status

    python scripts/verify_artifacts.py [repo-root]
"""

import json
import re
import sys
from pathlib import Path

import yaml

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".py"}
CONFLICT = re.compile(r"^(<<<<<<< |=======$|>>>>>>> )", re.M)
ADR_NAME = re.compile(r"^\d{4}-[a-z0-9][a-z0-9-]*\.md$")


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            yield path


def verify(root: Path) -> list[str]:
    problems = []
    guardrails = root / "guardrails"
    if not guardrails.is_dir() or not any(guardrails.glob("*.md")):
        problems.append("guardrails/ must exist and hold at least one .md standards file")
    for path in files(root):
        rel = path.relative_to(root).as_posix()
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        if CONFLICT.search(text):
            problems.append(f"{rel}: merge-conflict markers")
        try:
            if path.suffix == ".json":
                json.loads(text)
            elif path.suffix in (".yaml", ".yml"):
                yaml.safe_load(text)
        except (ValueError, yaml.YAMLError) as e:
            problems.append(f"{rel}: does not parse ({str(e).splitlines()[0]})")
        if path.parent.name == "adr" and path.suffix == ".md":
            if not ADR_NAME.match(path.name):
                problems.append(f"{rel}: ADR files are named NNNN-short-title.md")
            if not re.search(r"^- Status: \S", text, re.M):
                problems.append(f"{rel}: ADR has no '- Status:' line")
    return problems


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    problems = verify(root)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("artifact repo verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
