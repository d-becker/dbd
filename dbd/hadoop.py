#!/usr/bin/env python3

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import default_cache_path_fragments, DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline_builder import DefaultPipelineBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"
    version_command = "hadoop version"
    version_regex = "\nHadoop (.*)\n"

    cache_paths = default_cache_path_fragments()
    cache = Cache(cache_dir, cache_paths)

    pipeline_builder = DefaultPipelineBuilder()

    return DefaultComponentImageBuilder("hadoop",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
