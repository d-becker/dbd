#!/usr/bin/env python3

import os, re, shutil, sys, time, __main__

from pathlib import Path
from typing import Any, Dict, Tuple

import docker, yaml

import hadoop, oozie
from utils import DistType

REPOSITORY: str = "dbd"

def parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def get_component_config(config: Dict[str, Any], component_key: str) -> Tuple[DistType, str]:
    component_dict: Dict[str, str] = config["components"][component_key]

    release = "release" in component_dict
    snapshot = "snapshot" in component_dict
    
    if release and snapshot:
        raise RuntimeError("Both release and snapshot mode specified.")

    if not release and not snapshot:
        raise RuntimeError("None of release and snapshot mode specified.")

    distType: DistType
    if release:
        distType = DistType.RELEASE
    else:
        distType = DistType.SNAPSHOT

    argument = component_dict["release"
                              if distType == DistType.RELEASE
                              else "snapshot"]
    return (distType, argument)

def determine_hadoop_version(client: docker.DockerClient, image_name: str) -> str:
    command = "hadoop version && exit 0" # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
    response_bytes = client.containers.run(image_name, command, auto_remove=True)
    response = response_bytes.decode()

    match = re.search("\nHadoop (.*)\n", response)

    if match is None:
        raise ValueError("No Hadoop version found.")

    version = match.group(1)
    return version
    
    
def main() -> None:
    filename = sys.argv[1]
    conf = parse_yaml(filename)

    timestamp: int = int(time.time())
    client = docker.from_env()

    (h_distType, h_argument) = get_component_config(conf, "hadoop")
        
    hadoop_resource_path = Path(__main__.__file__).parent.resolve().parent / "resources/hadoop"
    hadoop_image_builder = hadoop.ImageBuilder(client, REPOSITORY, timestamp, hadoop_resource_path)
    hadoop_image_name = hadoop_image_builder.ensure_image_exists(h_distType, h_argument)

    hadoop_tag = hadoop_image_name.split(":")[-1]
    hadoop_version: str
    if h_distType == DistType.RELEASE:
        hadoop_version = h_argument
    else:
        hadoop_version = determine_hadoop_version(client, hadoop_image_name)

    (oo_distType, oo_argument) = get_component_config(conf, "oozie")
    
    oozie_resource_path = Path(__main__.__file__).parent.resolve().parent / "resources/oozie"
    oozie_image_builder = oozie.ImageBuilder(client, REPOSITORY, timestamp, oozie_resource_path)
    oozie_image_builder.ensure_image_exists(oo_distType, oo_argument, hadoop_tag, hadoop_version)

main()
        
