from __future__ import annotations

from pathlib import Path

from .models import ProjectModel, ValidationIssue, WorkspaceModel
from .parsing import load_pylock, normalize_name
from .planner import is_valid_pylock_name, plan_targets
from .sync import build_lock_document


def validate_model(model: ProjectModel, *, check_lockfiles: bool = True) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    _check_normalization_collisions(model, issues)
    _check_target_collisions(model, issues)
    _check_pylock_filenames(model, issues)
    if check_lockfiles:
        _check_lockfiles(model, issues)
    return issues


def validate_workspace_model(
    workspace: WorkspaceModel, *, check_lockfiles: bool = True
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for item in workspace.projects:
        issues.extend(validate_model(item.project, check_lockfiles=check_lockfiles))
    return issues


def _check_normalization_collisions(model: ProjectModel, issues: list[ValidationIssue]) -> None:
    seen: dict[str, list[str]] = {}
    names = list(model.groups.keys()) + list(model.optionals.keys())
    for name in names:
        seen.setdefault(normalize_name(name), []).append(name)

    for normalized, originals in sorted(seen.items()):
        if len(originals) > 1:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="normalized-name-collision",
                    message=(
                        f"Multiple group/extra names normalize to '{normalized}': "
                        f"{', '.join(sorted(originals))}"
                    ),
                    path=model.project_path,
                )
            )


def _check_target_collisions(model: ProjectModel, issues: list[ValidationIssue]) -> None:
    filename_to_names: dict[str, list[str]] = {}
    for target in plan_targets(model):
        filename_to_names.setdefault(target.filename, []).append(target.name)

    for filename, names in sorted(filename_to_names.items()):
        if len(names) > 1:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="lockfile-name-collision",
                    message=f"Multiple targets map to '{filename}': {', '.join(sorted(names))}",
                    path=model.project_path,
                    target=filename,
                )
            )


def _check_pylock_filenames(model: ProjectModel, issues: list[ValidationIssue]) -> None:
    for target in plan_targets(model):
        if not is_valid_pylock_name(target.filename):
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="nonstandard-lockfile-name",
                    message=f"Target '{target.name}' uses nonstandard pylock filename '{target.filename}'.",
                    path=model.project_path,
                    target=target.name,
                )
            )


def _check_lockfiles(model: ProjectModel, issues: list[ValidationIssue]) -> None:
    base_dir = Path(model.project_path).parent
    for target in plan_targets(model):
        lock_path = base_dir / target.filename
        if not lock_path.exists():
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="missing-lockfile",
                    message=f"Expected lock target '{target.filename}' for '{target.name}' does not exist.",
                    path=str(lock_path),
                    target=target.name,
                )
            )
            continue

        current = load_pylock(lock_path)
        expected = build_lock_document(model, target, existing=current)
        drift = _compare_lock(current.raw_document, expected)
        if drift:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="lockfile-metadata-drift",
                    message=(
                        f"Lock target '{target.name}' metadata is out of sync with pyproject.toml: "
                        f"{', '.join(drift)}"
                    ),
                    path=str(lock_path),
                    target=target.name,
                )
            )


def _compare_lock(current: dict[str, object], expected: dict[str, object]) -> list[str]:
    drift: list[str] = []
    for key in ["requires-python", "extras", "dependency-groups", "default-groups"]:
        if current.get(key) != expected.get(key):
            drift.append(key)
    return drift
