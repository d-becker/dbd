#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path
import subprocess
import tarfile
import tempfile
from typing import Dict, List

from component_builder import ComponentConfig, ComponentImageBuilder, DistInfo, DistType
from default_component_image_builder.builder import default_cache_path_fragments, DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import Pipeline, Stage
from default_component_image_builder.pipeline_builder import DefaultPipelineBuilder, PipelineBuilder

class ShellCommandExecutor(metaclass=ABCMeta):
    @abstractmethod
    def run(self, command: List[str]) -> None:
        pass

class DefaultShellCommandExecutor(ShellCommandExecutor):
    def run(self, command: List[str]) -> None:
        subprocess.run(command, check=True)

class BuildOozieStage(Stage):
    def __init__(self,
                 shell_command_executor: ShellCommandExecutor) -> None:
        self._shell_command_executor = shell_command_executor

    def name(self) -> str:
        return "build_oozie"

    def execute(self, input_path: Path, output_path: Path) -> None:
        logging.info("Stage %s: Extracting the downloaded Oozie tar file.", self.name())

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            with tarfile.open(input_path) as tar:
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

                output_path.parent.mkdir(parents=True, exist_ok=True)
                distro_file_path.rename(output_path)

class OoziePipelineBuilder(PipelineBuilder):
    def __init__(self) -> None:
        self._default_builder = DefaultPipelineBuilder()

    def build_pipeline(self,
                       dependencies: Dict[str, ComponentConfig],
                       url_template: str,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        pipeline = self._default_builder.build_pipeline(dependencies,
                                                        url_template,
                                                        image_name,
                                                        dist_info,
                                                        docker_context_dir)

        if dist_info.dist_type == DistType.RELEASE:
            build_oozie_stage = BuildOozieStage(DefaultShellCommandExecutor())
            pipeline.inner_stages.insert(0, build_oozie_stage)

        return pipeline

def get_image_builder(dependencies: List[str], cache_dir: Path) -> ComponentImageBuilder:
    url_template = "https://archive.apache.org//dist/oozie/{0}/oozie-{0}.tar.gz"
    version_command = "bin/oozied.sh start && bin/oozie version"
    version_regex = "version: (.*)\n"
    pipeline_builder = OoziePipelineBuilder()

    cache_paths = default_cache_path_fragments()
    cache_paths[BuildOozieStage] = Path("distro")

    cache = Cache(cache_dir, cache_paths)

    return DefaultComponentImageBuilder("oozie",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
