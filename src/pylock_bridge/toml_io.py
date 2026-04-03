from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def load_toml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise TypeError("Expected TOML document to decode to a table")
    return data


def dump_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    _write_table(lines, [], data)
    return "\n".join(lines).rstrip() + "\n"


def _write_table(lines: list[str], prefix: list[str], table: dict[str, Any]) -> None:
    if prefix:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"[{'.'.join(prefix)}]")

    scalars: list[tuple[str, Any]] = []
    tables: list[tuple[str, dict[str, Any]]] = []
    arrays_of_tables: list[tuple[str, list[dict[str, Any]]]] = []

    for key, value in table.items():
        if isinstance(value, dict):
            tables.append((key, value))
        elif _is_array_of_tables(value):
            arrays_of_tables.append((key, value))
        else:
            scalars.append((key, value))

    for key, value in scalars:
        lines.append(f"{key} = {_format_value(value)}")

    for key, value in tables:
        _write_table(lines, [*prefix, key], value)

    for key, value in arrays_of_tables:
        for item in value:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[[{'.'.join([*prefix, key])}]]")
            _write_table_body(lines, [*prefix, key], item)


def _write_table_body(lines: list[str], prefix: list[str], table: dict[str, Any]) -> None:
    scalars: list[tuple[str, Any]] = []
    tables: list[tuple[str, dict[str, Any]]] = []
    arrays_of_tables: list[tuple[str, list[dict[str, Any]]]] = []

    for key, value in table.items():
        if isinstance(value, dict):
            tables.append((key, value))
        elif _is_array_of_tables(value):
            arrays_of_tables.append((key, value))
        else:
            scalars.append((key, value))

    for key, value in scalars:
        lines.append(f"{key} = {_format_value(value)}")

    for key, value in tables:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"[{'.'.join([*prefix, key])}]")
        _write_table_body(lines, [*prefix, key], value)

    for key, value in arrays_of_tables:
        for item in value:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[[{'.'.join([*prefix, key])}]]")
            _write_table_body(lines, [*prefix, key], item)


def _is_array_of_tables(value: Any) -> bool:
    return isinstance(value, list) and value and all(isinstance(item, dict) for item in value)


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        escaped = (
            value.replace("\\", "\\\\")
            .replace("\b", "\\b")
            .replace("\t", "\\t")
            .replace("\n", "\\n")
            .replace("\f", "\\f")
            .replace("\r", "\\r")
            .replace('"', '\\"')
        )
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(f"{key} = {_format_value(item)}" for key, item in value.items())
        return "{ " + items + " }"
    if value is None:
        raise TypeError("TOML does not support null values")
    raise TypeError(f"Unsupported TOML value: {type(value).__name__}")
