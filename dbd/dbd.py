#!/usr/bin/env python3

import argparse
import importlib
import time

from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

import __main__

import graph
import output

from component_builder import ComponentImageBuilder, Configuration

def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a directory which can be used by docker-compose " +
                                     "using the provided components, building the needed docker images.")
    parser.add_argument("config_file", help="the configuration file to be used")
    parser.add_argument("output_dir", default=".",
                        help="the directory in which the output directory will be created; " +
                        "this directory must already exist")
    parser.add_argument("-f", "--force", metavar="COMPONENT", nargs="*",
                        help="force rebuilding the images of the given COMPONENTs even if suitable " +
                        "images already exist; if specified without arguments, all images are rebuilt")

    return parser

def parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def get_force_rebuild_components(args: argparse.Namespace, components: List[str]) -> List[str]:
    force_rebuild_components: List[str]

    if args.force is not None and len(args.force) == 0:
        force_rebuild_components = components
    elif args.force is None:
        force_rebuild_components = []
    else:
        force_rebuild_components = args.force

    return force_rebuild_components

def get_components(conf: Dict[str, Any]) -> List[str]:
    return list(conf["components"].keys())

def get_component_image_builders(components: List[str]) -> Dict[str, ComponentImageBuilder]:
    modules = map(importlib.import_module, components)
    image_builders = map(lambda module: module.__dict__["ImageBuilder"](), modules)

    return dict(zip(components, image_builders))

def get_component_dependencies(image_builders: Dict[str, ComponentImageBuilder]) -> Dict[str, List[str]]:
    items = [(component_name, image_builders[component_name].dependencies())
             for component_name in image_builders.keys()]
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

def dependencies_without_configuration(components: List[str],
                                       dependencies: Dict[str, List[str]]) -> Set[str]:
    components_set = set(components)

    dependencies_set: Set[str] = set()
    for dependency_list in dependencies.values():
        dependencies_set.update(dependency_list)

    return dependencies_set - components_set

def main() -> None:
    parser = get_argument_parser()
    args = parser.parse_args()

    input_conf = parse_yaml(args.config_file)
    name = input_conf["name"]
    components = get_components(input_conf)

    force_rebuild_components = get_force_rebuild_components(args, components)

    image_builders = get_component_image_builders(components)

    dependencies = get_component_dependencies(image_builders)

    deps_without_config = dependencies_without_configuration(components, dependencies)
    if len(deps_without_config) > 0:
        print("Error: the following components are not specified in the configuration but are needed as dependencies"
              "by other components: {}".format(str(list(deps_without_config))))
        return

    dag = graph.build_graph_from_dependencies(dependencies)
    topologically_sorted_components = dag.get_topologically_sorted_nodes()

    output_configuration = build_component_images(name,
                                                  topologically_sorted_components,
                                                  input_conf["components"],
                                                  image_builders,
                                                  force_rebuild_components)

    output.generate_output(topologically_sorted_components, output_configuration, Path(args.output_dir))

if __name__ == "__main__":
    main()
