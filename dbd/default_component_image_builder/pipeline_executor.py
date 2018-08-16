#!/usr/bin/env python3

import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union

from component_builder import DistType
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import EntryStage, Pipeline, Stage

class PipelineExecutor:
    class _OutputExecutableWrapper:
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
        entry_stage = pipeline.entry_stage
        entry_output_path = cache.get_path(component_name, type(entry_stage), dist_type, id_string)

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
            stage_output_path = cache.get_path(component_name, type(stage), dist_type, id_string)
            if stage_output_path.exists():
                return (index + 1, stage_output_path)

        entry_stage_output_path = cache.get_path(component_name, type(pipeline.entry_stage), dist_type, id_string)
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
        for stage in pipeline.inner_stages[start_index:]:
            output_path = cache.get_path(component_name, type(stage), dist_type, id_string)

            PipelineExecutor._execute_output_stage_with_atomic_cache_entry(
                 PipelineExecutor._OutputExecutableWrapper(stage, input_path),
                output_path)
            
            stage.execute(input_path, output_path)
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
            
        
