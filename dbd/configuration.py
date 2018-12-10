#!/usr/bin/env python3

"""
This module provides a class that stores the configuration of the overall build.
"""

from pathlib import Path
from typing import Dict

from dbd.component_config import ComponentConfig

class Configuration:
    """
    A class that holds information about the overall build and on all components and images.
    """

    def __init__(self,
                 name: str,
                 timestamp: str,
                 repository: str,
                 kerberos: bool,
                 resource_path: Path) -> None:
        """
        Creates a new `Configuration` object.

        Args:
            name: The name of the BuildConfiguration (provided by the user).
            timestamp: The timestamp of the build.
            repository: The dockerhub repository to use when naming the images. Defaults to "dbd".
            kerberos: Whether Kerberos is enabled.
            resources_path: The path to the directory where the resources of the components are stored.

        """

        self._name = name
        self._timestamp = timestamp
        self._repository = repository

        self._kerberos = kerberos
        self._resource_path = resource_path
        self.components: Dict[str, ComponentConfig] = {}

    @property
    def name(self) -> str:
        """
        The name of the configuration (specified by the user).
        """

        return self._name

    @property
    def timestamp(self) -> str:
        """
        The timestamp of the current build of the configuration.
        """

        return self._timestamp

    @property
    def repository(self) -> str:
        """
        The docker repository to build the images in.
        """

        return self._repository

    def get_resource_dir(self, component_name: str) -> Path:
        """
        Returns the path to the resource directory of the component.

        Args:
            component_name: The name of the component.

        Returns:
            The path to the resource directory of the component.
        """

        return self._resource_path / component_name

    def get_assembly(self, component_name: str) -> Path:
        """
        Returns the path to the assembly file of the component.

        Args:
            component_name: The name of the component.

        Returns:
            The path to the assembly file of the component.
        """

        return self.get_resource_dir(component_name) / self._component_subdir() / "assembly.yaml"

    def get_compose_config_part(self, component_name: str) -> Path:
        """
        Returns the path to the compose-config_part file of the component.

        Args:
            component_name: The name of the component.

        Returns:
            The path to the compose-config_part file of the component.
        """

        return self.get_resource_dir(component_name) / self._component_subdir() / "compose-config_part"

    def get_docker_compose_part(self, component_name: str) -> Path:
        """
        Returns the path to the docker-compose_part.yaml file of the component.

        Args:
            component_name: The name of the component.

        Returns:
            The path to the docker-compose_part.yaml file of the component.
        """

        return self.get_resource_dir(component_name) / self._component_subdir() / "docker-compose_part.yaml"

    def get_docker_context(self, component_name: str) -> Path:
        """
        Returns the path to the docker-context directory of the component.

        Args:
            component_name: The name of the component.

        Returns:
            The path to the docker-context director of the component.
        """

        return self.get_resource_dir(component_name) / self._component_subdir() / "docker_context"

    def _component_subdir(self) -> str:
        if self._kerberos:
            return "kerberos"

        return "unsecure"
