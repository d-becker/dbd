#!/usr/bin/env python3

"""
This module contains the ImageBuilder for Hadoop.
"""

import docker

import base_image_builder
import utils

class ImageBuilder(base_image_builder.BaseImageBuilder):
    """
    The ImageBuilder class for Hadoop.
    """

    def __init__(self) -> None:
        url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"

        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hadoop",
                                                     [],
                                                     url_template,
                                                     self._find_out_version_from_image_name)

    def _find_out_version_from_image_name(self, docker_client: docker.DockerClient, image_name: str) -> str:
        command = "hadoop version"
        regex = "\nHadoop (.*)\n"
        return utils.find_out_version_from_image(docker_client, image_name, self.name(), command, regex)
