#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import cast, List
from pathlib import Path

from dbd.component_config import DistType
from dbd.default_component_image_builder.cache import Cache
from dbd.default_component_image_builder.pipeline import EntryStage, FinalStage, Pipeline, Stage
from dbd.default_component_image_builder.pipeline.executor import DefaultPipelineExecutor

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
    def __init__(self, postcondition_satisfied: bool) -> None:
        self.called = False
        self._postcondition_satisfied = postcondition_satisfied

    def name(self) -> str:
        return "test_final_stage"

    def execute(self, input_path: Path) -> None:
        self.called = True

    def postcondition_satisfied(self) -> bool:
        return self._postcondition_satisfied

class TestDefaultPipelineExecutor(TmpDirTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.component_name = "test_component"
        self.dist_type = DistType.SNAPSHOT
        self.id_string = "id_string"
        self.cache = Cache(self._tmp_dir_path)
        self.inner_stage_names = ["stage1", "stage2", "stage3"]

        path = self.cache.get_path(self.component_name,
                                   self.inner_stage_names[1],
                                   self.dist_type,
                                   self.id_string)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def _get_pipeline(self, final_stage_postcondition_satisfied: bool) -> Pipeline:
        inner_stages: List[Stage] = list(map(StageTest, self.inner_stage_names))

        return Pipeline(
            EntryStageTest(),
            inner_stages,
            FinalStageTest(final_stage_postcondition_satisfied))

    def test_execute_all(self) -> None:
        executor = DefaultPipelineExecutor()
        pipeline = self._get_pipeline(False)
        executor.execute_all(self.component_name,
                             self.dist_type,
                             self.id_string,
                             self.cache,
                             pipeline)

        self.assertTrue(cast(EntryStageTest, pipeline.entry_stage).called)

        self.assertTrue(
            all(
                map(lambda stage: cast(StageTest, stage).called,
                    pipeline.inner_stages)))

        self.assertTrue(cast(FinalStageTest, pipeline.final_stage).called)

    def test_execute_needed(self) -> None:
        executor = DefaultPipelineExecutor()
        pipeline = self._get_pipeline(False)
        executor.execute_needed(self.component_name,
                                self.dist_type,
                                self.id_string,
                                self.cache,
                                pipeline)

        self.assertFalse(cast(EntryStageTest, pipeline.entry_stage).called)

        self.assertFalse(
            any(
                map(lambda stage: cast(StageTest, stage).called,
                    pipeline.inner_stages[:2])))

        self.assertTrue(cast(StageTest, pipeline.inner_stages[2]).called)
        self.assertTrue(cast(FinalStageTest, pipeline.final_stage).called)

    def test_execute_needed_final_stage_postcondition_satisfied(self) -> None:
        executor = DefaultPipelineExecutor()
        pipeline = self._get_pipeline(True)
        executor.execute_needed(self.component_name,
                                self.dist_type,
                                self.id_string,
                                self.cache,
                                pipeline)

        self.assertFalse(cast(EntryStageTest, pipeline.entry_stage).called)

        self.assertFalse(
            any(
                map(lambda stage: cast(StageTest, stage).called,
                    pipeline.inner_stages)))

        self.assertFalse(cast(FinalStageTest, pipeline.final_stage).called)
