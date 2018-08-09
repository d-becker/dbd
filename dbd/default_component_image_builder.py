#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path

import docker

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration
from stage import Stage, StageExecutor

class CreateCacheStage(Stage):
    def __init__(self, parent_dir: Path) -> None:
        self._parent_dir = parent_dir.expanduser().resolve()
        self._cache_dir = self._parent_dir / "cache"

    def name(self) -> str:
        return "create_cache"

    def check_precondition(self) -> bool:
        return self._parent_dir.is_dir()

    def execute(self) -> None:
        self._cache_dir.mkdir(exist_ok=True)

class StageListBuilder(metaclass=ABCMeta):
    @abstractmethod
    def build_stage_list(self,
                         component_config: Dict[str, str],
                         built_config: Configuration) -> List[Stage]:
        pass

class DefaultComponentImageBuilder(ComponentImageBuilder):
    def __init__(self,
                 component_name: str,
                 dependencies: List[str],
                 stage_list_builder: StageListBuilder,
                 url_template: str,
                 version_command: str,
                 version_regex: str) -> None:
        self._name = component_name
        self._dependencies = dependencies
        self._stage_list_builder = stage_list_builder
        self._url_template = url_template # A string with {0} which will be formatted with the version.
        self._version_command = version_command
        self._version_regex = version_regex

        self._docker_client = docker.from_env()

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List[str]:
        return self._dependencies

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        stages = self._stage_list_builder.build_stage_list(component_config, built_config)
        stage_executor = StageExecutor(stages)

        if force_rebuild:
            stage_executor.execute_in_order()
        else:
            stage_executor.execute_needed()
