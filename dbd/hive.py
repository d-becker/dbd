#!/usr/bin/env python3

import docker

import base_image_builder
import utils

class ImageBuilder(base_image_builder.BaseImageBuilder):
    def __init__(self) -> None:
        url_template = "http://xenia.sote.hu/ftp/mirrors/www.apache.org/hive/hive-{0}/apache-hive-{0}-bin.tar.gz"

        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hive",
                                                     ["hadoop"],
                                                     url_template,
                                                     self.version_from_image_name)

    def version_from_image_name(self, docker_client: docker.DockerClient, image_name: str) -> str:
        command = "hive --version"
        regex = "Hive (.*)\n"
        return utils.find_out_version_from_image(docker_client, image_name, self.name(), command, regex)
