from __future__ import annotations

import sys
import textwrap
import unittest
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pylock_bridge.cli import main

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


class CliTests(unittest.TestCase):
    def test_plan_json(self) -> None:
        with workspace_tmpdir() as root:
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "demo"
                    dependencies = ["requests>=2"]

                    [dependency-groups]
                    dev = ["pytest"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            exit_code = main(["plan", "--project", str(root / "pyproject.toml"), "--format", "json"])

            self.assertEqual(exit_code, 0)

    def test_sync_check_detects_changes(self) -> None:
        with workspace_tmpdir() as root:
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "demo"
                    requires-python = ">=3.12"
                    dependencies = ["requests>=2"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            exit_code = main(["sync", "--project", str(root / "pyproject.toml"), "--check"])

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
