#!/usr/bin/env python3

from component_builder import DistType
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline import Pipeline

class PipelineExecutor:
    def execute_all(self,
                    component_name: str,
                    dist_type: DistType,
                    id_string: str,
                    cache: Cache,
                    pipeline: Pipeline) -> None:
        entry_stage = pipeline.entry_stage
        entry_output_path = cache.get_path(component_name, type(entry_stage), dist_type, id_string)
        entry_output_path.parent.mkdir(parents=True, exist_ok=True)

        entry_stage.execute(entry_output_path)

        input_path = entry_output_path

        for stage in pipeline.inner_stages:
            output_path = cache.get_path(component_name, type(stage), dist_type, id_string)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            stage.execute(input_path, output_path)
            input_path = output_path

        final_stage = pipeline.final_stage
        final_stage.execute(input_path)
