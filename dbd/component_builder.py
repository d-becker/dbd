#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from enum import Enum, auto, unique
from pathlib import Path
from typing import Dict, List

import __main__

@unique
class DistType(Enum):
    RELEASE = auto()
    SNAPSHOT = auto()

class ComponentConfig:
    def __init__(self,
                 dist_type: DistType,
                 version: str,
                 image_name: str) -> None:
        self._dist_type = dist_type
        self._version = version
        self._image_name = image_name

    @property
    def dist_type(self) -> DistType:
        return self._dist_type

    @property
    def version(self) -> str:
        return self._version

    @property
    def image_name(self) -> str:
        return self._image_name

class Configuration:
    def __init__(self,
                 name: str,
                 timestamp: str,
                 repository: str = None,
                 resource_path: Path = None) -> None:
        self._name = name
        self._timestamp = timestamp
        self._repository: str = "dbd" if repository is None else repository

        default_path = Path(__main__.__file__).parent.resolve().parent / "resources"
        self._resource_path: Path = default_path  if resource_path is None else resource_path
        self.components: Dict[str, ComponentConfig] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def timestamp(self) -> str:
        return self._timestamp

    @property
    def repository(self) -> str:
        return self._repository

    @property
    def resource_path(self) -> Path:
        return self._resource_path

class ComponentImageBuilder(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def dependencies(self) -> List[str]:
        pass

    @abstractmethod
    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig: pass
