#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import Any, Dict
from pathlib import Path

from component_builder import Configuration, DistInfo, DistType
from default_component_image_builder.assembly import Assembly

from ...temp_dir_test_case import TmpDirTestCase

class PipelineBuilderTestCase(TmpDirTestCase):
    def get_default_arguments(self) -> Dict[str, Any]:
        return {
            "built_config" : Configuration("test_configuration_name", "0001", "test_repository", self._tmp_dir_path),
            "assembly" : Assembly.from_dict({"url": "some_url"}),
            "image_name" : "test_image",
            "dist_info" : DistInfo(DistType.SNAPSHOT, "path/to/snapshot_build"),
            "docker_context_dir" : Path("path/to/docker/context")
        }
