#!/usr/bin/env python3

"""
The main module of the application containing the entry point.
"""

import argparse
import importlib
import logging
import time

from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

import __main__

import graph
import output

from component_builder import ComponentImageBuilder, Configuration
import default_image_builder_module

def _get_argument_parser() -> argparse.ArgumentParser:
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

def _parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def _get_force_rebuild_components(args: argparse.Namespace, components: List[str]) -> List[str]:
    force_rebuild_components: List[str]

    if args.force is not None and len(args.force) == 0:
        force_rebuild_components = components
    elif args.force is None:
        force_rebuild_components = []
    else:
        force_rebuild_components = args.force

    return force_rebuild_components

def _get_components(conf: Dict[str, Any]) -> List[str]:
    return list(conf["components"].keys())

def _get_component_image_builders(components: List[str],
                                  assemblies: Dict[str, Dict[str, Any]],
                                  cache_dir: Path) -> Dict[str, ComponentImageBuilder]:
    image_builders: Dict[str, ComponentImageBuilder] = {}

    for component in components:
        assembly = assemblies[component]
        image_builder: ComponentImageBuilder

        try:
            module = importlib.import_module(component)
            image_builder = module.__dict__["get_image_builder"](assembly, cache_dir)
        except ModuleNotFoundError:
            image_builder = default_image_builder_module.get_image_builder(component, assembly, cache_dir)

        image_builders[component] = image_builder

    return image_builders

def _get_assembly_from_resource_files(resource_path: Path,
                                      components: List[str],
                                      filename: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for component in components:
        assembly_file = resource_path / component / filename
        with assembly_file.open() as file:
            text = file.read()
            assembly_dictionary = yaml.load(text)

            result[component] = assembly_dictionary

    return result

def _get_component_assemblies(resource_path: Path, components: List[str]) -> Dict[str, Dict[str, Any]]:
    return _get_assembly_from_resource_files(resource_path, components, "assembly.yaml")

def _get_initial_configuration(name: str) -> Configuration:
    timestamp: str = str(int(time.time()))
    repository: str = "dbd"
    resource_path: Path = Path(__main__.__file__).parent.resolve().parent / "resources"

    return Configuration(name, timestamp, repository, resource_path)

def _build_component_images(name: str,
                            components: List[str],
                            input_configuration: Dict[str, Dict[str, str]],
                            image_builders: Dict[str, ComponentImageBuilder],
                            force_rebuild: List[str]) -> Configuration:
    resulting_configuration = _get_initial_configuration(name)

    print("Building components in the following order: {}.".format(components))

    for component in components:
        component_conf = input_configuration[component]
        image_builder = image_builders[component]
        force_rebuild_component = component in force_rebuild
        component_config = image_builder.build(component_conf, resulting_configuration, force_rebuild_component)
        resulting_configuration.components[component] = component_config

    return resulting_configuration

def _get_dependencies_from_assemblies(assemblies: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    dependencies: Dict[str, List[str]] = {}

    for component, assembly in assemblies.items():
        component_dependencies = assembly.get("dependencies", [])

        if (not isinstance(component_dependencies, list)
                or not all(map(lambda x: isinstance(x, str), component_dependencies))):
            raise TypeError("The 'dependencies' key must be associated with a value of type `List[str]`.")

        dependencies[component] = component_dependencies

    return dependencies

def _dependencies_without_configuration(components: List[str],
                                        dependencies: Dict[str, List[str]]) -> Set[str]:
    components_set = set(components)

    dependencies_set: Set[str] = set()
    for dependency_list in dependencies.values():
        dependencies_set.update(dependency_list)

    return dependencies_set - components_set

def main() -> None:
    """
    The entry point to the application. Run on the command line with `--help` to get information on usage.
    """

    parser = _get_argument_parser()
    args = parser.parse_args()

    input_conf = _parse_yaml(args.config_file)
    name = input_conf["name"]
    components = _get_components(input_conf)

    configuration = _get_initial_configuration(name)

    assemblies = _get_component_assemblies(configuration.resource_path, components)
    dependencies = _get_dependencies_from_assemblies(assemblies)

    deps_without_config = _dependencies_without_configuration(components, dependencies)
    if len(deps_without_config) > 0:
        print("Error: the following components are not specified in the configuration but are needed as dependencies"
              "by other components: {}".format(str(list(deps_without_config))))
        return

    dag = graph.build_graph_from_dependencies(dependencies)
    topologically_sorted_components = dag.get_topologically_sorted_nodes()

    cache_dir = Path(__main__.__file__).parent.resolve().parent / "cache"
    image_builders = _get_component_image_builders(components, assemblies, cache_dir)

    force_rebuild_components = _get_force_rebuild_components(args, components)
    output_configuration = _build_component_images(name,
                                                   topologically_sorted_components,
                                                   input_conf["components"],
                                                   image_builders,
                                                   force_rebuild_components)

    output.generate_output(input_conf, output_configuration, Path(args.output_dir))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
