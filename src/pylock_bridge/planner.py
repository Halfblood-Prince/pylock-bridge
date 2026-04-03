from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import LockTarget, ProjectModel, WorkspaceModel

PYLOCK_NAME_RE = re.compile(r"^pylock(?:\.[a-z0-9][a-z0-9._-]*)?\.toml$")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", ".", value)
    return value.strip(".") or "default"


def plan_targets(model: ProjectModel) -> list[LockTarget]:
    config = model.bridge_config or {}
    targets_cfg = config.get("targets", {}) if isinstance(config, dict) else {}
    default_lock = str(config.get("default-lock", "pylock.toml"))
    include_optionals = bool(config.get("include-optionals-by-default", False))
    include_groups = bool(config.get("include-groups-by-default", False))
    configured_default_groups = [str(item) for item in config.get("default-groups", []) or []]

    targets: list[LockTarget] = [
        LockTarget(
            name="default",
            filename=default_lock,
            source_type="runtime",
            include_runtime=True,
            dependency_groups=sorted(model.groups) if include_groups else [],
            optional_dependencies=sorted(model.optionals) if include_optionals else [],
            default_groups=configured_default_groups,
        )
    ]

    if isinstance(targets_cfg, dict) and targets_cfg:
        for name, details in sorted(targets_cfg.items()):
            details = details if isinstance(details, dict) else {}
            filename = str(details.get("filename", f"pylock.{slugify(str(name))}.toml"))
            targets.append(
                LockTarget(
                    name=str(name),
                    filename=filename,
                    source_type="configured",
                    include_runtime=bool(details.get("include-runtime", False)),
                    dependency_groups=sorted(str(item) for item in details.get("dependency-groups", []) or []),
                    optional_dependencies=sorted(
                        str(item) for item in details.get("optional-dependencies", []) or []
                    ),
                    default_groups=sorted(str(item) for item in details.get("default-groups", []) or []),
                )
            )
        return dedupe_targets(targets)

    for group in sorted(model.groups):
        targets.append(
            LockTarget(
                name=group,
                filename=f"pylock.{slugify(group)}.toml",
                source_type="dependency-group",
                include_runtime=False,
                dependency_groups=[group],
            )
        )

    for extra in sorted(model.optionals):
        targets.append(
            LockTarget(
                name=extra,
                filename=f"pylock.{slugify(extra)}.toml",
                source_type="optional-dependency",
                include_runtime=False,
                optional_dependencies=[extra],
            )
        )

    return dedupe_targets(targets)


def dedupe_targets(targets: Iterable[LockTarget]) -> list[LockTarget]:
    deduped: list[LockTarget] = []
    seen: set[tuple[str, str]] = set()
    for target in targets:
        key = (target.name, target.filename)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(target)
    return deduped


def resolve_target(model: ProjectModel, name: str) -> LockTarget:
    for target in plan_targets(model):
        if target.name == name:
            return target
    raise KeyError(f"Unknown target '{name}'")


def is_valid_pylock_name(filename: str) -> bool:
    return bool(PYLOCK_NAME_RE.match(Path(filename).name))


def plan_workspace_targets(workspace: WorkspaceModel) -> list[dict[str, str | dict[str, object]]]:
    plans: list[dict[str, str | dict[str, object]]] = []
    for item in workspace.projects:
        for target in plan_targets(item.project):
            plans.append(
                {
                    "project": item.relative_path,
                    "project_path": item.project.project_path,
                    "target": target.to_dict(),
                }
            )
    return plans
