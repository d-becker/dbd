import re, shutil, subprocess, tarfile

from pathlib import Path
from typing import Dict, List, Tuple

import docker, wget

from component_builder import ComponentConfig, Configuration, DistType
import utils

class ImageBuilder:
    def __init__(self) -> None:
        self.docker_client = docker.from_env()

    def name(self) -> str:
        return "oozie"

    def dependencies(self) -> List[str]:
        return ["hadoop"]

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        hadoop_config = built_config.components["hadoop"]
        hadoop_tag = hadoop_config.image_name.split(":")[-1]

        (dist_type, argument) = utils.dist_type_and_arg(component_config)
        image_name = self._get_image_name(dist_type, argument, hadoop_tag, built_config)

        reuse_existing_image = (not force_rebuild
                                and dist_type == DistType.RELEASE
                                and utils.image_exists_locally(self.docker_client, image_name))

        if reuse_existing_image:
            print("Reusing existing Hadoop image: {}.".format(image_name))
        else:
            with utils.TmpDirHandler(self._get_resource_dir(built_config.resource_path)) as tmp_dir:
                if dist_type == DistType.RELEASE:
                    release_version = argument
                    self._prepare_tarfile_release(release_version, hadoop_tag, hadoop_config.version, tmp_dir)
                elif dist_type == DistType.SNAPSHOT:
                    path = Path(argument)
                    self._prepare_tarfile_snapshot(path, hadoop_tag, tmp_dir)
                else:
                    raise ValueError("Unexpected DistType value.")

                self._build_docker_image(image_name, hadoop_tag, self._get_resource_dir(built_config.resource_path))

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            version = self._find_out_version_from_image(image_name)

        return ComponentConfig(dist_type, version, image_name)
        
        
    def _find_out_version_from_image(self, image_name: str) -> str:
        command = "bin/oozie version && exit 0" # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
        response_bytes = self.docker_client.containers.run(image_name, command, auto_remove=True)
        response = response_bytes.decode()

        match = re.search("version: (.*)\n", response)

        if match is None:
            raise ValueError("No Oozie version found.")

        version = match.group(1)
        return version

    def _get_image_name(self,
                        distType: DistType,
                        version_or_path: str,
                        hadoop_tag: str,
                        built_config: Configuration):
        oozie_part: str
        if distType == DistType.RELEASE:
            version = version_or_path
            oozie_part = version
        else:
            oozie_part = "snapshot_{}".format(built_config.timestamp)

        return "{}/oozie:{}_H{}".format(built_config.repository, oozie_part, hadoop_tag)


    def _prepare_tarfile_release(self,
                                 oozie_version: str,
                                 hadoop_tag: str,
                                 hadoop_version: str,
                                 tmp_path: Path):
        url = "https://archive.apache.org//dist/oozie/{0}/oozie-{0}.tar.gz".format(oozie_version)

        print("Downloading Oozie release version {} from URL {}.".format(oozie_version, url))        

        tmp_path = tmp_path.expanduser()
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

        print("Building the Oozie distribution against Hadoop version {}.".format(hadoop_version))
        subprocess.run(command, check=True)
        distro_file_path = oozie_dir / "distro/target/oozie-{}-distro.tar.gz".format(oozie_version)
        new_oozie_distro_path = tmp_path / "oozie.tar.gz"

        distro_file_path.rename(new_oozie_distro_path)

        shutil.rmtree(oozie_dir)

    def _prepare_tarfile_snapshot(self,
                                  path: Path,
                                  hadoop_tag: str,
                                  tmp_path: Path):
        print("Preparing Oozie snapshot version from path {}.".format(path))

        path = path.expanduser()
        tmp_path = tmp_path.expanduser()
        oozie_tar_file_path = tmp_path / "oozie.tar.gz"

        with tarfile.open(oozie_tar_file_path, "w:gz") as tar:
            tar.add(str(path), arcname=path.name)

    def _build_docker_image(self,
                            image_name: str,
                            hadoop_tag: str,
                            dockerfile_path: Path) -> None:
        print("Building docker image {}.".format(image_name))
        self.docker_client.images.build(path=str(dockerfile_path),
                                 tag=image_name,
                                 buildargs={"HADOOP_TAG": hadoop_tag},
                                 rm=True)

    def _get_resource_dir(self, global_resource_path: Path) -> Path:
        return global_resource_path / self.name()
