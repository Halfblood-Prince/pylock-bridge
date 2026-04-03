from __future__ import annotations

import re
from pathlib import Path

from .models import DependencyEntry, ProjectModel, PyLockModel
from .toml_io import load_toml

_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def dependency_name(requirement: str) -> str:
    match = _NAME_RE.match(requirement)
    if not match:
        raise ValueError(f"Could not parse dependency name from requirement: {requirement!r}")
    return normalize_name(match.group(1))


def _coerce_entries(values: list[str]) -> list[DependencyEntry]:
    entries: list[DependencyEntry] = []
    for raw in values:
        if not isinstance(raw, str):
            raise TypeError(f"Dependency entries must be strings, got {type(raw).__name__}")
        entries.append(DependencyEntry(raw=raw, normalized_name=dependency_name(raw)))
    return entries


def load_pyproject(path: str | Path = "pyproject.toml") -> ProjectModel:
    project_path = Path(path)
    if not project_path.exists():
        raise FileNotFoundError(f"pyproject file not found: {project_path}")

    data = load_toml(project_path)
    project = data.get("project", {}) or {}
    tool = data.get("tool", {}) or {}
    bridge_config = (tool.get("pylock-bridge", {}) or {}) if isinstance(tool, dict) else {}

    runtime = _coerce_entries(project.get("dependencies", []) or [])
    raw_optionals = project.get("optional-dependencies", {}) or {}
    raw_groups = data.get("dependency-groups", {}) or {}

    optionals = {
        str(extra): _coerce_entries(values or [])
        for extra, values in raw_optionals.items()
    }
    groups = {
        str(group): _coerce_entries(values or [])
        for group, values in raw_groups.items()
    }

    return ProjectModel(
        project_path=str(project_path.resolve()),
        project_name=project.get("name"),
        requires_python=project.get("requires-python"),
        runtime=runtime,
        optionals=optionals,
        groups=groups,
        bridge_config=bridge_config if isinstance(bridge_config, dict) else {},
        raw_document=data,
    )


def load_pylock(path: str | Path) -> PyLockModel:
    lock_path = Path(path)
    if not lock_path.exists():
        raise FileNotFoundError(f"pylock file not found: {lock_path}")

    data = load_toml(lock_path)
    return PyLockModel(
        path=str(lock_path.resolve()),
        lock_version=str(data.get("lock-version", "1.0")),
        created_by=dict(data.get("created-by", {}) or {}),
        requires_python=data.get("requires-python"),
        extras=[str(item) for item in data.get("extras", []) or []],
        dependency_groups=[str(item) for item in data.get("dependency-groups", []) or []],
        default_groups=[str(item) for item in data.get("default-groups", []) or []],
        packages=[dict(item) for item in data.get("packages", []) or []],
        metadata=dict(data.get("metadata", {}) or {}),
        tool=dict(data.get("tool", {}) or {}),
        raw_document=data,
    )
