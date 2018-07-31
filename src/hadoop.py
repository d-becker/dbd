#!/usr/bin/env python3

import re

from typing import Any, Dict, List, Optional, Tuple

import docker

from component_builder import DistType, ComponentConfig, Configuration
import base_image_builder

class ImageBuilder(base_image_builder.BaseImageBuilder):
    def __init__(self) -> None:
        url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"
        version_from_image_name = self._find_out_version_from_image
        
        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hadoop",
                                                     [],
                                                     url_template,
                                                     version_from_image_name)

    def _find_out_version_from_image(self, docker_client: docker.DockerClient, image_name: str) -> str:
        command = "hadoop version && exit 0" # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
        response_bytes = docker_client.containers.run(image_name, command, auto_remove=True)
        response = response_bytes.decode()

        match = re.search("\nHadoop (.*)\n", response)

        if match is None:
            raise ValueError("No Hadoop version found.")

        version = match.group(1)
        return version
