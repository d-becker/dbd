#!/usr/bin/env python3

"""
This module contains the default implementation of the `component_builder.ComponentImageBuilder` interface. For more
details, see the class documentation.

"""

import hashlib
import os

from pathlib import Path

import re

from typing import Dict, Iterable, List, Tuple

import docker

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration, DistType, DistInfo
from default_component_image_builder.assembly import Assembly
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline.builder import PipelineBuilder
from default_component_image_builder.pipeline.executor import PipelineExecutor

class DefaultComponentImageBuilder(ComponentImageBuilder):
    """
    This class is the default implementation of the `component_builder.ComponentImageBuilder` interface. It tries to
    extract and provide what is common in all (or most) image build processes but remain general and
    flexible. Individual components' image builders can be instances of this class directly, subclassing may not be
    necessary.

    The component image building process uses the following model. The building process is divided into stages. The
    process is then a pipeline built up of these stages: each stage produces an intermediate result, which will be the
    input of the next stage. The intermediate results are cached on the filesystem, so that it is not always necessary
    to execute all stages. The cache locations can be customised through the `cache` parameter.

    To customise the image builder to build the image for a specific component, a suitable pipeline builder has to be
    provided. The pipeline builder is responsible for generating the pipeline stages for a given component and
    configuration. Each time the `build` method of the image builder is called, the pipeline builder will be used to
    generate a pipeline for that particular configuration - the pipeline is not fixed for a component, it may for
    example depend on whether the component distribution is a release or a snapshot build.

    For more information about how pipelines work, see the `pipeline` package's documentation.

    """

    def __init__(self,
                 component_name: str,
                 assembly: Assembly,
                 cache: Cache,
                 pipeline_builder: PipelineBuilder) -> None:
        """
        Creates a new `DefaultComponentImageBuilder` object.

        Args:
            component_name: The name of the component for which the image is built.
            assembly: An object holding component-specific information.
            cache: The object from which cache locations can be queried.
            pipeline_builder: The pipeline builder to be used to generate the build stages.

        """

        self._name = component_name
        self._assembly = assembly
        self._cache = cache
        self._pipeline_builder = pipeline_builder

        self._docker_client = docker.from_env()

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List[str]:
        return self._assembly.dependencies

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        (dist_type, argument) = _dist_type_and_arg(component_config)
        dist_info = DistInfo(dist_type, argument)
        id_string = _get_id_string(dist_info)
        image_name = self._get_image_name(id_string,
                                          built_config)

        docker_context = built_config.resource_path / self.name() / "docker_context"

        pipeline = self._pipeline_builder.build_pipeline(built_config,
                                                         self._assembly,
                                                         image_name,
                                                         dist_info,
                                                         docker_context)
        pipeline_executor = PipelineExecutor()

        if force_rebuild:
            pipeline_executor.execute_all(self.name(),
                                          dist_type,
                                          id_string,
                                          self._cache,
                                          pipeline)
        else:
            if not _image_exists_locally(self._docker_client, image_name):
                pipeline_executor.execute_needed(self.name(),
                                                 dist_type,
                                                 id_string,
                                                 self._cache,
                                                 pipeline)

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            if self._assembly.version_command is None:
                raise ValueError(
                    "The `version_command` key is missing from the assembly but needed to find out the version number.")

            if self._assembly.version_regex is None:
                raise ValueError(
                    "The `version_regex` key is missing from the assembly but needed to find out the version number.")

            version = _find_out_version_from_image(self._docker_client,
                                                   image_name,
                                                   self.name(),
                                                   self._assembly.version_command,
                                                   self._assembly.version_regex)
        return ComponentConfig(dist_type, version, image_name)

    def _get_image_name(self,
                        id_string: str,
                        built_config: Configuration) -> str:
        template = "{repository}/{component}:{component_tag}{dependencies_tag}"

        dependencies = self.dependencies()
        dependencies.sort()

        deps_join_list: List[str] = [""]
        for dependency in dependencies:
            dependency_tag = built_config.components[dependency].image_name.split(":")[-1]
            deps_join_list.append(dependency + dependency_tag)

        dependencies_tag = "_".join(deps_join_list)

        return template.format(repository=built_config.repository,
                               component=self.name(),
                               component_tag=id_string,
                               dependencies_tag=dependencies_tag)


def _dist_type_and_arg(component_config: Dict[str, str]) -> Tuple[DistType, str]:
    """
    Returns the distribution type (release or snapshot) and the corresponding argument
    (version or path to snapshot buid) from a component configuration dictionary.

    Args:
        component_config: A dictionary containing information about a component.

    Returns:
        The distribution type (release or snapshot) and the corresponding argument (version or path to snapshot buid).

        """

    release_specified = "release" in component_config
    snapshot_specified = "snapshot" in component_config

    if release_specified and snapshot_specified:
        raise ValueError("Both release and snapshot mode specified.")

    if not release_specified and not snapshot_specified:
        raise ValueError("None of release and snapshot mode specified.")

    # pylint: disable=no-else-return
    if release_specified:
        version = component_config["release"]
        return (DistType.RELEASE, version)
    else:
        path = component_config["snapshot"]
        return (DistType.SNAPSHOT, path)

def _image_exists_locally(docker_client: docker.DockerClient, image_name: str) -> bool:
    """
    Returns whether there exists a docker image with name `image_name` locally.

    Args:
        image_name: The name of the docker image to check.

    Returns:
        True if the docker image with the given name exists; False otherwise.
    """

    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound:
        return False
    else:
        return True

def _find_out_version_from_image(docker_client: docker.DockerClient,
                                 image_name: str,
                                 component_name: str,
                                 command: str,
                                 regex: str) -> str:
    """
    Retrieves the version of a component from a docker image.

    Args:
        docker_client: The docker client object to use when starting the container.
        image_name: The name of the docker image from which the version should be retrieved.
        componenet_name: The name of the component the version of which should be retrieved.
        command: The command to run inside the docker container - the output should contain the version number.
        regex: A regular expression that will be matched against the output of `command` using the `re.search`
            function. Group 1 of the regex should catch the verion number string.
    Returns: The version number as a string.
    Raises: ValueError: If no match is found.

    """

    # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
    command_to_use = "{} && exit 0".format(command)
    response_bytes = docker_client.containers.run(image_name, command_to_use, auto_remove=True)
    response = response_bytes.decode()

    match = re.search(regex, response)

    if match is None:
        raise ValueError("No {} version found.".format(component_name))

    version = match.group(1)
    return version

def _get_id_string(dist_info: DistInfo) -> str:
    # pylint: disable=no-else-return
    if dist_info.dist_type == DistType.RELEASE:
        # The id_string is the version string.
        version = dist_info.argument
        return version
    else:
        # The id_string is the hash of the source path prepended to the last modification of the source path tree.
        source_path = Path(dist_info.argument).expanduser().resolve()
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
