#!/usr/bin/env python3

"""
This module contains the ImageBuilder for Hadoop.
"""

import base_image_builder

class ImageBuilder(base_image_builder.BaseImageBuilder):
    """
    The ImageBuilder class for Hadoop.
    """

    def __init__(self) -> None:
        url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"

        version_command = "hadoop version"
        version_regex = "\nHadoop (.*)\n"

        base_image_builder.BaseImageBuilder.__init__(self,
                                                     "hadoop",
                                                     [],
                                                     url_template,
                                                     version_command,
                                                     version_regex)
