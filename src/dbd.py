#!/usr/bin/env python3

import importlib, os, re, shutil, sys, time, __main__

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
                           image_builders: Dict[str, ComponentImageBuilder]) -> Configuration:
    resulting_configuration = get_initial_configuration(name)

    print("Building components in the following order: {}.".format(components))

    for component in components:
        component_conf = input_configuration[component]
        image_builder = image_builders[component]
        component_config = image_builder.build(component_conf, resulting_configuration)
        resulting_configuration.components[component] = component_config

    return resulting_configuration

def main() -> None:
    filename = sys.argv[1]
    
    input_conf = parse_yaml(filename)

    name = input_conf["name"]
    components = get_components(input_conf)

    image_builders = get_component_image_builders(components)

    dependencies = get_component_dependencies(image_builders)

    dag = graph.build_graph_from_dependencies(dependencies)
    topologically_sorted_components = dag.get_topologically_sorted_nodes()

    output_configuration = build_component_images(name,
                                                  topologically_sorted_components,
                                                  input_conf["components"],
                                                  image_builders)

    output_dir: Path
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path(".")

    output.generate_output(output_configuration, output_dir)

if __name__ == "__main__":
    main()
        
