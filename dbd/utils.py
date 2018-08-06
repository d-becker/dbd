#!/usr/bin/env python3

"""
This module contains utility functions that other modules can use.

"""

import re
import shutil

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

import docker

from component_builder import DistType

def image_exists_locally(client: docker.DockerClient, image_name: str) -> bool:
    """
    Checks whether a docker image with a given name exists locally.

    Args:
        client: The docker client to use to check whether the given image exists.
        image_name: The name of the docker image to check.

    Returns:
        True if the docker image with name `image_name` exists locally; False otherwise.

    """

    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        return False
    else:
        return True

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

class TmpDirHandler:
    def __init__(self, base_path: Path) -> None:
        if not base_path.is_dir():
            raise ValueError("The base directory path is not a directory.")

        self._base_path = base_path

    @property
    def base_path(self) -> Path:
        return self._base_path

    def get_tmp_dir_path(self) -> Path:
        return self.base_path / "tmp"

    def create_tmp_dir(self) -> None:
        self.remove_tmp_dir()
        self.get_tmp_dir_path().mkdir()

    def remove_tmp_dir(self) -> None:
        tmp_path = self.get_tmp_dir_path()
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    def __enter__(self) -> Path:
        self.create_tmp_dir()
        return self.get_tmp_dir_path()

    def __exit__(self, exc_type: Optional[Type], exc_value: Any, traceback: Any) -> bool:
        self.remove_tmp_dir()
        return False
