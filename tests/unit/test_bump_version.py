import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bump_version import (
    classify_bump,
    git_commit_messages,
    next_version,
    read_current_version,
    read_version_from_git,
    write_version,
)


@pytest.mark.parametrize(
    ("messages", "expected"),
    [
        (["fix: correct off-by-one error"], "patch"),
        (["feat: add export button"], "minor"),
        (["feat: add export button", "fix: correct off-by-one error"], "minor"),
        (["docs: update readme", "chore: bump dep", "test: add case"], None),
        (["feat!: drop legacy endpoint"], "major"),
        (["feat(api): add endpoint\n\nBREAKING CHANGE: removes old field"], "major"),
        ([], None),
    ],
)
def test_classify_bump(messages: list[str], expected: str | None) -> None:
    assert classify_bump(messages) == expected


@pytest.mark.parametrize(
    ("current", "bump", "expected"),
    [
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
    ],
)
def test_next_version(current: str, bump: str, expected: str) -> None:
    assert next_version(current, bump) == expected


def test_next_version_rejects_unknown_bump() -> None:
    with pytest.raises(ValueError):
        next_version("1.0.0", "epic")


def test_read_and_write_version_round_trip(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\nversion = "0.1.0"\ndescription = "x"\n')

    assert read_current_version(pyproject) == "0.1.0"

    write_version(pyproject, "0.2.0")

    assert read_current_version(pyproject) == "0.2.0"
    assert 'name = "demo"' in pyproject.read_text()


def test_read_current_version_missing_line_raises(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\n')

    with pytest.raises(ValueError):
        read_current_version(pyproject)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_git_commit_messages_strips_leading_newline_from_bodied_commits(
    tmp_path: Path,
) -> None:
    # Regression test: a naive `git log --format=%B%x00` leaves a stray leading
    # "\n" on every message after the first once split on the NUL separator,
    # which silently breaks the `^feat:`/`^fix:` anchor match in classify_bump.
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "a.txt").write_text("1")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-q", "-m", "chore: initial commit")
    (repo / "a.txt").write_text("2")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-q", "-m", "fix: correct behavior\n\nSigned-off-by: Test <t@example.com>")

    messages = git_commit_messages("HEAD~1..HEAD", cwd=repo)

    assert len(messages) == 1
    assert messages[0].startswith("fix: correct behavior")
    assert classify_bump(messages) == "patch"


@pytest.fixture
def pr_repo(tmp_path: Path) -> Path:
    """A repo with a `main` branch (version 0.1.0) and a `feature` branch with one
    `feat:` commit, mimicking the state version-bump.yml runs against on a real PR.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "0.1.0"\n')
    _git(repo, "add", "pyproject.toml")
    _git(repo, "commit", "-q", "-m", "chore: initial commit")
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "app.py").write_text("print('hi')\n")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "feat: add greeting")
    return repo


def _run_bump_cli(repo: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts" / "bump_version.py"
    return subprocess.run(
        [sys.executable, str(script), *extra_args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_read_version_from_git_reads_ref_without_checkout(pr_repo: Path) -> None:
    assert read_version_from_git("main", "pyproject.toml", cwd=pr_repo) == "0.1.0"
    # Bump the branch's working copy; the git-ref read of `main` must be unaffected.
    write_version(pr_repo / "pyproject.toml", "0.2.0")
    assert read_version_from_git("main", "pyproject.toml", cwd=pr_repo) == "0.1.0"


def test_bump_cli_applies_bump_from_pr_commits(pr_repo: Path) -> None:
    result = _run_bump_cli(pr_repo, "main..feature", "--base-ref", "main", "--apply")

    assert result.returncode == 0, result.stderr
    assert "bump=minor" in result.stdout
    assert read_current_version(pr_repo / "pyproject.toml") == "0.2.0"


def test_bump_cli_is_idempotent_on_rerun(pr_repo: Path) -> None:
    first = _run_bump_cli(pr_repo, "main..feature", "--base-ref", "main", "--apply")
    assert first.returncode == 0, first.stderr

    _git(pr_repo, "add", "pyproject.toml")
    _git(pr_repo, "commit", "-q", "-m", "chore(release): bump version to 0.2.0")

    second = _run_bump_cli(pr_repo, "main..feature", "--base-ref", "main", "--apply")

    assert second.returncode == 0, second.stderr
    assert "already-applied" in second.stdout
    assert read_current_version(pr_repo / "pyproject.toml") == "0.2.0"
