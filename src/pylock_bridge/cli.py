from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .api import (
    discover_projects,
    inspect_project,
    inspect_workspace,
    plan_project,
    plan_workspace,
    sync_project_lock,
    validate_project,
    validate_workspace,
)
from .render import (
    render_inspect_text,
    render_json,
    render_plan_text,
    render_sync_text,
    render_validate_text,
    render_workspace_plan_text,
    render_workspace_text,
)
from .sync import render_lock_document


class CLIError(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pylock-bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a pyproject or workspace")
    inspect_parser.add_argument("--project", default="pyproject.toml", help="Path to pyproject.toml")
    inspect_parser.add_argument("--workspace", help="Scan a workspace root instead of a single project")
    inspect_parser.add_argument("--format", choices=["text", "json"], default="text")

    plan_parser = subparsers.add_parser("plan", help="Plan pylock targets")
    plan_parser.add_argument("--project", default="pyproject.toml", help="Path to pyproject.toml")
    plan_parser.add_argument("--workspace", help="Scan a workspace root instead of a single project")
    plan_parser.add_argument("--format", choices=["text", "json"], default="text")

    validate_parser = subparsers.add_parser("validate", help="Validate pyproject and pylock state")
    validate_parser.add_argument("--project", default="pyproject.toml", help="Path to pyproject.toml")
    validate_parser.add_argument("--workspace", help="Scan a workspace root instead of a single project")
    validate_parser.add_argument("--format", choices=["text", "json"], default="text")
    validate_parser.add_argument(
        "--no-check-lockfiles",
        action="store_true",
        help="Only validate target planning and naming, skip on-disk pylock files",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero for warnings as well as errors",
    )

    sync_parser = subparsers.add_parser("sync", help="Sync pyproject metadata into pylock.toml")
    sync_parser.add_argument("--project", default="pyproject.toml", help="Path to pyproject.toml")
    sync_parser.add_argument("--target", default="default", help="Planned target name to sync")
    sync_parser.add_argument("--lockfile", help="Override the output lockfile path")
    sync_parser.add_argument("--format", choices=["text", "json", "toml"], default="text")
    sync_parser.add_argument("--write", action="store_true", help="Write the synchronized lockfile")
    sync_parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the lockfile would change",
    )

    discover_parser = subparsers.add_parser("discover", help="List pyproject files in a workspace")
    discover_parser.add_argument("--workspace", default=".", help="Workspace root")
    discover_parser.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return _dispatch(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "inspect":
        return _run_inspect(args)
    if args.command == "plan":
        return _run_plan(args)
    if args.command == "validate":
        return _run_validate(args)
    if args.command == "sync":
        return _run_sync(args)
    if args.command == "discover":
        return _run_discover(args)
    raise CLIError(f"Unknown command: {args.command}")


def _run_inspect(args: argparse.Namespace) -> int:
    if args.workspace:
        workspace = inspect_workspace(args.workspace)
        _print(args.format, workspace.to_dict(), render_workspace_text(workspace))
        return 0
    model = inspect_project(args.project)
    _print(args.format, model.to_dict(), render_inspect_text(model))
    return 0


def _run_plan(args: argparse.Namespace) -> int:
    if args.workspace:
        plans = plan_workspace(args.workspace)
        _print(args.format, {"targets": plans}, render_workspace_plan_text(plans))
        return 0
    targets = plan_project(args.project)
    _print(args.format, {"targets": [target.to_dict() for target in targets]}, render_plan_text(targets))
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    check_lockfiles = not args.no_check_lockfiles
    if args.workspace:
        issues = validate_workspace(args.workspace, check_lockfiles=check_lockfiles)
    else:
        issues = validate_project(args.project, check_lockfiles=check_lockfiles)
    ok = _is_ok(issues, strict=args.strict)
    _print(
        args.format,
        {"ok": ok, "issues": [issue.to_dict() for issue in issues]},
        render_validate_text(issues),
    )
    return 0 if ok else 1


def _run_sync(args: argparse.Namespace) -> int:
    result = sync_project_lock(
        args.project,
        target_name=args.target,
        lockfile=args.lockfile,
        write=args.write,
    )
    if args.format == "toml":
        print(render_lock_document(result))
    else:
        _print(args.format, result.to_dict(), render_sync_text(result))
    if args.check and result.changed:
        return 1
    return 0


def _run_discover(args: argparse.Namespace) -> int:
    projects = discover_projects(args.workspace)
    if args.format == "json":
        print(render_json({"workspace": str(Path(args.workspace).resolve()), "projects": projects}))
    else:
        print("\n".join(projects))
    return 0


def _print(fmt: str, json_payload: Any, text_payload: str) -> None:
    if fmt == "json":
        print(render_json(json_payload))
    else:
        print(text_payload)


def _is_ok(issues: list[Any], *, strict: bool) -> bool:
    if strict:
        return not issues
    return not any(issue.level == "error" for issue in issues)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
