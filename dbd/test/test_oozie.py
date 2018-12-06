#!/usr/bin/env python3

# pylint: disable=missing-docstring

import tarfile
import tempfile
from typing import List
from pathlib import Path

from dbd.component_builder import ComponentConfig, DistInfo, DistType

from dbd.default_component_image_builder.stages import (
    BuildDockerImageStage,
    CreateTarfileStage,
    DownloadFileStage)

from dbd.oozie import BuildOozieStage, OoziePipelineBuilder, ShellCommandExecutor

from .temp_dir_test_case import TmpDirTestCase
from .test_default_component_image_builder.test_pipeline.pipeline_builder_testcase import PipelineBuilderTestCase

class MockShellCommandExecutor(ShellCommandExecutor):
    def run(self, command: List[str]) -> None:
        pass

class TestBuildOozieStage(TmpDirTestCase):
    def test_execute_distro_archive_present_at_dest_path(self) -> None:
        source_archive = self._tmp_dir_path / "oozie.tar.gz"
        TestBuildOozieStage._create_archive(source_archive)
        self.assertTrue(source_archive.exists())

        dest_path = self._tmp_dir_path / "oozie-disto.tar.gz"

        shell_command_executor = MockShellCommandExecutor()
        hadoop_version = "2.8.5"
        stage = BuildOozieStage("distro", shell_command_executor, hadoop_version)

        stage.execute(source_archive, dest_path)

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

class TestOoziePipelineBuilder(PipelineBuilderTestCase):
    def test_snapshot_mode(self) -> None:
        arguments = self.get_default_arguments()

        pipeline_builder = OoziePipelineBuilder()

        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, CreateTarfileStage))
        self.assertEqual([], pipeline.inner_stages)
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))

    def test_oozie_builder_adds_build_oozie_stage_in_release_mode(self) -> None:
        arguments = self.get_default_arguments()
        arguments["built_config"].components["hadoop"] = ComponentConfig(DistType.RELEASE, "2.8.5", "no-image")
        arguments["dist_info"] = DistInfo(DistType.RELEASE, "5.0.0")

        pipeline_builder = OoziePipelineBuilder()

        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, DownloadFileStage))
        self.assertEqual(1, len(pipeline.inner_stages))
        self.assertTrue(isinstance(pipeline.inner_stages[0], BuildOozieStage))
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))
