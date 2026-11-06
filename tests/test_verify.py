import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from verify_artifacts import verify  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def make(tmp_path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def test_this_repo_verifies():
    assert verify(REPO) == []


def test_missing_guardrails_is_reported(tmp_path):
    assert any("guardrails/" in p for p in verify(make(tmp_path, {"README.md": "x"})))


def test_broken_json_and_yaml_are_reported(tmp_path):
    root = make(tmp_path, {"guardrails/a.md": "x", "sdlc/INT-1/plan.json": "{oops", "sdlc/INT-1/x.yaml": "a: [1"})
    problems = verify(root)
    assert any("plan.json" in p for p in problems) and any("x.yaml" in p for p in problems)


def test_conflict_markers_are_reported(tmp_path):
    root = make(tmp_path, {"guardrails/a.md": "x\n<<<<<<< HEAD\ny\n=======\nz\n>>>>>>> main\n"})
    assert any("merge-conflict" in p for p in verify(root))


def test_adr_name_and_status_are_checked(tmp_path):
    root = make(tmp_path, {"guardrails/a.md": "x", "guardrails/adr/bad name.md": "no status here"})
    problems = verify(root)
    assert any("NNNN-short-title" in p for p in problems) and any("Status" in p for p in problems)
