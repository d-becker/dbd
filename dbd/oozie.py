#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the
Oozie component and some Oozie-specific classes that the function depends on.

For kerberised Oozie component, you can specify the "hbase-common-jar-version" configuration option
in the `BuildConfiguration file. Its value is the version number of the hbase-common-{version}.jar
that will be added to the Oozie image.
"""

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from typing import Any, Dict, List

import docker

from dbd.configuration import Configuration
from dbd.component_builder import ComponentImageBuilder
from dbd.component_config import DistInfo, DistType
import dbd.defaults
from dbd.default_component_image_builder.assembly import Assembly
from dbd.default_component_image_builder.builder import DefaultComponentImageBuilder
from dbd.default_component_image_builder.cache import Cache
from dbd.default_component_image_builder.pipeline import Pipeline, Stage
from dbd.default_component_image_builder.pipeline.builder import DefaultPipelineBuilder, PipelineBuilder
from dbd.default_component_image_builder.pipeline.executor import DefaultPipelineExecutor

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
                 shell_command_executor: ShellCommandExecutor,
                 hadoop_version: str) -> None:
        """
        Creates a new `BuildOozieStage` object.

        Args:
            name: The name of the stage.
            shell_command_executor: The `ShellCommandExecutor` to use.
            hadoop_version: The Hadoop version against which Oozie will be built.

        """

        self._name = name
        self._shell_command_executor = shell_command_executor
        self._hadoop_version = hadoop_version

    def name(self) -> str:
        return self._name

    def execute(self, input_path: Path, output_path: Path) -> None:
        if not BuildOozieStage._is_maven_available():
            msg = "Maven does not seem to be installed but is needed to build Oozie: missing command `mvn`."
            logging.error("Stage %s: %s", self.name(), msg)
            raise ValueError(msg)

        logging.info("Stage %s: Extracting the downloaded Oozie tar file.", self.name())

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            with tarfile.open(input_path) as tar:
                
                import os
                
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, path=tmp_dir)

                oozie_dirs = list(tmp_dir.glob("oozie*"))

                if len(oozie_dirs) != 1:
                    raise ValueError("There should be exactly one oozie* directory.")

                oozie_dir = oozie_dirs[0]
                script_file = oozie_dir / "bin" / "mkdistro.sh"
                command = [str(script_file),
                           "-Puber",
                           "-Ptez",
                           "-Dhadoop.version={}".format(self._hadoop_version),
                           "-DskipTests"]

                logging.info("Build command: %s.", " ".join(command))

                self._shell_command_executor.run(command)

                distro_file_paths = list((oozie_dir / "distro" / "target").glob("oozie-*-distro.tar.gz"))

                if len(distro_file_paths) != 1:
                    raise ValueError("There should be exactly one oozie-*-distro.tar.gz directory.")

                distro_file_path = distro_file_paths[0]

                output_path.parent.mkdir(parents=True, exist_ok=True)
                distro_file_path.rename(output_path)

    @staticmethod
    def _is_maven_available() -> bool:
        return shutil.which("mvn") is not None

class OoziePipelineBuilder(PipelineBuilder):
    """
    A `PipelineBuilder` that builds pipelines for the Oozie component.
    """

    def __init__(self) -> None:
        self._default_builder = DefaultPipelineBuilder()

    def build_pipeline(self,
                       built_config: Configuration,
                       component_input_config: Dict[str, Any],
                       assembly: Assembly,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        pipeline = self._default_builder.build_pipeline(built_config,
                                                        component_input_config,
                                                        assembly,
                                                        image_name,
                                                        dist_info,
                                                        docker_context_dir)

        if dist_info.dist_type == DistType.RELEASE:
            hadoop_version = built_config.components["hadoop"].version
            build_oozie_stage = BuildOozieStage("distro", DefaultShellCommandExecutor(), hadoop_version)
            pipeline.inner_stages.insert(0, build_oozie_stage)

        dependencies = {dependency : built_config.components[dependency]
                        for dependency in assembly.dependencies}

        # If using Kerberos, add hbase-common-jar-version argument to the Docker build process.
        if built_config.kerberos:
            hbase_common_jar_version = component_input_config.get("hbase-common-jar-version",
                                                                  dbd.defaults.HBASE_COMMON_JAR_VERSION)
            build_args = {"HBASE_COMMON_JAR_VERSION": hbase_common_jar_version}

            pipeline.final_stage = DefaultPipelineBuilder.get_docker_image_stage(docker.from_env(),
                                                                                 image_name,
                                                                                 dependencies,
                                                                                 docker_context_dir,
                                                                                 build_args)
        return pipeline

def get_image_builder(assembly: Dict[str, Any], cache: Cache) -> ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Oozie docker images.

    Args:
        assembly: An object containing component-specific information such as dependencies.
        cache: The `Cache` object that handles the global cache.
    """

    assembly_object = Assembly.from_dict(assembly)
    pipeline_builder = OoziePipelineBuilder()
    pipeline_executor = DefaultPipelineExecutor()

    return DefaultComponentImageBuilder("oozie",
                                        assembly_object,
                                        cache,
                                        pipeline_builder,
                                        pipeline_executor)
