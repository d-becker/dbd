#!/usr/bin/env python3

"""
This module contains the `PipelineBuilder` interface and a default implementation.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path

from typing import Any, Dict, Optional

import docker

from dbd.configuration import Configuration
from dbd.component_config import ComponentConfig, DistInfo, DistType
from dbd.default_component_image_builder.assembly import Assembly
from dbd.default_component_image_builder.pipeline import EntryStage, Pipeline

from dbd.default_component_image_builder.stages import (
    BuildDockerImageStage,
    CreateTarfileStage,
    DefaultDownloader,
    DownloadFileStage)

class PipelineBuilder(metaclass=ABCMeta):
    """
    An interface for classes that build pipelines from the provided configuration.
    """

    @abstractmethod
    def build_pipeline(self,
                       built_config: Configuration,
                       component_input_config: Dict[str, Any],
                       assembly: Assembly,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        """
        Builds a pipeline from the provided configuration.

        Args:
            built_config: A `Configuration` object that contains information about
                previously built components and images. This should never be modified.
            component_input_config: A dictionary of component-specific extra configuration.
                This is inside the `release` or `snapshot` section in the `BuildConfiguration` file.
            assembly: An object holding component-specific information.
            image_name: The name of the docker image that will be built.
            dist_info: Information about the distribution type (release or snapshot).
            docker_context_dir: The path to the static (non-generated) resources that need
                to be present in the docker build directory when the image is built.
        """

        pass

class DefaultPipelineBuilder(PipelineBuilder):
    """
    The default implementation of the `PipelineBuilder` interface. It generates two stages: the first either downloads
    the release archive for the component (release builds) or creates a tar archive from the distribution directory on
    the local filesystem (snapshot builds), the second builds the docker image for the component.

    """

    def build_pipeline(self,
                       built_config: Configuration,
                       component_input_config: Dict[str, Any],
                       assembly: Assembly,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        entry_stage = DefaultPipelineBuilder._get_entry_stage(dist_info, assembly.url_template)

        dependencies = {dependency : built_config.components[dependency]
                        for dependency in assembly.dependencies}

        docker_image_stage = DefaultPipelineBuilder.get_docker_image_stage(docker.from_env(),
                                                                           image_name,
                                                                           dependencies,
                                                                           docker_context_dir,
                                                                           dict())

        return Pipeline(entry_stage, [], docker_image_stage)

    @staticmethod
    def get_docker_image_stage(docker_client: docker.DockerClient,
                               image_name: str,
                               dependencies: Dict[str, ComponentConfig],
                               docker_context_dir: Path,
                               build_args: Dict[str, str]) -> BuildDockerImageStage:
        """
        Returns a `BuildDockerImageStage` object with the given parameters.

        Args:
            docker_client: A docker client object.
            image_name: The name of the image the `BuildDockerImageStage` will build.
            dependencies: A dictionary with the dependencies of the component to be built, where
                the keys are the names and the values are the configuration of the dependencies.
            docker_context_dir: The path to the directory that will be
                the docker context when building the docker image.
            build_args: A dictionary of arguments in the Dockerfile.

        Returns:
            A `BuildDockerImageStage` object with the given parameters.

        """

        dependency_images = {key : dependencies[key].image_name for key in dependencies}

        return BuildDockerImageStage("docker",
                                     docker_client,
                                     image_name,
                                     dependency_images,
                                     docker_context_dir,
                                     build_args)

    @staticmethod
    def _get_entry_stage(dist_info: DistInfo, url_template: Optional[str]) -> EntryStage:
        # pylint: disable=no-else-return
        if dist_info.dist_type == DistType.RELEASE:
            downloader = DefaultDownloader()
            version = dist_info.argument

            if url_template is None:
                raise ValueError("The `url` key is missing from the assembly but needed to download the component.")

            url = url_template.format(version=version)
            return DownloadFileStage("archive", downloader, url)
        else:
            assert dist_info.dist_type == DistType.SNAPSHOT

            source_dir = Path(dist_info.argument).expanduser().resolve()
            return CreateTarfileStage("archive", source_dir)
