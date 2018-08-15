#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path
import subprocess
import tarfile
import tempfile
from typing import List, Optional

import docker

from component_builder import ComponentImageBuilder, Configuration, DistInfo, DistType
from default_component_image_builder.builder import (DefaultComponentImageBuilder,
                                                     StageListBuilder)
from default_component_image_builder.cache import Cache
from default_component_image_builder.stages import BuildDockerImageStage
from default_component_image_builder.stage_list_builder import DefaultStageListBuilder
from stage import Stage

class ShellCommandExecutor(metaclass=ABCMeta):
    @abstractmethod
    def run(self, command: List[str]) -> None:
        pass

class DefaultShellCommandExecutor(ShellCommandExecutor):
    def run(self, command: List[str]) -> None:
        subprocess.run(command, check=True)

class BuildOozieStage(Stage):
    def __init__(self,
                 release_archive: Path,
                 dest_path: Path,
                 shell_command_executor: ShellCommandExecutor) -> None:
        self._release_archive = release_archive.expanduser().resolve()
        self._dest_path = dest_path.expanduser().resolve()
        self._shell_command_executor = shell_command_executor

    def name(self) -> str:
        return "build_oozie"

    def check_precondition(self) -> bool:
        if not self._release_archive.exists():
            logging.info("Stage %s precondition check: the release archive does not exist: %s.",
                         self.name(),
                         self._release_archive)
            return False

        return True

    def execute(self) -> None:
        logging.info("Stage %s: Extracting the downloaded Oozie tar file.", self.name())

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            with tarfile.open(self._release_archive) as tar:
                tar.extractall(path=tmp_dir)

                oozie_dirs = list(tmp_dir.glob("oozie*"))

                if len(oozie_dirs) != 1:
                    raise ValueError("There should be exactly one oozie* directory.")

                oozie_dir = oozie_dirs[0]
                script_file = oozie_dir / "bin" / "mkdistro.sh"
                command = [str(script_file),
                           "-Puber",
                           "-Ptez",
                           "-DskipTests"]

                logging.info("Build command: %s.", " ".join(command))

                self._shell_command_executor.run(command)

                distro_file_paths = list((oozie_dir / "distro" / "target").glob("oozie-*-distro.tar.gz"))

                if len(distro_file_paths) != 1:
                    raise ValueError("There should be exactly one oozie-*-distro.tar.gz directory.")

                distro_file_path = distro_file_paths[0]

                self._dest_path.parent.mkdir(parents=True, exist_ok=True)
                distro_file_path.rename(self._dest_path)

class OozieStageListBuilder(StageListBuilder):
    def __init__(self) -> None:
        self._default_builder = DefaultStageListBuilder()

    def build_stage_list(self,
                         component_name: str,
                         dependencies: List[str],
                         url_template: str,
                         image_name: str,
                         dist_info: DistInfo,
                         docker_context_dir: Path,
                         cache: Cache,
                         built_config: Configuration) -> List[Stage]:
        default_stage_list = self._default_builder.build_stage_list(component_name,
                                                                    dependencies,
                                                                    url_template,
                                                                    image_name,
                                                                    dist_info,
                                                                    docker_context_dir,
                                                                    cache,
                                                                    built_config)
        download_stage_index = OozieStageListBuilder._get_download_stage_index(default_stage_list)

        if download_stage_index is not None:
            assert dist_info.dist_type == DistType.RELEASE

            archive_path = cache.get_path("archive",
                                          dist_info.dist_type,
                                          component_name,
                                          dist_info.argument) / "oozie.tar.gz"
            distro_path = cache.get_path("distro",
                                         dist_info.dist_type,
                                         component_name,
                                         dist_info.argument) / "oozie.tar.gz"

            build_oozie_stage = BuildOozieStage(archive_path, distro_path, DefaultShellCommandExecutor())

            default_stage_list.insert(download_stage_index + 1, build_oozie_stage)

            docker_stage_index = download_stage_index + 2
            assert isinstance(default_stage_list[docker_stage_index], BuildDockerImageStage)

            # TODO: See if this can be solved more elegantly and without less code duplication.
            dependency_images = {dependency : built_config.components[dependency].image_name
                                 for dependency in dependencies}
            file_dependencies = [distro_path]

            new_docker_stage = BuildDockerImageStage(docker.from_env(),
                                                     image_name,
                                                     dependency_images,
                                                     docker_context_dir,
                                                     file_dependencies)
            default_stage_list[docker_stage_index] = new_docker_stage
        else:
            assert dist_info.dist_type == DistType.SNAPSHOT

        return default_stage_list

    @staticmethod
    def _get_download_stage_index(stage_list: List[Stage]) -> Optional[int]:
        enumerated = enumerate(stage_list)
        filtered = filter(lambda t: t[1].name() == "download_file", enumerated)

        element = next(filtered, None)

        if element is None:
            return element

        return element[0]

def get_image_builder(dependencies: List[str], cache_dir: Path) -> ComponentImageBuilder:
    url_template = "https://archive.apache.org//dist/oozie/{0}/oozie-{0}.tar.gz"
    version_command = "bin/oozied.sh start && bin/oozie version"
    version_regex = "version: (.*)\n"
    stage_list_builder = OozieStageListBuilder()

    cache = Cache(cache_dir,
                  {"archive" : Path("archive"),
                   "distro" : Path("distro")})

    return DefaultComponentImageBuilder("oozie",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        stage_list_builder)
