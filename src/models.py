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
    runtime: list[DependencyEntry] = field(default_factory=list)
    optionals: dict[str, list[DependencyEntry]] = field(default_factory=dict)
    groups: dict[str, list[DependencyEntry]] = field(default_factory=dict)
    bridge_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
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
    sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationIssue:
    level: str
    code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
