#!/usr/bin/env python3

"""
This module contains the pipeline executor.
"""

import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union

from component_builder import DistType
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import EntryStage, Pipeline, Stage

class PipelineExecutor:
    """
    Executes a pipeline, making the output of a stage become the input of the next stage at runtime.

    Intermediate results are cached.

    An attempt is made at writing the cache files atomically - the output of the stages is first
    written to a temporary file which is then renamed to the cached file.

    For more information, see the package level documentation.

    """

    class _OutputExecutableWrapper:
        # pylint: disable=missing-docstring
        def __init__(self,
                     stage: Stage,
                     input_path: Path) -> None:
            self._stage = stage
            self._input_path = input_path

        def execute(self, output_path: Path) -> None:
            self._stage.execute(self._input_path, output_path)

    def execute_all(self,
                    component_name: str,
                    dist_type: DistType,
                    id_string: str,
                    cache: Cache,
                    pipeline: Pipeline) -> None:
        """
        Executes all stages of the provided pipeline, regardless of whether there are cached intermediate results.
        Produced intermediate results are still written to the cache.

        Args:
            component_name: The name of the component that the pipeline builds the image for.
            dist_type: The distribution type of the component (release or snapshot).
            id_string: A string that identifies the build configuration - for example for
                release builds, it could be the version number.
            cache: The cache path locator to use to get the appropriate cache directories.
            pipeline: The pipeline to execute.
        """

        entry_stage = pipeline.entry_stage
        entry_output_path = cache.get_path(component_name, entry_stage.name(), dist_type, id_string)

        PipelineExecutor._execute_output_stage_with_atomic_cache_entry(entry_stage, entry_output_path)

        inner_stages_input_path = entry_output_path
        PipelineExecutor._execute_from(component_name,
                                       dist_type,
                                       id_string,
                                       cache,
                                       pipeline,
                                       inner_stages_input_path,
                                       0)

    def execute_needed(self,
                       component_name: str,
                       dist_type: DistType,
                       id_string: str,
                       cache: Cache,
                       pipeline: Pipeline) -> None:
        """
        Executes the pipeline from the latest stage the input of which is cached. The arguments are the same as for the
        `execute_all` method.

        """

        first_needed_stage_index_and_input_path = self._get_first_needed_stage_index_and_input_path(
            component_name,
            dist_type,
            id_string,
            cache,
            pipeline)

        if first_needed_stage_index_and_input_path is None:
            self.execute_all(component_name, dist_type, id_string, cache, pipeline)
        else:
            index, input_path = first_needed_stage_index_and_input_path
            PipelineExecutor._execute_from(component_name,
                                           dist_type,
                                           id_string,
                                           cache,
                                           pipeline,
                                           input_path,
                                           index)

    @staticmethod
    def _get_first_needed_stage_index_and_input_path(component_name: str,
                                                     dist_type: DistType,
                                                     id_string: str,
                                                     cache: Cache,
                                                     pipeline: Pipeline) -> Optional[Tuple[int, Path]]:
        for index, stage in reversed(list(enumerate(pipeline.inner_stages))):
            stage_output_path = cache.get_path(component_name, stage.name(), dist_type, id_string)
            if stage_output_path.exists():
                return (index + 1, stage_output_path)

        entry_stage_output_path = cache.get_path(component_name, pipeline.entry_stage.name(), dist_type, id_string)
        if entry_stage_output_path.exists():
            return (0, entry_stage_output_path)

        return None

    @staticmethod
    def _execute_from(component_name: str,
                      dist_type: DistType,
                      id_string: str,
                      cache: Cache,
                      pipeline: Pipeline,
                      input_path: Path,
                      start_index: int) -> None:
        print("Stages: {}.".format(pipeline.inner_stages))
        for stage in pipeline.inner_stages[start_index:]:
            output_path = cache.get_path(component_name, stage.name(), dist_type, id_string)

            PipelineExecutor._execute_output_stage_with_atomic_cache_entry(
                PipelineExecutor._OutputExecutableWrapper(stage, input_path),
                output_path)

            input_path = output_path

        pipeline.final_stage.execute(input_path)


    @staticmethod
    def _execute_output_stage_with_atomic_cache_entry(stage: Union[EntryStage, _OutputExecutableWrapper],
                                                      output_path: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            tmp_file_path = tmp_dir / "temp_file"

            stage.execute(tmp_file_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_file_path.rename(output_path)
