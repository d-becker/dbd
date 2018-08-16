#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the Hive component.
"""

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline_builder import DefaultPipelineBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Hive docker images.

    Args:
        dependencies: The names of the components that this component depends on.
        cache_dir: The path to the global cache directory.
    """

    url_template = "http://xenia.sote.hu/ftp/mirrors/www.apache.org/hive/hive-{0}/apache-hive-{0}-bin.tar.gz"
    version_command = "hive --version"
    version_regex = "Hive (.*)\n"
    pipeline_builder = DefaultPipelineBuilder()

    cache = Cache(cache_dir)

    return DefaultComponentImageBuilder("hive",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
