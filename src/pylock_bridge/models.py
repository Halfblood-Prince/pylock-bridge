from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DependencyEntry:
    raw: str
    normalized_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProjectModel:
    project_path: str
    project_name: str | None = None
    requires_python: str | None = None
    runtime: list[DependencyEntry] = field(default_factory=list)
    optionals: dict[str, list[DependencyEntry]] = field(default_factory=dict)
    groups: dict[str, list[DependencyEntry]] = field(default_factory=dict)
    bridge_config: dict[str, Any] = field(default_factory=dict)
    raw_document: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "requires_python": self.requires_python,
            "runtime": [item.to_dict() for item in self.runtime],
            "optionals": {
                key: [item.to_dict() for item in value]
                for key, value in sorted(self.optionals.items())
            },
            "groups": {
                key: [item.to_dict() for item in value]
                for key, value in sorted(self.groups.items())
            },
            "bridge_config": self.bridge_config,
        }


@dataclass(slots=True)
class LockTarget:
    name: str
    filename: str
    source_type: str
    include_runtime: bool
    dependency_groups: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    default_groups: list[str] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        sources: list[str] = []
        if self.include_runtime:
            sources.append("project.dependencies")
        sources.extend(f"dependency-group:{name}" for name in self.dependency_groups)
        sources.extend(f"optional:{name}" for name in self.optional_dependencies)
        return sources or ["custom"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "filename": self.filename,
            "source_type": self.source_type,
            "include_runtime": self.include_runtime,
            "dependency_groups": list(self.dependency_groups),
            "optional_dependencies": list(self.optional_dependencies),
            "default_groups": list(self.default_groups),
            "sources": self.sources,
        }


@dataclass(slots=True)
class PyLockModel:
    path: str
    lock_version: str = "1.0"
    created_by: dict[str, Any] = field(default_factory=dict)
    requires_python: str | None = None
    extras: list[str] = field(default_factory=list)
    dependency_groups: list[str] = field(default_factory=list)
    default_groups: list[str] = field(default_factory=list)
    packages: list[dict[str, Any]] = field(default_factory=list)
    tool: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_document: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "lock_version": self.lock_version,
            "created_by": self.created_by,
            "requires_python": self.requires_python,
            "extras": list(self.extras),
            "dependency_groups": list(self.dependency_groups),
            "default_groups": list(self.default_groups),
            "packages": list(self.packages),
            "metadata": self.metadata,
            "tool": self.tool,
        }


@dataclass(slots=True)
class ValidationIssue:
    level: str
    code: str
    message: str
    path: str | None = None
    target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SyncResult:
    project_path: str
    lock_path: str
    changed: bool
    created: bool
    target: LockTarget
    lock: PyLockModel
    document: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "lock_path": self.lock_path,
            "changed": self.changed,
            "created": self.created,
            "target": self.target.to_dict(),
            "lock": self.lock.to_dict(),
        }


@dataclass(slots=True)
class WorkspaceProject:
    root: str
    relative_path: str
    project: ProjectModel

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "relative_path": self.relative_path,
            "project": self.project.to_dict(),
        }


@dataclass(slots=True)
class WorkspaceModel:
    root: str
    projects: list[WorkspaceProject] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "projects": [project.to_dict() for project in self.projects],
        }
