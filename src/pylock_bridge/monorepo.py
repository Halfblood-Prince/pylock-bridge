from __future__ import annotations

from pathlib import Path

from .models import WorkspaceModel, WorkspaceProject
from .parsing import load_pyproject

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


def discover_pyprojects(root: str | Path) -> list[Path]:
    root_path = Path(root).resolve()
    results: list[Path] = []
    for path in root_path.rglob("pyproject.toml"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        results.append(path.resolve())
    return sorted(results)


def load_workspace(root: str | Path) -> WorkspaceModel:
    root_path = Path(root).resolve()
    projects = [
        WorkspaceProject(
            root=str(root_path),
            relative_path=path.parent.relative_to(root_path).as_posix() or ".",
            project=load_pyproject(path),
        )
        for path in discover_pyprojects(root_path)
    ]
    return WorkspaceModel(root=str(root_path), projects=projects)
