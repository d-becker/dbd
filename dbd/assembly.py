#!/usr/bin/env python3

from typing import List

class Assembly:
    def __init__(self,
                 dependencies: List[str],
                 url: str,
                 version_command: str,
                 version_regex: str) -> None:
        self.dependencies = dependencies
        self.url = url
        self.version_command = version_command
        self.version_regex = version_regex
