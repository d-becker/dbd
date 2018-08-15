#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import hashlib
import os
from pathlib import Path

from typing import Dict, Iterable, List

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
        archive_id_string = self._get_archive_id_string(dist_info)
        archive_dest_path = cache.get_path("archive",
                                           dist_info.dist_type,
                                           component_name,
                                           archive_id_string) / "{}.tar.gz".format(component_name)

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

    @staticmethod
    def _archive_retrieval_stage(archive_dest_path: Path,
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

    @staticmethod
    def _get_archive_id_string(dist_info: DistInfo) -> str:
        if dist_info.dist_type == DistType.RELEASE:
            # The id_string is the version string.
            version = dist_info.argument
            return version
        else:
            # The id_string is the hash of the source path prepended to the last modification of the source path tree.
            # TODO: This caching could be extended to the image names, too.
            source_path = Path(dist_info.argument)
            source_path_hash = hashlib.sha1(str(source_path).encode()).hexdigest()
            last_mod = _get_last_modification_in_directory_tree(source_path)
            return "{}_{}".format(source_path_hash, str(int(last_mod)))

def _get_last_modification_in_directory_tree(directory: Path) -> float:
    return max(map(lambda path: path.stat().st_mtime, _generate_all_paths(directory)))

def _generate_all_paths(directory: Path) -> Iterable[Path]:
    dir_path = Path(directory.expanduser().resolve())
    if not dir_path.is_dir():
        yield dir_path
    else:
        for dirpath, _, filenames in os.walk(dir_path):
            yield Path(dirpath)
            for  filename in filenames:
                yield Path(dirpath) / filename
