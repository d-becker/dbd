#!/usr/bin/env python3

"""
This module contains the `PipelineBuilder` interface and a default implementation.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path

from typing import Dict

import docker

from component_builder import ComponentConfig, DistInfo, DistType
from default_component_image_builder.pipeline import EntryStage, Pipeline

from default_component_image_builder.stages import (
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
                       dependencies: Dict[str, ComponentConfig],
                       url_template: str,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        """
        Builds a pipeline from the provided configuration.

        Args:
            dependencies: The names of the other components that the component depends on.
            url_template: A url templated with the version number of the component, from which the release
                 archive can be downloaded. In the string, \"{0}\" is the placholder for the version number.
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
                       dependencies: Dict[str, ComponentConfig],
                       url_template: str,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        entry_stage = DefaultPipelineBuilder._get_entry_stage(dist_info, url_template)
        docker_image_stage = DefaultPipelineBuilder._get_docker_image_stage(docker.from_env(),
                                                                            image_name,
                                                                            dependencies,
                                                                            docker_context_dir)

        return Pipeline(entry_stage, [], docker_image_stage)

    @staticmethod
    def _get_entry_stage(dist_info: DistInfo, url_template: str) -> EntryStage:
        # pylint: disable=no-else-return
        if dist_info.dist_type == DistType.RELEASE:
            downloader = DefaultDownloader()
            version = dist_info.argument
            url = url_template.format(version)
            return DownloadFileStage("archive", downloader, url)
        else:
            assert dist_info.dist_type == DistType.SNAPSHOT

            source_dir = Path(dist_info.argument).expanduser().resolve()
            return CreateTarfileStage("archive", source_dir)

    @staticmethod
    def _get_docker_image_stage(docker_client: docker.DockerClient,
                                image_name: str,
                                dependencies: Dict[str, ComponentConfig],
                                docker_context_dir: Path) -> BuildDockerImageStage:
        dependency_images = {key : dependencies[key].image_name for key in dependencies}

        return BuildDockerImageStage("docker",
                                     docker_client,
                                     image_name,
                                     dependency_images,
                                     docker_context_dir)
