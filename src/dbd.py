#!/usr/bin/env python3

import argparse, importlib, os, re, shutil, sys, time, __main__

from pathlib import Path
from typing import Any, Dict, List

import docker, yaml

import graph, output
from component_builder import ComponentImageBuilder, Configuration, DistType

def parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def get_components(conf: Dict[str, Any]) -> List[str]:
    return list(conf["components"].keys())

def get_component_image_builders(components: List[str]) -> Dict[str, ComponentImageBuilder]:
    modules = map(importlib.import_module, components)
    image_builders = map(lambda module: module.__dict__["ImageBuilder"](), modules)

    return dict(zip(components, image_builders))

def get_component_dependencies(image_builders: Dict[str, ComponentImageBuilder]) -> Dict[str, List[str]]:
    items = [(component_name, image_builders[component_name].dependencies()) for component_name in image_builders.keys()]
    return dict(items)
    
def get_initial_configuration(name: str) -> Configuration:
    timestamp: str = str(int(time.time()))
    repository: str = "dbd"
    resource_path: Path = Path(__main__.__file__).parent.resolve().parent / "resources"

    return Configuration(name, timestamp, repository, resource_path)

def build_component_images(name: str,
                           components: List[str],
                           input_configuration: Dict[str, Dict[str, str]],
                           image_builders: Dict[str, ComponentImageBuilder],
                           force_rebuild: List[str]) -> Configuration:
    resulting_configuration = get_initial_configuration(name)

    print("Building components in the following order: {}.".format(components))

    for component in components:
        component_conf = input_configuration[component]
        image_builder = image_builders[component]
        force_rebuild_component = component in force_rebuild
        component_config = image_builder.build(component_conf, resulting_configuration, force_rebuild_component)
        resulting_configuration.components[component] = component_config

    return resulting_configuration

def main() -> None:
    parser = argparse.ArgumentParser(description="Create a directory which can be used by docker-compose " +
                                     "using the provided components, building the needed docker images.")
    parser.add_argument("config_file", help="the configuration file to be used")
    parser.add_argument("output_dir", default=".",
                        help="the directory in which the output directory will be created; " +
                        "this directory must already exist")
    parser.add_argument("-f", "--force", metavar="COMPONENT", nargs="*", default=[],
                        help="force rebuilding the images of the given COMPONENTs even if suitable " +
                        "images already exist; if specified without arguments, all images are rebuilt")

    args = parser.parse_args()
    
    input_conf = parse_yaml(args.config_file)

    name = input_conf["name"]
    components = get_components(input_conf)
    force_rebuild_components = args.force if len(args.force) > 0 else components

    image_builders = get_component_image_builders(components)

    dependencies = get_component_dependencies(image_builders)

    dag = graph.build_graph_from_dependencies(dependencies)
    topologically_sorted_components = dag.get_topologically_sorted_nodes()

    output_configuration = build_component_images(name,
                                                  topologically_sorted_components,
                                                  input_conf["components"],
                                                  image_builders,
                                                  force_rebuild_components)

    output.generate_output(output_configuration, Path(args.output_dir))

if __name__ == "__main__":
    main()
        
