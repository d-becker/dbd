#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the Hadoop component.
"""

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline_builder import DefaultPipelineBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Hadoop docker images.

    Args:
        dependencies: The names of the components that this component depends on.
        cache_dir: The path to the global cache directory.
    """

    url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"
    version_command = "hadoop version"
    version_regex = "\nHadoop (.*)\n"

    cache = Cache(cache_dir)

    pipeline_builder = DefaultPipelineBuilder()

    return DefaultComponentImageBuilder("hadoop",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
