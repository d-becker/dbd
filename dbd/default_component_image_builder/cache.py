#!/usr/bin/env python3

from typing import Dict, Type, Union
from pathlib import Path

from component_builder import DistType
from default_component_image_builder.pipeline import EntryStage, Stage

class Cache:
    OutputStageType = Type[Union[EntryStage, Stage]]
    def __init__(self,
                 base_path: Path,
                 stage_paths: Dict[OutputStageType, Path]) -> None:
        self._base_path = base_path.expanduser().resolve()
        self._stage_paths = stage_paths
        self._dist_type_paths = {DistType.RELEASE: "release", DistType.SNAPSHOT: "snapshot"}

    def get_path(self,
                 component_name: str,
                 stage_type: OutputStageType,
                 dist_type: DistType,
                 id_string: str) -> Path:
        return (self._base_path
                / component_name
                / self._stage_paths[stage_type]
                / self._dist_type_paths[dist_type]
                / id_string)
