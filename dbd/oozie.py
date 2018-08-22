#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the
Oozie component and some Oozie-specific classes that the function depends on.
"""

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path
import subprocess
import tarfile
import tempfile
from typing import Dict, List

from component_builder import ComponentConfig, ComponentImageBuilder, DistInfo, DistType
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import Pipeline, Stage
from default_component_image_builder.pipeline.builder import DefaultPipelineBuilder, PipelineBuilder

class ShellCommandExecutor(metaclass=ABCMeta):
    """
    An interface for objects that can execute shell commands.
    """

    @abstractmethod
    def run(self, command: List[str]) -> None:
        """
        Runs the provided shell commands.

        Args:
            command: The command to run as a list - the first element is the executable name, the others are arguments.
        """
        pass

class DefaultShellCommandExecutor(ShellCommandExecutor):
    """
    The default shell command executor. It uses python's `subprocess` module to run the commands.
    """

    def run(self, command: List[str]) -> None:
        subprocess.run(command, check=True)

class BuildOozieStage(Stage):
    """
    A stage that builds the Oozie distribution from source.
    """

    def __init__(self,
                 name: str,
                 shell_command_executor: ShellCommandExecutor) -> None:
        """
        Creates a new `BuildOozieStage` object.

        Args:
            name: The name of the stage.
            shell_command_executor: The `ShellCommandExecutor` to use.

        """

        self._name = name
        self._shell_command_executor = shell_command_executor

    def name(self) -> str:
        return self._name

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
    """
    A `PipelineBuilder` that builds pipelines for the Oozie component.
    """

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
            build_oozie_stage = BuildOozieStage("distro", DefaultShellCommandExecutor())
            pipeline.inner_stages.insert(0, build_oozie_stage)

        return pipeline

def get_image_builder(dependencies: List[str], cache_dir: Path) -> ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Oozie docker images.

    Args:
        dependencies: The names of the components that this component depends on.
        cache_dir: The path to the global cache directory.
    """
    
    pipeline_builder = OoziePipelineBuilder()

    cache = Cache(cache_dir)

    return DefaultComponentImageBuilder("oozie",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
