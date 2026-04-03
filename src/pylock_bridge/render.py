from __future__ import annotations

import json
from typing import Iterable

from .models import LockTarget, ProjectModel, SyncResult, ValidationIssue, WorkspaceModel


def render_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def render_inspect_text(model: ProjectModel) -> str:
    lines: list[str] = []
    runtime = ", ".join(item.normalized_name for item in model.runtime) or "(none)"
    lines.append(f"project: {model.project_path}")
    if model.project_name:
        lines.append(f"name: {model.project_name}")
    lines.append(f"runtime: {runtime}")
    lines.append(f"requires-python: {model.requires_python or '(none)'}")

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

    if model.bridge_config:
        lines.append("bridge-config: present")

    return "\n".join(lines)


def render_workspace_text(workspace: WorkspaceModel) -> str:
    lines = [f"workspace: {workspace.root}", f"projects: {len(workspace.projects)}"]
    for item in workspace.projects:
        name = item.project.project_name or item.relative_path
        lines.append(f"  - {item.relative_path}: {name}")
    return "\n".join(lines)


def render_plan_text(targets: Iterable[LockTarget]) -> str:
    lines = ["planned lock targets:"]
    for target in targets:
        sources = ", ".join(target.sources)
        lines.append(f"  - {target.filename} <- {target.name} ({target.source_type}: {sources})")
    return "\n".join(lines)


def render_workspace_plan_text(plans: Iterable[dict[str, object]]) -> str:
    lines = ["planned workspace lock targets:"]
    for item in plans:
        target = item["target"]
        assert isinstance(target, dict)
        lines.append(f"  - {item['project']}: {target['filename']} <- {target['name']}")
    return "\n".join(lines)


def render_validate_text(issues: Iterable[ValidationIssue]) -> str:
    issues = list(issues)
    if not issues:
        return "validation passed"
    lines = ["validation issues:"]
    for issue in issues:
        prefix = f"{issue.path}: " if issue.path else ""
        lines.append(f"  - [{issue.level}] {issue.code}: {prefix}{issue.message}")
    return "\n".join(lines)


def render_sync_text(result: SyncResult) -> str:
    state = "created" if result.created else "updated" if result.changed else "already-synced"
    return f"target: {result.target.name}\nlockfile: {result.lock_path}\nstate: {state}"
