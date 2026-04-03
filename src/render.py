from __future__ import annotations

import json
from typing import Iterable

from .models import LockTarget, ProjectModel, ValidationIssue


def render_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def render_inspect_text(model: ProjectModel) -> str:
    lines: list[str] = []
    runtime = ", ".join(item.normalized_name for item in model.runtime) or "(none)"
    lines.append(f"project: {model.project_path}")
    lines.append(f"runtime: {runtime}")

    if model.optionals:
        lines.append("optional-dependencies:")
        for name, entries in sorted(model.optionals.items()):
            deps = ", ".join(item.normalized_name for item in entries) or "(none)"
            lines.append(f"  - {name}: {deps}")
    else:
        lines.append("optional-dependencies: (none)")

    if model.groups:
        lines.append("dependency-groups:")
        for name, entries in sorted(model.groups.items()):
            deps = ", ".join(item.normalized_name for item in entries) or "(none)"
            lines.append(f"  - {name}: {deps}")
    else:
        lines.append("dependency-groups: (none)")

    return "\n".join(lines)


def render_plan_text(targets: Iterable[LockTarget]) -> str:
    lines = ["planned lock targets:"]
    for target in targets:
        sources = ", ".join(target.sources)
        lines.append(f"  - {target.filename} <- {target.name} ({target.source_type}: {sources})")
    return "\n".join(lines)


def render_validate_text(issues: Iterable[ValidationIssue]) -> str:
    issues = list(issues)
    if not issues:
        return "validation passed"
    lines = ["validation issues:"]
    for issue in issues:
        lines.append(f"  - [{issue.level}] {issue.code}: {issue.message}")
    return "\n".join(lines)
