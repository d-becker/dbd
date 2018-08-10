#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from pathlib import Path

import tarfile

from typing import Dict, List

import docker

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration
from stage import Stage, StageChain

class CreateCacheStage(Stage):
    """
    A stage that creates a cache directory.

    Its precondition is that the directory in which the cache directory should be created needs to exist.

    If the cache directory already exists, executing this stage does nothing.
    """

    def __init__(self, parent_dir: Path) -> None:
        """
        Creates a `CreateCacheStage` object.

        Args:
            parent_dir: The directory in which to create the cache directory.

        """

        self._parent_dir = parent_dir.expanduser().resolve()
        self._cache_dir = self._parent_dir / "cache"

    def name(self) -> str:
        return "create_cache"

    def check_precondition(self) -> bool:
        return self._parent_dir.is_dir()

    def execute(self) -> None:
        self._cache_dir.mkdir(exist_ok=True)

class CreateTarfileStage(Stage):
    """
    A stage that takes a directory and creates a tar archive from it.

    Its precondition is that the source and the destination directories must exist.

    If the target file already exists, it is overwritten.
    """

    def __init__(self, source_dir: Path, dest_path: Path) -> None:
        """
        Creates a `CreateTarfileStage` object.

        Args:
            source_dir: The directory that is to be archived.
            dest_path: The path of the archive file to be created.
        """

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
    """
    An interface for classes that can download files from url's.
    """

    @abstractmethod
    def download(self, url: str, dest_path: Path) -> None:
        """
        Downloads a the file pointed to by the url to the destination pointed by `dest_path`.

        Args:
            url: The url of the file to download.
            dest_path: The path to which the file is to be downloaded.

        """

        pass

class DownloadFileStage(Stage):
    """
    A stage that downloads a file from a url.

    Its precondition is that the destination directory needs to exist.

    If the target file already exists, it is overwritten.

    If the url is invalid or downloading the file fails, the stage fails, too.
    """

    def __init__(self, downloader: Downloader, url: str, dest_path: Path) -> None:
        """
        Creates a `DownloadFileStage` object.

        Args:
            downloader: A `Downloader` object that will be used to download the file.
            url: The url of the file to download.
            dest_path: The path to which the file is to be downloaded.

        """

        self._downloader = downloader
        self._url = url
        self._dest_path = dest_path.expanduser().resolve()

    def name(self) -> str:
        return "download_file"

    def check_precondition(self) -> bool:
        return self._dest_path.parent.is_dir()

    def execute(self) -> None:
        self._downloader.download(self._url, self._dest_path)

class BuildDockerImageStage(Stage):
    # TODO: Add precondition to the docstring.
    """
    A stage that builds a docker image.
    """

    def __init__(self,
                 docker_client: docker.DockerClient,
                 image_name: str,
                 dependency_images: Dict[str, str],
                 build_directory: Path,
                 file_dependencies: List[str]) -> None:
        self._docker_client = docker_client
        self._image_name = image_name
        self._dependency_images = dependency_images
        self._build_directory = build_directory
        self._file_dependencies = file_dependencies

    def name(self) -> str:
        return "build_docker_image"

    def check_precondition(self) -> bool:
        if not self._build_directory.is_dir():
            return False

        for dep_file in self._file_dependencies:
            if not (self._build_directory / dep_file).exists():
                return False

        return True

    def execute(self) -> None:
        buildargs = {"{}_IMAGE".format(component.upper()) : image
                     for (component, image) in self._dependency_images.items()}

        self._docker_client.images.build(path=str(self._build_directory),
                                         buildargs=buildargs,
                                         tag=self._image_name,
                                         rm=True)

class StageListBuilder(metaclass=ABCMeta):
    """
    An interface for classes that build lists of `Stage` objects according to the provided configuration.
    """

    @abstractmethod
    def build_stage_list(self,
                         component_config: Dict[str, str],
                         built_config: Configuration) -> List[Stage]:
        """
        Builds and returns a list of `Stage` objects according to the provided configration.

        Args:
            component_config: A dictionary that contains (usually user-provided)
                configuration information about the component.
            built_config: A `Configuration` object that contains information about
                previously built components and images. This should never be modified.

        """

        pass

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
