import shutil, subprocess, tarfile

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
                            version_or_path: str,
                            hadoop_tag: str,
                            hadoop_version: str,
                            forceRebuild: bool = False):
        image_name = self._get_image_name(distType, version_or_path, hadoop_tag)

        # TODO: possibly also check whether the image can be pulled.
        if (distType == DistType.RELEASE
            and not forceRebuild
            and utils.image_exists_locally(self.client, image_name)):
            print("Reusing local image {}.".format(image_name))
        else:
            self._create_tmp_directory()
            
            try:
                self._build_image(distType, version_or_path, hadoop_tag, hadoop_version)
            finally:
                self._cleanup_tmp_directory()
        
        
    def _get_image_name(self,
                        distType: DistType,
                        version_or_path: str,
                        hadoop_tag: str):
        oozie_part: str
        if distType == DistType.RELEASE:
            version = version_or_path
            oozie_part = version
        else:
            oozie_part = "snapshot_{}".format(self.timestamp)

        return "{}/oozie:{}_H{}".format(self.repository, oozie_part, hadoop_tag)
            
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
                                     oozie_version: str,
                                     hadoop_tag: str,
                                     hadoop_version: str):
        print("Downloading Oozie release version {}.".format(oozie_version))
                
        url = "https://www-eu.apache.org/dist/oozie/{0}/oozie-{0}.tar.gz".format(oozie_version)
        tmp_path = self._get_tmp_dir_path()
        out_path = tmp_path / "oozie-src.tar.gz"
        wget.download(url, out=str(out_path))

        print()

        print("Extracting the downloaded oozie tar file.")
        with tarfile.open(out_path) as tar:
            tar.extractall(path=tmp_path)

        out_path.unlink()
        oozie_dirs = list(tmp_path.glob("oozie*"))

        if len(oozie_dirs) != 1:
            raise ValueError("There should be exactly one oozie* directory.")

        oozie_dir = oozie_dirs[0]
        script_file = oozie_dir / "bin" / "mkdistro.sh"
        command = [str(script_file), "-Puber", "-Phadoop.version={}".format(hadoop_version), "-DskipTests"]

        print("Building the Oozie distribution.")
        subprocess.run(command, check=True)
        distro_file_path = oozie_dir / "distro/target/oozie-{}-distro.tar.gz".format(oozie_version)
        new_oozie_distro_path = tmp_path / "oozie.tar.gz"

        distro_file_path.rename(new_oozie_distro_path)

        shutil.rmtree(oozie_dir)

       

    def _prepare_build_snapshot_image(self,
                                      path: Path,
                                      hadoop_tag: str):
        pass

    def _build_with_docker(self, image_name: str, hadoop_tag: str) -> None:
        print("Building docker image {}.".format(image_name))
        self.client.images.build(path=str(self.dockerfile_dir_path),
                                 tag=image_name,
                                 buildargs={"HADOOP_TAG": hadoop_tag},
                                 rm=True)

    def _build_image(self,
                     distType: DistType,
                     version_or_path: str,
                     hadoop_tag: str,
                     hadoop_version: str):
        if distType == DistType.RELEASE:
            version = version_or_path
            print("Preparing to build Oozie release version {} docker image.".format(version))
            self._prepare_build_release_image(version, hadoop_tag, hadoop_version)
        else:
            path = Path(version_or_path).expanduser().resolve()
            print("Preparing to build Oozie snapshot version docker image from path {}.".format(path))
            self._prepare_build_snapshot_image(path, hadoop_tag)

        image_name = self._get_image_name(distType, version_or_path, hadoop_tag)
        self._build_with_docker(image_name, hadoop_tag)
