#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from pathlib import Path

from typing import Dict, List

import docker

from component_builder import ComponentConfig, Configuration, DistInfo, DistType
from default_component_image_builder.cache import Cache
from default_component_image_builder.stages import (
    BuildDockerImageStage,
    CreateTarfileStage,
    DefaultDownloader,
    DownloadFileStage,
    ImageBuiltStage)

from stage import Stage

class StageListBuilder(metaclass=ABCMeta):
    """
    An interface for classes that build lists of `Stage` objects according to the provided configuration.
    """

    @abstractmethod
    def build_stage_list(self,
                         component_name: str,
                         dependencies: List[str],
                         url_template: str,
                         image_name: str,
                         dist_info: DistInfo,
                         docker_context_dir: Path,
                         cache: Cache,
                         built_config: Configuration) -> List[Stage]:
        pass

class DefaultStageListBuilder(StageListBuilder):
    def __init__(self) -> None:
        self._docker_client = docker.from_env() # TODO

    def build_stage_list(self,
                         component_name: str,
                         dependencies: List[str],
                         url_template: str,
                         image_name: str,
                         dist_info: DistInfo,
                         docker_context_dir: Path,
                         cache: Cache,
                         built_config: Configuration) -> List[Stage]:
        archive_dest_path = self._get_archive_dest_path(cache, dist_info, component_name)

        file_deps = [archive_dest_path]

        stage_list: List[Stage] = [
            self._archive_retrieval_stage(archive_dest_path,
                                          dist_info,
                                          url_template),
            self._build_docker_image_stage(image_name,
                                           docker_context_dir,
                                           dependencies,
                                           built_config.components,
                                           file_deps),
            ImageBuiltStage(self._docker_client, image_name)]

        return stage_list

    def _archive_retrieval_stage(self,
                                 archive_dest_path: Path,
                                 dist_info: DistInfo,
                                 url_template: str) -> Stage:

        # pylint: disable=no-else-return
        if dist_info.dist_type == DistType.RELEASE:
            downloader = DefaultDownloader()
            version = dist_info.argument
            url = url_template.format(version)
            return DownloadFileStage(downloader, url, archive_dest_path)
        elif dist_info.dist_type == DistType.SNAPSHOT:
            source_dir = Path(dist_info.argument)
            return CreateTarfileStage(source_dir, archive_dest_path)
        else:
            raise ValueError("Unexpected DistType value.")

    def _build_docker_image_stage(self,
                                  image_name: str,
                                  build_directory: Path,
                                  dependencies: List[str],
                                  component_configs: Dict[str, ComponentConfig],
                                  file_dependencies: List[Path]) -> Stage:
        dependency_images = {dependency : component_configs[dependency].image_name for dependency in dependencies}

        return BuildDockerImageStage(self._docker_client,
                                     image_name,
                                     dependency_images,
                                     build_directory,
                                     file_dependencies)

    def _get_archive_dest_path(self,
                               cache: Cache,
                               dist_info: DistInfo,
                               component_name: str) -> Path:
        id_string: str
        if dist_info.dist_type == DistType.RELEASE:
            id_string = dist_info.argument
        else:
            id_string = "snapshot" # TODO: prevent caching.

        archive_dir = cache.get_path("archive", dist_info.dist_type, component_name, id_string)

        return archive_dir / "{}.tar.gz".format(component_name)
