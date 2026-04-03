from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from . import __version__
from .models import LockTarget, ProjectModel, PyLockModel, SyncResult
from .parsing import load_pylock
from .planner import resolve_target
from .toml_io import dump_toml


def build_lock_document(
    project: ProjectModel,
    target: LockTarget,
    existing: PyLockModel | None = None,
) -> dict[str, Any]:
    base = dict(existing.raw_document) if existing else {}
    packages = list(existing.packages) if existing else list(base.get("packages", []) or [])
    metadata = dict(existing.metadata) if existing else dict(base.get("metadata", {}) or {})
    tool = dict(existing.tool) if existing else dict(base.get("tool", {}) or {})
    bridge_meta = dict(metadata.get("pylock-bridge", {}) or {})

    bridge_meta.update(
        {
            "project-path": project.project_path,
            "target-name": target.name,
            "source-type": target.source_type,
            "include-runtime": target.include_runtime,
        }
    )
    if project.project_name:
        bridge_meta["project-name"] = project.project_name
    else:
        bridge_meta.pop("project-name", None)
    metadata["pylock-bridge"] = bridge_meta

    document: dict[str, Any] = dict(base)
    document["lock-version"] = base.get("lock-version", "1.0")
    document["created-by"] = {"name": "pylock-bridge", "version": __version__}
    document["extras"] = list(target.optional_dependencies)
    document["dependency-groups"] = list(target.dependency_groups)
    document["default-groups"] = list(target.default_groups)
    document["metadata"] = metadata
    document["tool"] = tool

    requires_python = project.requires_python or base.get("requires-python")
    if requires_python:
        document["requires-python"] = requires_python
    else:
        document.pop("requires-python", None)

    if packages:
        document["packages"] = packages
    else:
        document.pop("packages", None)

    return document


def sync_to_lock(
    project: ProjectModel,
    *,
    target_name: str = "default",
    lockfile: str | Path | None = None,
    write: bool = False,
) -> SyncResult:
    target = resolve_target(project, target_name)
    project_dir = Path(project.project_path).parent
    lock_path = Path(lockfile) if lockfile else project_dir / target.filename

    existing = load_pylock(lock_path) if lock_path.exists() else None
    document = build_lock_document(project, target, existing=existing)
    rendered = dump_toml(document)
    changed = True
    created = not lock_path.exists()

    if not created:
        current_text = lock_path.read_text(encoding="utf-8")
        changed = current_text != rendered

    if write and changed:
        _atomic_write(lock_path, rendered)

    lock_model = load_pylock(lock_path) if write and lock_path.exists() else PyLockModel(
        path=str(lock_path.resolve()),
        lock_version=str(document["lock-version"]),
        created_by=dict(document["created-by"]),
        requires_python=document.get("requires-python"),
        extras=list(document.get("extras", []) or []),
        dependency_groups=list(document.get("dependency-groups", []) or []),
        default_groups=list(document.get("default-groups", []) or []),
        packages=list(document.get("packages", []) or []),
        metadata=dict(document.get("metadata", {}) or {}),
        tool=dict(document.get("tool", {}) or {}),
        raw_document=document,
    )

    return SyncResult(
        project_path=project.project_path,
        lock_path=str(lock_path.resolve()),
        changed=changed,
        created=created,
        target=target,
        lock=lock_model,
        document=document,
    )


def render_lock_document(sync_result: SyncResult) -> str:
    return dump_toml(sync_result.document)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)
