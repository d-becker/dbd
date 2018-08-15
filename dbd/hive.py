#!/usr/bin/env python3

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import default_cache_path_fragments, DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.pipeline_builder import DefaultPipelineBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    url_template = "http://xenia.sote.hu/ftp/mirrors/www.apache.org/hive/hive-{0}/apache-hive-{0}-bin.tar.gz"
    version_command = "hive --version"
    version_regex = "Hive (.*)\n"
    pipeline_builder = DefaultPipelineBuilder()

    cache_paths = default_cache_path_fragments()
    cache = Cache(cache_dir, cache_paths)

    return DefaultComponentImageBuilder("hive",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        pipeline_builder)
