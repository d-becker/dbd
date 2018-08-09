#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from pathlib import Path

import tarfile

from typing import Dict, List, Optional

import docker

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration
from stage import Stage, StageChain

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

class CreateTarfileStage(Stage):
    def __init__(self, source_dir: Path, dest_path: Path) -> None:
        self._source_dir = source_dir.expanduser().resolve()
        self._dest_path = dest_path.expanduser().resolve()

    def name(self) -> str:
        return "create_tarfile"

    def check_precondition(self) -> bool:
        return self._source_dir.is_dir() and self._dest_path.parent.is_dir()

    def execute(self) -> None:
        with tarfile.open(self._dest_path, "w:gz") as tar:
            tar.add(str(self._source_dir), arcname=self._source_dir.name)

class Downloader(metaclass=ABCMeta):
    @abstractmethod
    def download(self, url: str, dest_path: Path) -> None:
        pass
            
class DownloadFileStage(Stage):
    def __init__(self, downloader: Downloader, url: str, dest_path: Path) -> None:
        self._downloader = downloader
        self._url = url
        self._dest_path = dest_path.expanduser().resolve()

    def name(self) -> str:
        return "download_file"

    def check_precondition(self) -> bool:
        return self._dest_path.parent.is_dir()

    def execute(self) -> None:
        self._downloader.download(self._url, self._dest_path)

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
        stage_executor = StageChain(stages)

        if force_rebuild:
            stage_executor.execute_in_order()
        else:
            stage_executor.execute_needed()
