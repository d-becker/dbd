from abc import ABCMeta, abstractmethod
from enum import Enum, auto, unique
from pathlib import Path
from typing import Any, Dict, List, Optional

import __main__

@unique
class DistType(Enum):
    RELEASE = auto()
    SNAPSHOT = auto()

class ComponentConfig:
    def __init__(self,
                 dist_type: Optional[DistType] = None,
                 version: Optional[str] = None,
                 path: Optional[Path] = None,
                 image_name: Optional[str] = None) -> None:
        self.dist_type = dist_type
        self.version = version
        self.path = path
        self.image_name = image_name
    
class Configuration:
    def __init__(self,
                 timestamp: int,
                 repository: str = None,
                 resource_path: Path = None) -> None:
        self.timestamp = timestamp
        self.repository: str = "dbd" if repository is None else repository

        default_path = Path(__main__.__file__).parent.resolve().parent / "resources"
        self.resource_path: Path = default_path  if resource_path is None else resource_path
        self.components : Dict[str, ComponentConfig] = {}

class ComponentBuilder(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    def dependencies(self) -> List[str]: pass

    @abstractmethod
    def build(self, config: Configuration, force_rebuild: bool = False): pass
