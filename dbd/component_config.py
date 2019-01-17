#!/usr/bin/env python3

"""
This module contains a class that contains information about a
built docker image with a component, as well as helper classes.
"""

from enum import Enum, auto, unique

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
                 image_name: str,
                 reused: bool) -> None:
        """
        Creates a new `ComponentConfig` object.

        Args:
            dist_type: The type of the distribution (release or snapshot).
            version: The version number of the component in the image. It should be provided
                irrespective of whether this is a release or a snapshot distribution.
            image_name: The name of the docker image that was built with the component.
            reused: `True` if the image already existed and is reused; `False` if it was generated.

        """

        self._dist_type = dist_type
        self._version = version
        self._image_name = image_name
        self._reused = reused

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

    @property
    def reused(self) -> bool:
        """
        `True` if the image already existed and is reused; `False` if it was generated.
        """

        return self._reused
