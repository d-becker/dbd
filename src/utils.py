import shutil

from enum import Enum, auto, unique
from pathlib import Path
from typing import Dict, Tuple

import docker

from component_builder import DistType

def image_exists_locally(client: docker.DockerClient, image_name: str) -> bool:
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        return False
    else:
        return True

def dist_type_and_arg(component_config: Dict[str, str]) -> Tuple[DistType, str]:
        release_specified = "release" in component_config
        snapshot_specified = "snapshot" in component_config

        if release_specified and snapshot_specified:
            raise ValueError("Both release and snapshot mode specified.")

        if not release_specified and not snapshot_specified:
            raise ValueError("None of release and snapshot mode specified.")

        if release_specified:
            version = component_config["release"]
            return (DistType.RELEASE, version)
        else:
            path = component_config["snapshot"]
            return (DistType.SNAPSHOT, path)
    
class TmpDirHandler:
    def __init__(self, base_path: Path) -> None:
        if not base_path.is_dir():
            raise ValueError("The base directory path is not a directory.")
        
        self._base_path = base_path

    @property
    def base_path(self) -> Path:
        return self._base_path

    def get_tmp_dir_path(self) -> Path:
        return self.base_path / "tmp"

    def create_tmp_dir(self):
        self.remove_tmp_dir()
        self.get_tmp_dir_path().mkdir()

    def remove_tmp_dir(self):
        tmp_path = self.get_tmp_dir_path()
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    def __enter__(self) -> Path:
        self.create_tmp_dir()
        return self.get_tmp_dir_path()

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.remove_tmp_dir()
        return False
