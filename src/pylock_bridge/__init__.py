"""Public package interface for pylock-bridge."""

__version__ = "1.0.0"

from .api import (
    discover_projects,
    inspect_project,
    inspect_workspace,
    load_project,
    load_workspace,
    plan_project,
    plan_workspace,
    sync_project_lock,
    validate_project,
    validate_workspace,
)
from .models import (
    DependencyEntry,
    LockTarget,
    ProjectModel,
    PyLockModel,
    SyncResult,
    ValidationIssue,
    WorkspaceModel,
    WorkspaceProject,
)

__all__ = [
    "__version__",
    "DependencyEntry",
    "LockTarget",
    "ProjectModel",
    "PyLockModel",
    "SyncResult",
    "ValidationIssue",
    "WorkspaceModel",
    "WorkspaceProject",
    "discover_projects",
    "inspect_project",
    "inspect_workspace",
    "load_project",
    "load_workspace",
    "plan_project",
    "plan_workspace",
    "sync_project_lock",
    "validate_project",
    "validate_workspace",
]
