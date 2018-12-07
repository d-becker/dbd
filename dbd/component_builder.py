#!/usr/bin/env python3

"""
This module contains an interface for classes that build docker
images for the components as well as classes that it depends on.

"""

from abc import ABCMeta, abstractmethod
from typing import Dict, List

from dbd.configuration import Configuration
from dbd.component_config import ComponentConfig

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
