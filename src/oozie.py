#!/usr/bin/env python3

import re, shutil, subprocess, tarfile

from pathlib import Path
from typing import Dict, List, Tuple

import docker, wget

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration, DistType
import base_image_builder
import utils

class ImageBuilder(base_image_builder.BaseImageBuilder):
    def __init__(self) -> None:
        url_template = "https://archive.apache.org//dist/oozie/{0}/oozie-{0}.tar.gz"
        version_from_image_name = self._find_out_version_from_image

        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "oozie",
                                                     ["hadoop"],
                                                     url_template,
                                                     version_from_image_name)
        
    def _find_out_version_from_image(self, docker_client: docker.DockerClient, image_name: str) -> str:
        command = "bin/oozied.sh start && bin/oozie version && exit 0" # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
        response_bytes = docker_client.containers.run(image_name, command, auto_remove=True)
        response = response_bytes.decode()

        match = re.search("version: (.*)\n", response)

        if match is None:
            raise ValueError("No Oozie version found.")

        version = match.group(1)
        return version

    def _prepare_tarfile_release(self,
                                 oozie_version: str,
                                 tmp_path: Path,
                                 built_config: Configuration):
        base_image_builder.BaseImageBuilder._prepare_tarfile_release(self, oozie_version, tmp_path, built_config)
        
        out_path = tmp_path / "oozie.tar.gz"

        print("Extracting the downloaded oozie tar file.")
        with tarfile.open(out_path) as tar:
            tar.extractall(path=tmp_path)

        out_path.unlink()
        oozie_dirs = list(tmp_path.glob("oozie*"))

        if len(oozie_dirs) != 1:
            raise ValueError("There should be exactly one oozie* directory.")

        hadoop_version = built_config.components["hadoop"].version

        oozie_dir = oozie_dirs[0]
        script_file = oozie_dir / "bin" / "mkdistro.sh"
        command = [str(script_file),
                   "-Puber",
                   "-Ptez",
                   # "-Dhadoop.version={}".format(hadoop_version),
                   "-DskipTests"]

        # if oozie_version.split(".")[0] == "4":
        #     command.append("-Phadoop-{}".format(hadoop_version.split(".")[0]))

        ### TODO: Oozie cannot be built when specifying a Hadoop-3 version. ###

        print("Building the Oozie distribution against Hadoop version {}.".format(hadoop_version))
        print("Build command: {}.".format(" ".join(command)))
        
        subprocess.run(command, check=True)
        distro_file_path = oozie_dir / "distro/target/oozie-{}-distro.tar.gz".format(oozie_version)
        new_oozie_distro_path = tmp_path / "oozie.tar.gz"

        distro_file_path.rename(new_oozie_distro_path)

        shutil.rmtree(oozie_dir)
