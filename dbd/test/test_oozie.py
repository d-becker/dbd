#!/usr/bin/env python3

# pylint: disable=missing-docstring

import tarfile
import tempfile
from typing import Dict, List
from pathlib import Path

from dbd.component_config import ComponentConfig, DistInfo, DistType

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

    def test_hbase_jar_version_argument_is_added_if_kerberised(self) -> None:
        self._test_hbase_jar_version_argument_is_added(True)

    def test_hbase_jar_version_argument_is_not_added_if_not_kerberised(self) -> None:
        self._test_hbase_jar_version_argument_is_added(False)

    def _test_hbase_jar_version_argument_is_added(self, kerberos: bool) -> None:
        jar_version = "1.1.1"
        arguments = self.get_default_arguments(kerberos)
        arguments["component_input_config"] = {"snapshot": "/path/to/distribution",
                                               "hbase-common-jar-version": jar_version}

        pipeline_builder = OoziePipelineBuilder()

        pipeline = pipeline_builder.build_pipeline(**arguments)

        docker_stage = pipeline.final_stage

        assert isinstance(docker_stage, BuildDockerImageStage)
        build_args: Dict[str, str] = docker_stage.get_build_args()

        hbase_common_jar_version_string = "HBASE_COMMON_JAR_VERSION"
        self.assertEqual(kerberos, hbase_common_jar_version_string in build_args)

        if kerberos:
            self.assertEqual(jar_version, build_args[hbase_common_jar_version_string])
