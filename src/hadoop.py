import shutil, tarfile

from pathlib import Path
from typing import Any, Dict, List, Optional

import docker, wget

from component_builder import DistType, ComponentBuilder, ComponentConfig, Configuration
import utils

class ImageBuilder(ComponentBuilder):
    def __init__(self) -> None:
        self.docker_client: docker.DockerClient = docker.from_env()

    def name(self) -> str:
        return "hadoop"
    
    def dependencies(self) -> List[str]:
        return []

    def build(self, config: Configuration, force_rebuild: bool = False):
        component_config = config.components[self.name()]

        image_name = self._get_image_name(config)
        if (not force_rebuild
            and component_config.dist_type == DistType.RELEASE
            and utils.image_exists_locally(self.docker_client, image_name)):
            component_config.image_name = image_name
        else:
            tmp_dir = self._get_tmp_dir_path(config.resource_path)
            self._create_tmp_directory(tmp_dir)
            
            try:
                if component_config.dist_type == DistType.RELEASE:
                    version = component_config.version
                    self._prepare_tarfile_release(version, tmp_dir)
                elif component_config.dist_type == DistType.SNAPSHOT:
                    self._prepare_tarfile_snapshot(path, tmp_dir)
                else:
                    raise ValueError("Unexpected DistType value.")
            finally:
                self._cleanup_tmp_directory(tmp_dir)

    def _prepare_tarfile_release(self, version: str, tmp_dir: Path):
        url="https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz".format(version)
        print("Downloading Hadoop release version {} from {}.".format(version, url))

        out_path = tmp_dir / "hadoop.tar.gz"
        wget.download(url, out=str(out_path))

        print()

    def _prepare_tarfile_snapshot(self,
                                  path: Path,
                                  tmp_dir: Path):
        print("Preparing Hadoop snapshot version from path {}.".format(path))

        with tarfile.open(tmp_dir / "hadoop.tar.gz", "w:gz") as tar:
            tar.add(str(path), arcname=path.name)

    def _get_image_name(self, config: Configuration) -> str:
        component_config = config.components[self.name()]
        if component_config.dist_type == DistType.RELEASE:
            if component_config.version is None:
                raise ValueError("The version is None but release mode is specified.")
            return "{}/hadoop:{}".format(config.repository, component_config.version)
        elif component_config.dist_type == DistType.SNAPSHOT:
            return "{}/hadoop:snapshot_{}".format(config.repository, config.timestamp)
        else:
            raise RuntimeError("Unexpected value of DistType.")
            

    def _get_tmp_dir_path(self, resource_path) -> Path:
        return resource_path / self.name() / "tmp"
        
    def _create_tmp_directory(self, tmp_path: Path) -> None:
       self._cleanup_tmp_directory(tmp_path)
       tmp_path.mkdir()

    def _cleanup_tmp_directory(self, tmp_path: Path) -> None:
        if tmp_path.exists():
                shutil.rmtree(tmp_path)

    # def ensure_image_exists(self,
    #                         distType: DistType,
    #                         argument: str,
    #                         forceRebuild: bool = False) -> str:
    #     image_name = self._get_image_name(distType, argument)

    #     # TODO: possibly also check whether the image can be pulled.
    #     if (distType == DistType.RELEASE
    #         and not forceRebuild
    #         and utils.image_exists_locally(self.client, image_name)):
    #         print("Reusing local image {}.".format(image_name))
    #     else:
    #         self._create_tmp_directory()
            
    #         try:
    #             self._build_image(distType, argument)
    #         finally:
    #             self._cleanup_tmp_directory()
    #     return image_name

    # def _get_image_name(self,
    #                    distType: DistType,
    #                    argument: str) -> str:
    #     if distType == DistType.RELEASE:
    #         version = argument
    #         return "{}/hadoop:{}".format(self.repository, version)
    #     elif distType == DistType.SNAPSHOT:
    #         return "{}/hadoop:snapshot_{}".format(self.repository, self.timestamp)
    #     else:
    #         raise RuntimeError("Unexpected value of DistType.")

    # def _get_tmp_dir_path(self) -> Path:
    #     return self.dockerfile_dir_path / "tmp"
        
    # def _create_tmp_directory(self) -> None:
    #    self._cleanup_tmp_directory()
    #    self._get_tmp_dir_path().mkdir()

    # def _cleanup_tmp_directory(self) -> None:
    #     tmp_path = self._get_tmp_dir_path()

    #     if tmp_path.exists():
    #             shutil.rmtree(tmp_path)
        
    # def _prepare_build_release_image(self,
    #                                  version: str):
    #     print("Downloading Hadoop release version {}.".format(version))

    #     url="https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz".format(version)
    #     out_path = self._get_tmp_dir_path() / "hadoop.tar.gz"
    #     wget.download(url, out=str(out_path))

    #     print()

    # def _prepare_build_snapshot_image(self,
    #                                     path: Path):
    #     print("Preparing Hadoop snapshot version from path {}.".format(path))

    #     with tarfile.open(self._get_tmp_dir_path() / "hadoop.tar.gz", "w:gz") as tar:
    #         tar.add(str(path), arcname=path.name)

    # def _build_with_docker(self, image_name: str) -> None:
    #     print("Building docker image {}.".format(image_name))
    #     self.client.images.build(path=str(self.dockerfile_dir_path), tag=image_name, rm=True)

    # def _build_image(self,
    #                  distType: DistType,
    #                  argument: str):
    #     if distType == DistType.RELEASE:
    #         version = argument
    #         print("Preparing to build Hadoop release version {} docker image.".format(version))
    #         self._prepare_build_release_image(version)
    #     else:
    #         path = Path(argument).expanduser().resolve()
    #         print("Preparing to build Hadoop snapshot version docker image from path {}.".format(path))
    #         self._prepare_build_snapshot_image(path)

    #     image_name = self._get_image_name(distType, argument)
    #     self._build_with_docker(image_name)
