#!/usr/bin/env python3

"""
This module contains an interface for classes that build docker
images for the components as well as classes that it depends on.

"""

from abc import ABCMeta, abstractmethod
from enum import Enum, auto, unique
from pathlib import Path
from typing import Dict, List, Optional

import __main__

@unique
class DistType(Enum):
    """
    An enum to store the distribution types, i.e. release or snapshot.
    """

    RELEASE = auto()
    SNAPSHOT = auto()

class DistInfo:
    """
    A class storing information about the user-provided configuration of the component distribution - its distribution
    type (release or snapshot) and an additional string, `argument`, which in case of release distributions is the
    version number, and in case of snapshot builds, the path to the distribution on the local file system.

    """

    def __init__(self, dist_type: DistType, argument: str) -> None:
        """
        Creates a new `DistInfo` object.

        Args:
            dist_type: The type of the distribution (release or snapshot).
            argument: For release distributions the version number, for snapshot
                builds the path to the distribution on the local file system.
        """

        self._dist_type = dist_type
        self._argument = argument

    @property
    def dist_type(self) -> DistType:
        """
        Returns the distribution type.
        """

        return self._dist_type

    @property
    def argument(self) -> str:
        """
        Returns the argument.
        """

        return self._argument

class ComponentConfig:
    """
    A class that contains information about a built docker image with a component.
    """

    def __init__(self,
                 dist_type: DistType,
                 version: str,
                 image_name: str) -> None:
        """
        Creates a new `ComponentConfig` object.

        Args:
            dist_type: The type of the distribution (release or snapshot).
            version: The version number of the component in the image. It should be provided
                irrespective of whether this is a release or a snapshot distribution.
            image_name: The name of the docker image that was built with the component.

        """

        self._dist_type = dist_type
        self._version = version
        self._image_name = image_name

    @property
    def dist_type(self) -> DistType:
        """
        The type of the distribution, i.e. release or snapshot.
        """

        return self._dist_type

    @property
    def version(self) -> str:
        """
        The version of the component in the docker image.
        """

        return self._version

    @property
    def image_name(self) -> str:
        """
        The name of the docker image that was built.
        """

        return self._image_name

class Configuration:
    """
    A class that holds information about the overall build and on all components and images.
    """

    def __init__(self,
                 name: str,
                 timestamp: str,
                 repository: Optional[str] = None,
                 resource_path: Optional[Path] = None) -> None:
        """
        Creates a new `Configuration` object.

        Args:
            name: The name of the BuildConfiguration (provided by the user).
            timestamp: The timestamp of the build.
            repository: The dockerhub repository to use when naming the images. Defaults to "dbd".
            resource_path: The path to the directory where the resources of the components are stored.

        """

        self._name = name
        self._timestamp = timestamp
        self._repository: str = "dbd" if repository is None else repository

        default_path = Path(__main__.__file__).parent.resolve().parent / "resources"
        self._resource_path: Path = default_path  if resource_path is None else resource_path
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

    @property
    def resource_path(self) -> Path:
        """
        The file system path to the resource files.
        """

        return self._resource_path

class ComponentImageBuilder(metaclass=ABCMeta):
    """
    An interface for classes that build docker images for individual components.

    Each component should have a module with the name of the component which
    contains a class called ImageBuilder implementing this interface.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the component for which the image is built.
        """
        pass

    @abstractmethod
    def dependencies(self) -> List[str]:
        """
        Returns the dependencies of the component for which the image is built. The dependencies are other
        components for which the image needs to be built before building the image for this component.
        """
        pass

    @abstractmethod
    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        """
        Builds the image for this component and returns a `ComponentConfig` object
        containing information about the component and the built image.

        Args:
            component_config: A dictionary that contains (usually user-provided)
                configuration information about the component.
            built_config: A `Configuration` object that contains information about
                previously built components and images. This should never be modified.
            force_rebuild: Rebuild the image even if the requested image already exists.

        Returns:
            A `ComponentConfig` object containing information about the component and the built image.

        """
        pass
