#!/usr/bin/env python3

"""
This module contains the ImageBuilder for Hive.
"""

import base_image_builder

class ImageBuilder(base_image_builder.BaseImageBuilder):
    """
    The ImageBuilder class for Hive.
    """

    def __init__(self) -> None:
        url_template = "http://xenia.sote.hu/ftp/mirrors/www.apache.org/hive/hive-{0}/apache-hive-{0}-bin.tar.gz"

        version_command = "hive --version"
        version_regex = "Hive (.*)\n"
        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hive",
                                                     ["hadoop"],
                                                     url_template,
                                                     version_command,
                                                     version_regex)
