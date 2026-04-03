# pylock-bridge 0.1.0

`pylock-bridge` is a small Python package that inspects dependency intent from `pyproject.toml`, plans recommended `pylock` targets, and validates basic drift conditions.

## Features in 0.1

- Read `project.dependencies`
- Read `project.optional-dependencies`
- Read `[dependency-groups]`
- Normalize dependency names
- Plan recommended lock target filenames
- Validate missing lock targets and basic naming collisions
- Emit text or JSON

## Install

```bash
pip install .
```

## CLI

```bash
pylock-bridge inspect
pylock-bridge plan
pylock-bridge validate
```

Run against a specific project file:

```bash
pylock-bridge inspect --project path/to/pyproject.toml --format json
```

## Example config

You can optionally add planning overrides:

```toml
[tool.pylock-bridge]
default-lock = "pylock.toml"
include-optionals-by-default = false

[tool.pylock-bridge.targets.dev]
dependency-groups = ["dev"]

[tool.pylock-bridge.targets.docs]
dependency-groups = ["docs"]
```

## Notes

Version 0.1 intentionally does **not** solve dependencies or generate lockfile contents. It only inspects, plans, and validates.
