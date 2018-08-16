#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import logging
from pathlib import Path

import shutil
import tarfile
import tempfile

from typing import Dict, Iterable

import docker
import wget

from default_component_image_builder.pipeline import EntryStage, FinalStage

class CreateTarfileStage(EntryStage):
    def __init__(self, src_dir: Path) -> None:
        self._src_dir = src_dir

    def name(self) -> str:
        return "create_tarfile"

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
    def download(self, url: str, dest_path: Path) -> None:
        wget.download(url, out=str(dest_path))

class DownloadFileStage(EntryStage):
    def __init__(self, downloader: Downloader, url: str) -> None:
        self._downloader = downloader
        self._url = url

    def name(self) -> str:
        return "download_file"

    def execute(self, output_path: Path) -> None:
        logging.info("Stage %s: downloading file from %s.",
                     self.name(),
                     self._url)

        self._downloader.download(self._url, output_path)
        print() # Printing a newline is needed because the wget downloader output does not end with one.

class BuildDockerImageStage(FinalStage):
    def __init__(self,
                 docker_client: docker.DockerClient,
                 image_name: str,
                 dependency_images: Dict[str, str],
                 build_context: Path) -> None:

        self._docker_client = docker_client
        self._image_name = image_name
        self._dependency_images = dependency_images
        self._build_context = build_context

    def name(self) -> str:
        return "build_docker_image"

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
            BuildDockerImageStage._copy_all([input_path], generated_dir_path) # TODO: Shutil.copy?

            self._docker_client.images.build(path=str(tmp_context),
                                             buildargs=buildargs,
                                             tag=self._image_name,
                                             rm=True)

    @staticmethod
    def _copy_all(items: Iterable[Path], dst: Path) -> None:
        for item in items:
            if item.is_dir():
                shutil.copytree(item, dst / item.name)
            else:
                shutil.copy(item, dst)
