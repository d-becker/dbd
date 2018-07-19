import shutil, tarfile

from pathlib import Path
from typing import Any, Dict, Tuple

import docker, wget

from utils import DistType
import utils

class ImageBuilder:
    def __init__(self,
                 client: docker.DockerClient,
                 repository: str,
                 timestamp: int,
                 dockerfile_dir_path: Path) -> None:
        self.client = client
        self.repository = repository
        self.timestamp = timestamp
        self.dockerfile_dir_path = dockerfile_dir_path

        if not self.dockerfile_dir_path.is_dir():
            raise ValueError("The provided Dockerfile directory path is not a directory.")

    def ensure_image_exists(self,
                            distType: DistType,
                            argument: str,
                            forceRebuild: bool = False):
        image_name = self._get_image_name(distType, argument)

        # TODO: possibly also check whether the image can be pulled.
        if (distType == DistType.RELEASE
            and not forceRebuild
            and utils.image_exists_locally(self.client, image_name)):
            print("Reusing local image {}.".format(image_name))
        else:
            self._create_tmp_directory()
            
            try:
                self._build_image(distType, argument)
            finally:
                self._cleanup_tmp_directory()

    def _get_image_name(self,
                       distType: DistType,
                       argument: str) -> str:
        if distType == DistType.RELEASE:
            version = argument
            return "{}/hadoop:{}".format(self.repository, version)
        elif distType == DistType.SNAPSHOT:
            return "{}/hadoop:snapshot_{}".format(self.repository, self.timestamp)
        else:
            raise RuntimeError("Unexpected value of DistType.")

    def _get_tmp_dir_path(self) -> Path:
        return self.dockerfile_dir_path / "tmp"
        
    def _create_tmp_directory(self) -> None:
       self._cleanup_tmp_directory()
       self._get_tmp_dir_path().mkdir()

    def _cleanup_tmp_directory(self) -> None:
        tmp_path = self._get_tmp_dir_path()

        if tmp_path.exists():
                shutil.rmtree(tmp_path)
        
    def _prepare_build_release_image(self,
                                     version: str):
        print("Downloading Hadoop release version {}.".format(version))

        url="https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz".format(version)
        out_path = self._get_tmp_dir_path() / "hadoop.tar.gz"
        wget.download(url, out=str(out_path))

        print()

    def _prepare_build_snapshot_image(self,
                                        path: Path):
        print("Preparing Hadoop snapshot version from path {}.".format(path))

        with tarfile.open(self._get_tmp_dir_path() / "hadoop.tar.gz", "w:gz") as tar:
            tar.add(str(path), arcname=path.name)

    def _build_with_docker(self, image_name: str) -> None:
        print("Building docker image {}.".format(image_name))
        self.client.images.build(path=str(self.dockerfile_dir_path), tag=image_name, rm=True)

    def _build_image(self,
                     distType: DistType,
                     argument: str):
        if distType == DistType.RELEASE:
            version = argument
            print("Preparing to build Hadoop release version {} docker image.".format(version))
            self._prepare_build_release_image(version)
        else:
            path = Path(argument).expanduser().resolve()
            print("Preparing to build Hadoop snapshot version docker image from path {}.".format(path))
            self._prepare_build_snapshot_image(path)

        image_name = self._get_image_name(distType, argument)
        self._build_with_docker(image_name)
