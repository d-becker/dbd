#!/usr/bin/env python3

import re

import docker

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

    @staticmethod
    def _find_out_version_from_image(docker_client: docker.DockerClient, image_name: str) -> str:
        # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
        command = "hadoop version && exit 0"
        response_bytes = docker_client.containers.run(image_name, command, auto_remove=True)
        response = response_bytes.decode()

        match = re.search("\nHadoop (.*)\n", response)

        if match is None:
            raise ValueError("No Hadoop version found.")

        version = match.group(1)
        return version
