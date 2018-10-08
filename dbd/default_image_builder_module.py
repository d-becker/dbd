#!/usr/bin/env python3

"""
This module contains the function that creates `DefaultComponentImageBuilder`s for any component.
"""

from typing import Any, Dict

import dbd.component_builder
from dbd.default_component_image_builder.builder import DefaultComponentImageBuilder
from dbd.default_component_image_builder.assembly import Assembly
from dbd.default_component_image_builder.cache import Cache
from dbd.default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

def get_image_builder(component_name: str,
                      assembly: Dict[str, Any],
                      cache: Cache) -> dbd.component_builder.ComponentImageBuilder:
    """
    Returns a `DefaultComponentImageBuilder` object for the given component.

    Args:
        component_name: The name of the component.
        assembly: An object containing component-specific information such as dependencies.
        cache: The `Cache` object that handles the global cache.
    """

    assembly_object = Assembly.from_dict(assembly)
    pipeline_builder = DefaultPipelineBuilder()

    return DefaultComponentImageBuilder(component_name,
                                        assembly_object,
                                        cache,
                                        pipeline_builder)
