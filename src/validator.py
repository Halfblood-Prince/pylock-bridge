from __future__ import annotations

from pathlib import Path

from .models import ProjectModel, ValidationIssue
from .parsing import normalize_name
from .planner import plan_targets


def validate_model(model: ProjectModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    _check_normalization_collisions(model, issues)
    _check_target_collisions(model, issues)
    _check_missing_lockfiles(model, issues)

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
                        f"Multiple group/extra names normalize to '{normalized}': {', '.join(sorted(originals))}"
                    ),
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
                )
            )


def _check_missing_lockfiles(model: ProjectModel, issues: list[ValidationIssue]) -> None:
    base_dir = Path(model.project_path).parent
    for target in plan_targets(model):
        if not (base_dir / target.filename).exists():
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="missing-lockfile",
                    message=f"Expected lock target '{target.filename}' for '{target.name}' does not exist.",
                )
            )
