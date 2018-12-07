#!/usr/bin/env python3

# pylint: disable=missing-docstring

from dbd.component_config import DistInfo, DistType
from dbd.default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

from dbd.default_component_image_builder.stages import (
    BuildDockerImageStage,
    CreateTarfileStage,
    DownloadFileStage)

from .pipeline_builder_testcase import PipelineBuilderTestCase

class TestDefaultPipelineBuilder(PipelineBuilderTestCase):
    def test_snapshot_build_has_create_tarfile_stage(self) -> None:
        arguments = self.get_default_arguments()
        arguments["dist_info"] = DistInfo(DistType.SNAPSHOT, "path/to/snapshot_build")

        pipeline_builder = DefaultPipelineBuilder()
        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, CreateTarfileStage))
        self.assertEqual([], pipeline.inner_stages)
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))

    def test_release_build_has_download_file_stage(self) -> None:
        arguments = self.get_default_arguments()
        arguments["dist_info"] = DistInfo(DistType.RELEASE, "5.0.0")

        pipeline_builder = DefaultPipelineBuilder()
        pipeline = pipeline_builder.build_pipeline(**arguments)

        self.assertTrue(isinstance(pipeline.entry_stage, DownloadFileStage))
        self.assertEqual([], pipeline.inner_stages)
        self.assertTrue(isinstance(pipeline.final_stage, BuildDockerImageStage))
