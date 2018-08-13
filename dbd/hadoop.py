#!/usr/bin/env python3

from typing import List
from pathlib import Path

import component_builder
from default_component_image_builder.builder import DefaultComponentImageBuilder
from default_component_image_builder.cache import Cache
from default_component_image_builder.stage_list_builder import DefaultStageListBuilder

def get_image_builder(dependencies: List[str], cache_dir: Path) -> component_builder.ComponentImageBuilder:
    url_template = "https://www-eu.apache.org/dist/hadoop/common/hadoop-{0}/hadoop-{0}.tar.gz"
    version_command = "hadoop version"
    version_regex = "\nHadoop (.*)\n"

    cache = Cache(cache_dir,
                  {"archive" : Path("archive")})

    stage_list_builder = DefaultStageListBuilder()

    return DefaultComponentImageBuilder("hadoop",
                                        dependencies,
                                        url_template,
                                        version_command,
                                        version_regex,
                                        cache,
                                        stage_list_builder)
