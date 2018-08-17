#!/usr/bin/env python3

"""
This module contains a class which can be used to query cache locations that depend on the component and configuration.
"""

from typing import Dict, Optional
from pathlib import Path

from component_builder import DistType

class Cache:
    """
    A class that can be used to query the filesystem locations where the output files
    of the different stages of the component image building process should be cached.
    """

    def __init__(self,
                 base_path: Path,
                 stage_name_paths: Optional[Dict[str, str]] = None) -> None:
        """
        Creates a new `Cache` object.

        Args:
            base_path: The path to the root cache directory.
            stage_name_paths: A dictionary which maps stage names to directory names (not full paths).
                For stage names that are not present in this dictionary, the stage name itself is used.
        """

        self._base_path = base_path.expanduser().resolve()
        self._stage_name_paths = stage_name_paths if stage_name_paths is not None else {}

        self._dist_type_paths = {DistType.RELEASE: "release", DistType.SNAPSHOT: "snapshot"}

    def get_path(self,
                 component_name: str,
                 stage_name: str,
                 dist_type: DistType,
                 id_string: str) -> Path:
        """
        Returns a full path to the cache location that matches the provided arguments.

        Args:
            component_name: The name of the component.
            stage_name: The name of the stage to which the path belongs.
            dist_type: The distribution type.
            id_string: A string that identifies the build configuration - for example for
                release builds, it could be the version number.
        """

        return (self._base_path
                / component_name
                / self._stage_name_paths.get(stage_name, stage_name) # The second argument is the default return value.
                / self._dist_type_paths[dist_type]
                / id_string
                / "{}.tar.gz".format(component_name))
