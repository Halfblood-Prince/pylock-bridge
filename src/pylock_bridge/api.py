from __future__ import annotations

from pathlib import Path

from .models import ProjectModel, SyncResult, ValidationIssue, WorkspaceModel
from .monorepo import discover_pyprojects, load_workspace as load_workspace_model
from .parsing import load_pyproject
from .planner import plan_targets, plan_workspace_targets
from .sync import sync_to_lock
from .validator import validate_model, validate_workspace_model


def load_project(path: str | Path = "pyproject.toml") -> ProjectModel:
    return load_pyproject(path)


def inspect_project(path: str | Path = "pyproject.toml") -> ProjectModel:
    return load_project(path)


def plan_project(path: str | Path = "pyproject.toml"):
    return plan_targets(load_project(path))


def validate_project(
    path: str | Path = "pyproject.toml", *, check_lockfiles: bool = True
) -> list[ValidationIssue]:
    return validate_model(load_project(path), check_lockfiles=check_lockfiles)


def sync_project_lock(
    path: str | Path = "pyproject.toml",
    *,
    target_name: str = "default",
    lockfile: str | Path | None = None,
    write: bool = False,
) -> SyncResult:
    return sync_to_lock(load_project(path), target_name=target_name, lockfile=lockfile, write=write)


def discover_projects(root: str | Path = ".") -> list[str]:
    return [str(path) for path in discover_pyprojects(root)]


def load_workspace(root: str | Path = ".") -> WorkspaceModel:
    return load_workspace_model(root)


def inspect_workspace(root: str | Path = ".") -> WorkspaceModel:
    return load_workspace(root)


def plan_workspace(root: str | Path = ".") -> list[dict[str, str | dict[str, object]]]:
    return plan_workspace_targets(load_workspace(root))


def validate_workspace(
    root: str | Path = ".", *, check_lockfiles: bool = True
) -> list[ValidationIssue]:
    return validate_workspace_model(load_workspace(root), check_lockfiles=check_lockfiles)
