from __future__ import annotations

import re
from typing import Iterable

from .models import LockTarget, ProjectModel


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", ".", value)
    return value.strip(".") or "default"


def plan_targets(model: ProjectModel) -> list[LockTarget]:
    config = model.bridge_config or {}
    targets_cfg = config.get("targets", {}) if isinstance(config, dict) else {}
    default_lock = config.get("default-lock", "pylock.toml")

    targets: list[LockTarget] = [
        LockTarget(
            name="default",
            filename=str(default_lock),
            source_type="runtime",
            sources=["project.dependencies"],
        )
    ]

    if isinstance(targets_cfg, dict) and targets_cfg:
        for name, details in sorted(targets_cfg.items()):
            details = details or {}
            groups = [str(item) for item in details.get("dependency-groups", [])]
            optionals = [str(item) for item in details.get("optional-dependencies", [])]
            sources: list[str] = []
            if groups:
                sources.extend([f"dependency-group:{group}" for group in groups])
            if optionals:
                sources.extend([f"optional:{extra}" for extra in optionals])
            if not sources:
                sources.append("custom")
            targets.append(
                LockTarget(
                    name=str(name),
                    filename=f"pylock.{slugify(str(name))}.toml",
                    source_type="configured",
                    sources=sources,
                )
            )
        return dedupe_targets(targets)

    for group in sorted(model.groups):
        targets.append(
            LockTarget(
                name=group,
                filename=f"pylock.{slugify(group)}.toml",
                source_type="dependency-group",
                sources=[group],
            )
        )

    for extra in sorted(model.optionals):
        targets.append(
            LockTarget(
                name=extra,
                filename=f"pylock.{slugify(extra)}.toml",
                source_type="optional-dependency",
                sources=[extra],
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
