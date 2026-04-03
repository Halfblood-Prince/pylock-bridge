from __future__ import annotations

import sys
import textwrap
import unittest
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pylock_bridge import api

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"
TEST_TMP_ROOT.mkdir(exist_ok=True)


@contextmanager
def workspace_tmpdir():
    path = TEST_TMP_ROOT / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        if path.exists():
            rmtree(path)


class ApiTests(unittest.TestCase):
    def test_plan_project_infers_targets(self) -> None:
        with workspace_tmpdir() as root:
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "demo"
                    dependencies = ["requests>=2", "rich"]

                    [project.optional-dependencies]
                    docs = ["mkdocs"]

                    [dependency-groups]
                    dev = ["pytest"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            targets = api.plan_project(root / "pyproject.toml")

            self.assertEqual([item.name for item in targets], ["default", "dev", "docs"])
            self.assertEqual(targets[0].filename, "pylock.toml")
            self.assertEqual(targets[1].filename, "pylock.dev.toml")

    def test_sync_writes_metadata_and_preserves_packages(self) -> None:
        with workspace_tmpdir() as root:
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "demo"
                    requires-python = ">=3.11"
                    dependencies = ["requests>=2"]

                    [dependency-groups]
                    dev = ["pytest"]

                    [tool.pylock-bridge.targets.dev]
                    dependency-groups = ["dev"]
                    default-groups = ["dev"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "pylock.dev.toml").write_text(
                textwrap.dedent(
                    """
                    lock-version = "1.0"
                    extras = []
                    dependency-groups = []
                    default-groups = []

                    [[packages]]
                    name = "pytest"
                    version = "8.0.0"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = api.sync_project_lock(root / "pyproject.toml", target_name="dev", write=True)

            self.assertTrue(result.changed)
            content = (root / "pylock.dev.toml").read_text(encoding="utf-8")
            self.assertIn('dependency-groups = ["dev"]', content)
            self.assertIn('default-groups = ["dev"]', content)
            self.assertIn('[[packages]]', content)

    def test_validate_reports_metadata_drift(self) -> None:
        with workspace_tmpdir() as root:
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "demo"
                    requires-python = ">=3.11"
                    dependencies = ["requests>=2"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "pylock.toml").write_text(
                textwrap.dedent(
                    """
                    lock-version = "1.0"
                    requires-python = ">=3.10"
                    extras = []
                    dependency-groups = []
                    default-groups = []
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            issues = api.validate_project(root / "pyproject.toml")

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].code, "lockfile-metadata-drift")

    def test_discover_workspace_projects(self) -> None:
        with workspace_tmpdir() as root:
            (root / "apps" / "a").mkdir(parents=True)
            (root / "apps" / "b").mkdir(parents=True)
            (root / "apps" / "a" / "pyproject.toml").write_text("[project]\nname = 'a'\n", encoding="utf-8")
            (root / "apps" / "b" / "pyproject.toml").write_text("[project]\nname = 'b'\n", encoding="utf-8")

            workspace = api.inspect_workspace(root)

            self.assertEqual(len(workspace.projects), 2)
            self.assertEqual([item.relative_path for item in workspace.projects], ["apps/a", "apps/b"])


if __name__ == "__main__":
    unittest.main()
