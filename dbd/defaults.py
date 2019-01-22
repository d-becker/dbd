#!/usr/bin/env python3

"""
This module contains default configuration values.
"""

from pathlib import Path
import pkg_resources

import __main__

DOCKER_REPOSITORY: str = "dbd"

RESOURCE_PATH: Path = Path(pkg_resources.resource_filename("dbd.resources", ""))

CACHE_DIR: Path = Path(__main__.__file__).parent.resolve() / "cache"

CACHE_SIZE: int = 15

OUTPUT_DIR: str = "."

DOCKER_CONTEXT_GENERATED_DIR_NAME: str = "generated"

HBASE_COMMON_JAR_VERSION: str = "2.1.1"

KERBEROS_SERVICE_CONFIG: str = """
services:
    krb5:
        image: flokkr/krb5
#        ports:
#          - 8081:8081
"""
