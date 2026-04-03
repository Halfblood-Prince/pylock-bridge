# pylock-bridge

`pylock-bridge` is a production-ready Python library and CLI for converting, syncing, and validating dependency intent between:

- `project.dependencies`
- `project.optional-dependencies`
- top-level `[dependency-groups]`
- `pylock.toml` metadata and target naming

It is designed for CI pipelines, multi-lock workflows, and monorepos that want one place to reason about standardized packaging data without taking over dependency resolution.

## What it does

- inspects dependency intent from `pyproject.toml`
- plans standardized `pylock.toml` target filenames
- syncs lockfile metadata from `pyproject.toml` into existing or new `pylock*.toml` files
- preserves existing `[[packages]]`, `tool.*`, and unrelated lockfile content while updating bridge-managed metadata
- validates drift between project metadata and lockfile metadata
- scans monorepos and reports project-by-project plans
- exposes a clean Python API for automation

`pylock-bridge` does **not** resolve dependencies or generate package entries. It keeps project intent and lockfile metadata aligned so your resolver or build pipeline can do the actual solving.

## Install

```bash
pip install pylock-bridge
```

For local development:

```bash
pip install -e .
python -m unittest discover -s tests
```

## CLI

Inspect a project:

```bash
pylock-bridge inspect
pylock-bridge inspect --project path/to/pyproject.toml --format json
```

Plan lock targets:

```bash
pylock-bridge plan
pylock-bridge plan --workspace .
```

Validate drift:

```bash
pylock-bridge validate
pylock-bridge validate --workspace . --strict
```

Sync a target into a lockfile:

```bash
pylock-bridge sync --target default --write
pylock-bridge sync --target dev --format toml
pylock-bridge sync --target dev --check
```

Discover projects in a monorepo:

```bash
pylock-bridge discover --workspace .
```

## Python API

```python
from pylock_bridge import plan_project, sync_project_lock, validate_workspace

targets = plan_project("pyproject.toml")
result = sync_project_lock("pyproject.toml", target_name="default", write=True)
issues = validate_workspace(".", check_lockfiles=True)
```

## Planning configuration

You can customize how lock targets are planned using `[tool.pylock-bridge]`:

```toml
[tool.pylock-bridge]
default-lock = "pylock.toml"
include-optionals-by-default = false
include-groups-by-default = false
default-groups = ["dev"]

[tool.pylock-bridge.targets.dev]
dependency-groups = ["dev"]
default-groups = ["dev"]

[tool.pylock-bridge.targets.docs]
optional-dependencies = ["docs"]

[tool.pylock-bridge.targets.ci]
include-runtime = true
dependency-groups = ["lint", "test"]
filename = "pylock.ci.toml"
```

## Sync model

When you run `sync`, the tool updates lockfile metadata based on the selected target:

- `requires-python`
- `extras`
- `dependency-groups`
- `default-groups`
- `metadata.pylock-bridge`

Existing `[[packages]]` entries are preserved so lockfile metadata can be refreshed without discarding solved package state.

## Monorepo support

Workspace scanning walks the tree for `pyproject.toml` files while ignoring common generated directories such as `.git`, `.venv`, `dist`, `build`, and `node_modules`.

This makes it suitable for:

- repository-wide validation in CI
- reporting planned lock targets for many packages
- standardizing lock metadata conventions across multiple subprojects

## Validation rules

Validation currently checks:

- group/extra normalization collisions
- target filename collisions
- nonstandard `pylock` filenames
- missing lockfiles
- drift between `pyproject.toml` metadata and existing `pylock*.toml` metadata
