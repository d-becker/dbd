#!/usr/bin/env python3

"""
This module contains the function that creates `DefaultComponentImageBuilder`s for any component.
"""

from typing import Any, Dict
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.assembly import Assembly
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

def get_image_builder(component_name: str,
                      assembly: Dict[str, Any],
                      cache_dir: Path) -> component_builder.ComponentImageBuilder:
    """
    Returns a `DefaultComponentImageBuilder` object for the given component.

    Args:
        component_name: The name of the component.
        assembly: An object containing component-specific information such as dependencies.
        cache_dir: The path to the global cache directory.
    """

    assembly_object = Assembly.from_dict(assembly)
    cache = Cache(cache_dir)
    pipeline_builder = DefaultPipelineBuilder()

    return DefaultComponentImageBuilder(component_name,
                                        assembly_object,
                                        cache,
                                        pipeline_builder)
