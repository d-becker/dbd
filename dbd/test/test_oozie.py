#!/usr/bin/env python3

# pylint: disable=missing-docstring

import tarfile
import tempfile
from typing import List
from pathlib import Path

from oozie import BuildOozieStage, ShellCommandExecutor

from test.temp_dir_test_case import TmpDirTestCase

class MockShellCommandExecutor(ShellCommandExecutor):
    def run(self, command: List[str]) -> None:
        pass

class TestBuildOozieStage(TmpDirTestCase):
    def test_check_precondition_returns_false_when_source_archive_does_not_exist(self) -> None:
        source_archive = self._tmp_dir_path / "oozie.tar.gz"
        self.assertFalse(source_archive.exists())

        dest_path = self._tmp_dir_path / "oozie-d.tar.gz"

        shell_command_executor = MockShellCommandExecutor()
        stage = BuildOozieStage(source_archive, dest_path, shell_command_executor)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_execute_distro_archive_present_at_dest_path(self) -> None:
        source_archive = self._tmp_dir_path / "oozie.tar.gz"
        TestBuildOozieStage._create_archive(source_archive)
        self.assertTrue(source_archive.exists())

        dest_path = self._tmp_dir_path / "oozie-disto.tar.gz"

        shell_command_executor = MockShellCommandExecutor()
        stage = BuildOozieStage(source_archive, dest_path, shell_command_executor)

        self.assertTrue(stage.check_precondition())

        stage.execute()

        self.assertTrue(dest_path.exists())

    @staticmethod
    def _create_archive(dest_path: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            oozie_dir = tmp_dir / "oozie-5.0.0"
            distro_archive = oozie_dir / "distro" / "target" / "oozie-5.0.0-distro.tar.gz"
            distro_archive.parent.mkdir(parents=True)
            distro_archive.touch()

            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(str(oozie_dir), arcname=oozie_dir.name)
