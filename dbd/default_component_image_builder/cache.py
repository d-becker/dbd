#!/usr/bin/env python3

from typing import Dict
from pathlib import Path

from component_builder import DistType

class Cache:
    def __init__(self,
                 base_path: Path,
                 stages: Dict[str, Path]) -> None:
        self._base_path = base_path
        self._stages = stages
        self._dist_types = {DistType.RELEASE: "release", DistType.SNAPSHOT: "snapshot"}

    def get_path(self,
                 stage: str,
                 dist_type: DistType,
                 component_name: str,
                 id_string: str) -> Path:
        return self._base_path / component_name / self._stages[stage] / self._dist_types[dist_type] / id_string
