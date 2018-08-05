#!/usr/bin/env python3

import docker

import base_image_builder

class ImageBuilder(base_image_builder.BaseImageBuilder):
    def __init__(self) -> None:
        url_template = "http://xenia.sote.hu/ftp/mirrors/www.apache.org/hive/hive-{0}/apache-hive-{0}-bin.tar.gz"
        version_from_image_name = self._find_out_version_from_image

        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hive",
                                                     ["hadoop"],
                                                     url_template,
                                                     version_from_image_name)

    def _find_out_version_from_image(self, docker_client: docker.DockerClient, image_name: str) -> str:
        # TODO
        return "unimplemented_version_finding"
