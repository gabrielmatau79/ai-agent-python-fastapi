"""Compute the next semantic version from Conventional Commits and apply it to pyproject.toml.

Used by .github/workflows/version-bump.yml; kept as a standalone, unit-testable
module rather than inline workflow shell script so the bump logic itself can be
verified with pytest independently of CI.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

VERSION_LINE_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$', re.MULTILINE)
BREAKING_RE = re.compile(r"BREAKING CHANGE|^\w+(?:\(.+\))?!:", re.MULTILINE)
FEAT_RE = re.compile(r"^feat(?:\(.+\))?:")
FIX_RE = re.compile(r"^fix(?:\(.+\))?:")

BumpType = str  # "major" | "minor" | "patch"


def classify_bump(commit_messages: list[str]) -> BumpType | None:
    """Return the highest-priority bump implied by a list of full commit messages.

    Only `feat`/`fix`/breaking-change commits are release-worthy (matches the
    Conventional Commits convention already used in this repo's history);
    `docs:`, `chore:`, `test:`, etc. never trigger a version bump on their own.
    """
    has_feat = False
    has_fix = False
    for message in commit_messages:
        if BREAKING_RE.search(message):
            return "major"
        if FEAT_RE.match(message):
            has_feat = True
        elif FIX_RE.match(message):
            has_fix = True
    if has_feat:
        return "minor"
    if has_fix:
        return "patch"
    return None


def next_version(current: str, bump: BumpType) -> str:
    major, minor, patch = (int(part) for part in current.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump type: {bump!r}")


def _extract_version(text: str, source: str) -> str:
    match = VERSION_LINE_RE.search(text)
    if not match:
        raise ValueError(f"could not find a version line in {source}")
    return ".".join(match.groups())


def read_current_version(pyproject_path: Path) -> str:
    return _extract_version(pyproject_path.read_text(), str(pyproject_path))


def read_version_from_git(ref: str, path: str = "pyproject.toml") -> str:
    """Read the version line from `path` as it exists at `ref`, without checking it out.

    Used to get the pre-PR baseline version (e.g. "origin/main") even when the
    PR branch's own pyproject.toml has already been bumped by a prior run of
    this workflow, so re-runs compute the bump from the same baseline instead
    of stacking another bump on top of an already-applied one.
    """
    text = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return _extract_version(text, f"{ref}:{path}")


def write_version(pyproject_path: Path, new_version: str) -> None:
    text = pyproject_path.read_text()
    new_text, count = VERSION_LINE_RE.subn(f'version = "{new_version}"', text, count=1)
    if count != 1:
        raise ValueError(f"could not find a version line in {pyproject_path}")
    pyproject_path.write_text(new_text)


def git_commit_messages(commit_range: str) -> list[str]:
    # "format:" (not the "%x00"-only default "tformat:") avoids git auto-appending
    # a trailing newline per entry, which would otherwise land as a leading "\n"
    # on every message after this one once split on the NUL separator.
    output = subprocess.run(
        ["git", "log", "--format=format:%B%x00", commit_range],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [chunk.strip() for chunk in output.split("\x00") if chunk.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit_range", help="git rev range to inspect, e.g. origin/main..HEAD")
    parser.add_argument("--pyproject", default=Path("pyproject.toml"), type=Path)
    parser.add_argument(
        "--base-ref",
        help=(
            "git ref to read the baseline version from (e.g. origin/main) instead of "
            "--pyproject; makes re-runs on an already-bumped branch idempotent"
        ),
    )
    parser.add_argument(
        "--apply", action="store_true", help="write the computed version to --pyproject"
    )
    args = parser.parse_args()

    baseline_version = (
        read_version_from_git(args.base_ref, str(args.pyproject))
        if args.base_ref
        else read_current_version(args.pyproject)
    )
    bump = classify_bump(git_commit_messages(args.commit_range))

    if bump is None:
        print(f"bump=none current={baseline_version}")
        return 0

    target_version = next_version(baseline_version, bump)
    current_in_branch = read_current_version(args.pyproject)

    if current_in_branch == target_version:
        print(f"bump={bump} current={current_in_branch} next={target_version} already-applied")
        return 0

    print(
        f"bump={bump} baseline={baseline_version} "
        f"current={current_in_branch} next={target_version}"
    )
    if args.apply:
        write_version(args.pyproject, target_version)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
