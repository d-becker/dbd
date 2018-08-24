#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import Any, Dict
from pathlib import Path

from component_builder import Configuration, DistInfo, DistType
from default_component_image_builder.assembly import Assembly
from default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

from default_component_image_builder.stages import (
    BuildDockerImageStage,
    CreateTarfileStage,
    DownloadFileStage)

from ...temp_dir_test_case import TmpDirTestCase

class TestDefaultPipelineBuilder(TmpDirTestCase):
    def _get_arguments(self) -> Dict[str, Any]:
        return {
            "built_config" : Configuration("test_configuration_name", "0001", "test_repository", self._tmp_dir_path),
            "assembly" : Assembly.from_dict({"url": "some_url"}),
            "image_name" : "test_image",
            "dist_info" : DistInfo(DistType.SNAPSHOT, "path/to/snapshot_build"),
            "docker_context_dir" : Path("path/to/docker/context")
        }

    def test_snapshot_build_has_create_tarfile_stage(self) -> None:
        arguments = self._get_arguments()
        arguments["dist_info"] = DistInfo(DistType.SNAPSHOT, "path/to/snapshot_build")

        pipeline_builder = DefaultPipelineBuilder()
        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, CreateTarfileStage))
        self.assertEqual([], pipeline.inner_stages)
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))

    def test_release_build_has_download_file_stage(self) -> None:
        arguments = self._get_arguments()
        arguments["dist_info"] = DistInfo(DistType.RELEASE, "5.0.0")

        pipeline_builder = DefaultPipelineBuilder()
        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, DownloadFileStage))
        self.assertEqual([], pipeline.inner_stages)
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))
