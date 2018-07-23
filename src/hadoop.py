import re, shutil, tarfile

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        (dist_type, argument) = utils.dist_type_and_arg(component_config)
        image_name = self._get_image_name(dist_type,
                                          argument if dist_type == DistType.RELEASE else None,
                                          built_config)

        reuse_existing_image = (not force_rebuild
                                and dist_type == DistType.RELEASE
                                and utils.image_exists_locally(self.docker_client, image_name))

        if reuse_existing_image:
            print("Reusing existing Hadoop image: {}.".format(image_name))
        else:
            with utils.TmpDirHandler(self._get_resource_dir(built_config.resource_path)) as tmp_dir:
                if dist_type == DistType.RELEASE:
                    release_version = argument
                    self._prepare_tarfile_release(release_version, tmp_dir)
                elif dist_type == DistType.SNAPSHOT:
                    path = Path(argument)
                    self._prepare_tarfile_snapshot(path, tmp_dir)
                else:
                    raise ValueError("Unexpected DistType value.")

                self._build_docker_image(image_name, self._get_resource_dir(built_config.resource_path))

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            version = self._find_out_version_from_image(image_name)

        return ComponentConfig(dist_type, version, image_name)

    def _find_out_version_from_image(self, image_name: str) -> str:
        command = "hadoop version && exit 0" # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
        response_bytes = self.docker_client.containers.run(image_name, command, auto_remove=True)
        response = response_bytes.decode()

        match = re.search("\nHadoop (.*)\n", response)

        if match is None:
            raise ValueError("No Hadoop version found.")

        version = match.group(1)
        return version

    def _prepare_tarfile_release(self, version: str, tmp_dir: Path):
        url="https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz".format(version)
        print("Downloading Hadoop release version {} from {}.".format(version, url))

        out_path = tmp_dir / "hadoop.tar.gz"
        wget.download(url, out=str(out_path.expanduser()))

        print()

    def _prepare_tarfile_snapshot(self,
                                  path: Path,
                                  tmp_dir: Path):
        print("Preparing Hadoop snapshot version from path {}.".format(path))

        with tarfile.open(tmp_dir / "hadoop.tar.gz", "w:gz") as tar:
            tar.add(str(path.expanduser()), arcname=path.name)

    def _build_docker_image(self, image_name: str, dockerfile_path: Path) -> None:
        print("Building docker image {}.".format(image_name))
        self.docker_client.images.build(path=str(dockerfile_path), tag=image_name, rm=True)

    def _get_image_name(self,
                        dist_type: DistType,
                        version: Optional[str],
                        built_config: Configuration) -> str:
        if dist_type == DistType.RELEASE:
            if version is None:
                raise ValueError("The version is None but release mode is specified.")
            return "{}/hadoop:{}".format(built_config.repository, version)
        elif dist_type == DistType.SNAPSHOT:
            return "{}/hadoop:snapshot_{}".format(built_config.repository, built_config.timestamp)
        else:
            raise RuntimeError("Unexpected value of DistType.")
            
    def _get_resource_dir(self, global_resource_path: Path) -> Path:
        return global_resource_path / self.name()
