from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import DependencyEntry, ProjectModel

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


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

    with project_path.open("rb") as fh:
        data: dict[str, Any] = tomllib.load(fh)

    project = data.get("project", {}) or {}
    tool = data.get("tool", {}) or {}
    bridge_config = (tool.get("pylock-bridge", {}) or {}) if isinstance(tool, dict) else {}

    runtime = _coerce_entries(project.get("dependencies", []) or [])

    raw_optionals = project.get("optional-dependencies", {}) or {}
    optionals = {
        str(extra): _coerce_entries(values or [])
        for extra, values in raw_optionals.items()
    }

    raw_groups = data.get("dependency-groups", {}) or {}
    groups = {
        str(group): _coerce_entries(values or [])
        for group, values in raw_groups.items()
    }

    return ProjectModel(
        project_path=str(project_path.resolve()),
        runtime=runtime,
        optionals=optionals,
        groups=groups,
        bridge_config=bridge_config,
    )
