#!/usr/bin/env python3

"""
This module contains pipeline stages needed by the `DefaultComponentImageBuilder` class.
"""

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path

import shutil
import tarfile
import tempfile
import urllib.request

from typing import Dict, Iterable

import docker

from default_component_image_builder.pipeline import EntryStage, FinalStage

class CreateTarfileStage(EntryStage):
    """
    An entry stage that creates a tar archive of a directory.
    """

    def __init__(self,
                 name: str,
                 src_dir: Path) -> None:
        """
        Creates a new `CreateTarfileStage` object.

        Args:
            name: The name of the stage.
            src_dir: The directory of which the archive will be created.
        """

        self._name = name
        self._src_dir = src_dir.expanduser().resolve()

    def name(self) -> str:
        return self._name

    def execute(self, output_path: Path) -> None:
        logging.info("Stage %s: creating tar archive from %s.",
                     self.name(),
                     self._src_dir)

        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(str(self._src_dir), arcname=self._src_dir.name)

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

class DefaultDownloader(Downloader):
    """
    The default implementation of the `Downloader` interface.
    """

    def download(self, url: str, dest_path: Path) -> None:
        with urllib.request.urlopen(url) as response, dest_path.open(mode="wb") as outfile:
            chunk_length = 250
            chunk = response.read(chunk_length)

            while len(chunk) > 0:
                outfile.write(chunk)
                chunk = response.read(chunk_length)

class DownloadFileStage(EntryStage):
    """
    An entry stage that downloads a file.
    """

    def __init__(self,
                 name: str,
                 downloader: Downloader,
                 url: str) -> None:
        """
        Creates a new `DownloadFileStage` object.

        Args:
            name: The name of the stage.
            downloader: The `Downloader` object to use to download the file.
            url: The url from which to download the file.

        """

        self._name = name
        self._downloader = downloader
        self._url = url

    def name(self) -> str:
        return self._name

    def execute(self, output_path: Path) -> None:
        logging.info("Stage %s: downloading file from %s.",
                     self.name(),
                     self._url)

        self._downloader.download(self._url, output_path)
        print() # Printing a newline is needed because the wget downloader output does not end with one.

class BuildDockerImageStage(FinalStage):
    """
    A final stage that builds a docker image.
    """

    def __init__(self,
                 name: str,
                 docker_client: docker.DockerClient,
                 image_name: str,
                 dependency_images: Dict[str, str],
                 build_context: Path) -> None:
        """
        Creates a new `BuildDockerImageStage` object.

        Args:
            name: The name of the stage.
            docker_client: The docker client to use to build the docker image.
            image_name: The name of the docker image that will be built.
            dependency_images: A dictionary where the keys are the dependencies of the
                component for which the docker image is built, and the values are the
                names of the already built docker images of those components.
            build_context: The path to the static (non-generated) resources that need
                to be present in the docker build directory when the image is built.
        """

        self._name = name
        self._docker_client = docker_client
        self._image_name = image_name
        self._dependency_images = dependency_images
        self._build_context = build_context.expanduser().resolve()

    def name(self) -> str:
        return self._name

    def execute(self, input_path: Path) -> None:
        logging.info("Stage %s: building docker image %s.", self.name(), self._image_name)

        buildargs = {"{}_IMAGE".format(component.upper()) : image
                     for (component, image) in self._dependency_images.items()}
        generated_dir_name = "generated"
        buildargs["GENERATED_DIR"] = generated_dir_name

        with tempfile.TemporaryDirectory() as tmp:
            tmp_context = Path(tmp)

            BuildDockerImageStage._copy_all(self._build_context.iterdir(), tmp_context)

            generated_dir_path = tmp_context / generated_dir_name
            generated_dir_path.mkdir()
            BuildDockerImageStage._copy_tree_or_file(input_path, generated_dir_path)

            self._docker_client.images.build(path=str(tmp_context),
                                             buildargs=buildargs,
                                             tag=self._image_name,
                                             rm=True)

    @staticmethod
    def _copy_all(items: Iterable[Path], dst: Path) -> None:
        for item in items:
            BuildDockerImageStage._copy_tree_or_file(item, dst)

    @staticmethod
    def _copy_tree_or_file(item: Path, dst: Path) -> None:
        if item.is_dir():
            shutil.copytree(item, dst / item.name)
        else:
            shutil.copy(item, dst)
