#!/usr/bin/env python3

# pylint: disable=missing-docstring

from pathlib import Path

import unittest

from dbd.default_component_image_builder.assembly import Assembly
from dbd.default_component_image_builder.builder import DefaultComponentImageBuilder
from dbd.default_component_image_builder.cache import Cache
from dbd.default_component_image_builder.pipeline.builder import DefaultPipelineBuilder

class TestDefaultComponentImageBuilder(unittest.TestCase):
    @staticmethod
    def _default_builder() -> DefaultComponentImageBuilder:
        pass

    def test_name(self) -> None:
        name = "component_name"
        dependencies = ["d1", "d2"]
        assembly = Assembly.from_dict({"dependencies": dependencies})
        cache = Cache(Path())
        pipeline_builder = DefaultPipelineBuilder()
        builder = DefaultComponentImageBuilder(name, assembly, cache, pipeline_builder)

        self.assertEqual(name, builder.name())

    def test_dependencies(self) -> None:
        name = "component_name"
        dependencies = ["d1", "d2"]
        assembly = Assembly.from_dict({"dependencies": dependencies})
        cache = Cache(Path())
        pipeline_builder = DefaultPipelineBuilder()
        builder = DefaultComponentImageBuilder(name, assembly, cache, pipeline_builder)

        self.assertEqual(dependencies, builder.dependencies())
