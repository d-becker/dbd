#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import unittest

from dbd.configuration import Configuration
from dbd.component_config import ComponentConfig, DistType, DistInfo
from dbd.default_component_image_builder.assembly import Assembly
from dbd.default_component_image_builder.builder import DefaultComponentImageBuilder
from dbd.default_component_image_builder.cache import Cache
from dbd.default_component_image_builder.pipeline import EntryStage, FinalStage, Pipeline
from dbd.default_component_image_builder.pipeline.builder import PipelineBuilder
from dbd.default_component_image_builder.pipeline.executor import PipelineExecutor

class DummyEntryStage(EntryStage):
    def name(self) -> str:
        return "dummy_entry_stage"

    def execute(self, output_path: Path) -> None:
        pass

class DummyFinalStage(FinalStage):
    def __init__(self, postcondition_satisfied: bool) -> None:
        self._postcondition_satisfied = postcondition_satisfied

    def name(self) -> str:
        return "dummy_entry_stage"

    def execute(self, input_path: Path) -> None:
        pass

    def postcondition_satisfied(self) -> bool:
        return self._postcondition_satisfied

class MockPipelineBuilder(PipelineBuilder):
    def __init__(self, final_stage_postcondition_satisfied: bool) -> None:
        self._final_stage_postcondition_satisfied = final_stage_postcondition_satisfied

    def build_pipeline(self,
                       built_config: Configuration,
                       component_input_config: Dict[str, Any],
                       assembly: Assembly,
                       image_name: str,
                       dist_info: DistInfo,
                       docker_context_dir: Path) -> Pipeline:
        return Pipeline(DummyEntryStage(), [], DummyFinalStage(self._final_stage_postcondition_satisfied))

class MockPipelineExecutor(PipelineExecutor):
    def __init__(self) -> None:
        self.execute_all_called = 0
        self.execute_needed_called = 0

    def execute_all(self,
                    component_name: str,
                    dist_type: DistType,
                    id_string: str,
                    cache: Cache,
                    pipeline: Pipeline) -> None:
        self.execute_all_called += 1

    def execute_needed(self,
                       component_name: str,
                       dist_type: DistType,
                       id_string: str,
                       cache: Cache,
                       pipeline: Pipeline) -> None:
        self.execute_needed_called += 1

class TestDefaultComponentImageBuilder(unittest.TestCase):
    COMPONENT_NAME: str = "component_name"
    DEPENDENCIES: List[str] = ["d1", "d2"]

    @staticmethod
    def _get_builder(dependencies: bool,
                     final_stage_postcondition_satisfied: bool,
                     pipeline_executor: Optional[PipelineExecutor] = None)-> DefaultComponentImageBuilder:
        name = TestDefaultComponentImageBuilder.COMPONENT_NAME
        dependency_list = TestDefaultComponentImageBuilder.DEPENDENCIES if dependencies else []
        assembly = Assembly.from_dict({"dependencies": dependency_list})
        cache = Cache(Path())
        pipeline_builder = MockPipelineBuilder(final_stage_postcondition_satisfied)
        return DefaultComponentImageBuilder(name, assembly, cache, pipeline_builder, pipeline_executor)

    @staticmethod
    def _default_builder() -> DefaultComponentImageBuilder:
        return TestDefaultComponentImageBuilder._get_builder(True, False)

    @staticmethod
    def _get_builder_no_deps(final_stage_postcondition_satisfied: bool,
                             pipeline_executor: PipelineExecutor) -> DefaultComponentImageBuilder:
        return TestDefaultComponentImageBuilder._get_builder(False,
                                                             final_stage_postcondition_satisfied,
                                                             pipeline_executor)

    @staticmethod
    def _get_component_config_and_configuration() -> Tuple[Dict[str, Any], Configuration]:
        component_config = {"release": "1.0.0"}
        configuration = Configuration("configuration_name", "0001", "dbd", False, Path())

        return (component_config, configuration)

    def test_name(self) -> None:
        builder = TestDefaultComponentImageBuilder._default_builder()

        self.assertEqual(TestDefaultComponentImageBuilder.COMPONENT_NAME, builder.name())

    def test_dependencies(self) -> None:
        builder = TestDefaultComponentImageBuilder._default_builder()

        self.assertEqual(TestDefaultComponentImageBuilder.DEPENDENCIES, builder.dependencies())

    def test_build_no_force_rebuild(self) -> None:
        pipeline_executor = MockPipelineExecutor()
        builder = TestDefaultComponentImageBuilder._get_builder_no_deps(False, pipeline_executor)

        component_config, configuration = TestDefaultComponentImageBuilder._get_component_config_and_configuration()
        force_rebuild = False

        builder.build(component_config, configuration, force_rebuild)

        self.assertEqual(0, pipeline_executor.execute_all_called)
        self.assertEqual(1, pipeline_executor.execute_needed_called)

    def test_build_with_force_rebuild(self) -> None:
        pipeline_executor = MockPipelineExecutor()
        builder = TestDefaultComponentImageBuilder._get_builder_no_deps(False, pipeline_executor)

        component_config, configuration = TestDefaultComponentImageBuilder._get_component_config_and_configuration()
        force_rebuild = True

        builder.build(component_config, configuration, force_rebuild)

        self.assertEqual(1, pipeline_executor.execute_all_called)
        self.assertEqual(0, pipeline_executor.execute_needed_called)

    def test_reused_docker_image_false_forced(self) -> None:
        pipeline_executor = MockPipelineExecutor()
        builder = TestDefaultComponentImageBuilder._get_builder_no_deps(False, pipeline_executor)

        component_config, configuration = TestDefaultComponentImageBuilder._get_component_config_and_configuration()
        force_rebuild = True

        result: ComponentConfig = builder.build(component_config, configuration, force_rebuild)
        self.assertFalse(result.reused)

    def test_reused_docker_image_false_not_forced(self) -> None:
        pipeline_executor = MockPipelineExecutor()
        builder = TestDefaultComponentImageBuilder._get_builder_no_deps(False, pipeline_executor)

        component_config, configuration = TestDefaultComponentImageBuilder._get_component_config_and_configuration()
        force_rebuild = False

        result: ComponentConfig = builder.build(component_config, configuration, force_rebuild)
        self.assertFalse(result.reused)

    def test_reused_docker_image_true(self) -> None:
        pipeline_executor = MockPipelineExecutor()
        builder = TestDefaultComponentImageBuilder._get_builder_no_deps(True, pipeline_executor)

        component_config, configuration = TestDefaultComponentImageBuilder._get_component_config_and_configuration()
        force_rebuild = False

        result: ComponentConfig = builder.build(component_config, configuration, force_rebuild)
        self.assertTrue(result.reused)
