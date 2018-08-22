#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the Spark component.
"""

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Spark docker images.

    Args:
        dependencies: The names of the components that this component depends on.
        cache_dir: The path to the global cache directory.
    """

    url_template = "https://archive.apache.org/dist/spark/spark-{0}/spark-{0}-bin-without-hadoop.tgz"
    version_command = "spark-shell --version"
    version_regex = "version (.*)\n"
    pipeline_builder = DefaultPipelineBuilder()

    cache = Cache(cache_dir)

    return DefaultComponentImageBuilder("spark",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
