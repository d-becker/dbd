#!/usr/bin/env python3

import re

from typing import Dict, List, Optional, Tuple

import docker

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration, DistType, DistInfo
from default_component_image_builder.cache import Cache
from default_component_image_builder.stage_list_builder import StageListBuilder
from stage import StageChain

class DefaultComponentImageBuilder(ComponentImageBuilder):
    # TODO: Add more information to the docstring about how the images are built (using stages) and how it can be
    # customised (for example by adding stages through providing a different stage_list_builder).

    """
    A class that implements the common functionality that is needed to implement the `ComponentImageBuilder`
    interface. The constructor parameters make it possible to customise the behaviour to fit the actual component.

    """

    def __init__(self,
                 component_name: str,
                 dependencies: List[str],
                 url_template: str,
                 version_command: str,
                 version_regex: str,
                 cache: Cache,
                 stage_list_builder: StageListBuilder) -> None:
        self._name = component_name
        self._dependencies = dependencies
        self._url_template = url_template # A string with {0} which will be formatted with the version.
        self._version_command = version_command
        self._version_regex = version_regex
        self._cache = cache
        self._stage_list_builder = stage_list_builder

        self._docker_client = docker.from_env()

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List[str]:
        return self._dependencies

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        (dist_type, argument) = dist_type_and_arg(component_config)
        image_name = self._get_image_name(dist_type,
                                          argument if dist_type == DistType.RELEASE else None,
                                          built_config)

        dist_info = DistInfo(dist_type, argument)
        docker_context = built_config.resource_path / self.name() / "docker_context"

        stages = self._stage_list_builder.build_stage_list(self.name(),
                                                           self.dependencies(),
                                                           self._url_template,
                                                           image_name,
                                                           dist_info,
                                                           docker_context,
                                                           self._cache,
                                                           built_config)
        stage_executor = StageChain(stages)

        if force_rebuild:
            stage_executor.execute_in_order()
        else:
            stage_executor.execute_needed()

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            version = find_out_version_from_image(self._docker_client,
                                                  image_name,
                                                  self.name(),
                                                  self._version_command,
                                                  self._version_regex)

        return ComponentConfig(dist_type, version, image_name)

    def _get_image_name(self,
                        dist_type: DistType,
                        version: Optional[str],
                        built_config: Configuration) -> str:
        template = "{repository}/{component}:{component_tag}{dependencies_tag}"

        component_tag: str
        if dist_type == DistType.RELEASE:
            if version is None:
                raise ValueError("The version is None but release mode is specified.")
            component_tag = version
        elif dist_type == DistType.SNAPSHOT:
            component_tag = "snapshot_{}".format(built_config.timestamp)
        else:
            raise RuntimeError("Unexpected value of DistType.")

        dependencies_tag: str
        dependencies = self.dependencies()
        dependencies.sort()

        deps_join_list: List[str] = [""]
        for dependency in dependencies:
            dependency_tag = built_config.components[dependency].image_name.split(":")[-1]
            deps_join_list.append(dependency + dependency_tag)

        dependencies_tag = "_".join(deps_join_list)

        return template.format(repository=built_config.repository,
                               component=self.name(),
                               component_tag=component_tag,
                               dependencies_tag=dependencies_tag)


def dist_type_and_arg(component_config: Dict[str, str]) -> Tuple[DistType, str]:
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

def find_out_version_from_image(docker_client: docker.DockerClient,
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
