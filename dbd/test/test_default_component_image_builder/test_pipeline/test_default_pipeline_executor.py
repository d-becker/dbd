#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import cast
from pathlib import Path

from component_builder import DistType
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import EntryStage, FinalStage, Pipeline, Stage
from default_component_image_builder.pipeline.executor import DefaultPipelineExecutor

from ...temp_dir_test_case import TmpDirTestCase

class EntryStageTest(EntryStage):
    def __init__(self) -> None:
        self.called = False

    def name(self) -> str:
        return "test_entry_stage"

    def execute(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        self.called = True

class StageTest(Stage):
    def __init__(self, name: str) -> None:
        self._name = name
        self.called = False

    def name(self) -> str:
        return self._name

    def execute(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        self.called = True

class FinalStageTest(FinalStage):
    def __init__(self) -> None:
        self.called = False

    def name(self) -> str:
        return "test_final_stage"

    def execute(self, input_path: Path) -> None:
        self.called = True

class TestDefaultPipelineExecutor(TmpDirTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.component_name = "test_component"
        self.dist_type = DistType.SNAPSHOT
        self.id_string = "id_string"
        self.cache = Cache(self._tmp_dir_path)
        self.pipeline = Pipeline(
            EntryStageTest(),
            [StageTest("stage1"), StageTest("test2"), StageTest("test3")],
            FinalStageTest())

        path = self.cache.get_path(self.component_name,
                                   self.pipeline.inner_stages[1].name(),
                                   self.dist_type,
                                   self.id_string)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def test_execute_all(self) -> None:
        executor = DefaultPipelineExecutor()
        executor.execute_all(self.component_name, self.dist_type, self.id_string, self.cache, self.pipeline)

        self.assertTrue(cast(EntryStageTest, self.pipeline.entry_stage).called)

        self.assertTrue(
            all(
                map(lambda stage: cast(StageTest, stage).called,
                    self.pipeline.inner_stages)))

        self.assertTrue(cast(FinalStageTest, self.pipeline.final_stage).called)

    def test_execute_needed(self) -> None:
        executor = DefaultPipelineExecutor()
        executor.execute_needed(self.component_name, self.dist_type, self.id_string, self.cache, self.pipeline)

        self.assertFalse(cast(EntryStageTest, self.pipeline.entry_stage).called)

        self.assertFalse(
            any(
                map(lambda stage: cast(StageTest, stage).called,
                    self.pipeline.inner_stages[:2])))

        self.assertTrue(cast(StageTest, self.pipeline.inner_stages[2]).called)
        self.assertTrue(cast(FinalStageTest, self.pipeline.final_stage).called)
