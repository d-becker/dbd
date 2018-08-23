#!/usr/bin/env python3

"""
This module contains the function that creates `ComponentImageBuilder`s for the Hadoop component.
"""

from typing import Any, Dict
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.assembly import Assembly
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

def get_image_builder(assembly: Dict[str, Any], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    """
    Returns a `ComponentImageBuilder` object that can build Hadoop docker images.

    Args:
        assembly: An object containing component-specific information such as dependencies.
        cache_dir: The path to the global cache directory.
    """

    assembly_object = Assembly.from_dict(assembly)
    cache = Cache(cache_dir)
    pipeline_builder = DefaultPipelineBuilder()

    return DefaultComponentImageBuilder("hadoop",
                                        assembly_object,
                                        cache,
                                        pipeline_builder)
