#!/usr/bin/env python3

from typing import Dict, Optional
from pathlib import Path

from component_builder import DistType

class Cache:
    def __init__(self,
                 base_path: Path,
                 stage_name_paths: Optional[Dict[str, str]] = None) -> None:
        self._base_path = base_path.expanduser().resolve()
        self._stage_name_paths = stage_name_paths if stage_name_paths is not None else {}

        self._dist_type_paths = {DistType.RELEASE: "release", DistType.SNAPSHOT: "snapshot"}

    def get_path(self,
                 component_name: str,
                 stage_name: str,
                 dist_type: DistType,
                 id_string: str) -> Path:
        return (self._base_path
                / component_name
                / self._stage_name_paths.get(stage_name, stage_name) # The second argument is the default return value.
                / self._dist_type_paths[dist_type]
                / id_string
                / "{}.tar.gz".format(component_name))
