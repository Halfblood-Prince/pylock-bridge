from __future__ import annotations

import argparse
import sys
from typing import Any

from .parsing import load_pyproject
from .planner import plan_targets
from .render import (
    render_inspect_text,
    render_json,
    render_plan_text,
    render_validate_text,
)
from .validator import validate_model


class CLIError(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pylock-bridge")
    parser.add_argument("command", choices=["inspect", "plan", "validate"])
    parser.add_argument("--project", default="pyproject.toml", help="Path to pyproject.toml")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def _as_json_for_inspect(model: Any) -> dict[str, Any]:
    return model.to_dict()


def _as_json_for_plan(targets: Any) -> dict[str, Any]:
    return {"targets": [target.to_dict() for target in targets]}


def _as_json_for_validate(issues: Any) -> dict[str, Any]:
    issue_list = list(issues)
    return {
        "ok": not any(issue.level == "error" for issue in issue_list),
        "issues": [issue.to_dict() for issue in issue_list],
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        model = load_pyproject(args.project)

        if args.command == "inspect":
            if args.format == "json":
                print(render_json(_as_json_for_inspect(model)))
            else:
                print(render_inspect_text(model))
            return 0

        if args.command == "plan":
            targets = plan_targets(model)
            if args.format == "json":
                print(render_json(_as_json_for_plan(targets)))
            else:
                print(render_plan_text(targets))
            return 0

        if args.command == "validate":
            issues = validate_model(model)
            has_error = any(issue.level == "error" for issue in issues)
            if args.format == "json":
                print(render_json(_as_json_for_validate(issues)))
            else:
                print(render_validate_text(issues))
            return 1 if has_error else 0

        raise CLIError(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
