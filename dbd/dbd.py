#!/usr/bin/env python3

"""
The main module of the application containing the entry point.
"""

import argparse
import importlib
import logging
import time

from pathlib import Path

from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

import dbd.defaults
import dbd.docker_setup
import dbd.graph
import dbd.output

from dbd.component_builder import ComponentImageBuilder, Configuration
from dbd.default_component_image_builder.cache import Cache

import dbd.default_image_builder_module

def _get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a directory which can be used by docker-compose " +
                                     "using the provided components, building the needed docker images.")
    parser.add_argument("config_file", help="the configuration file to be used")
    parser.add_argument("output_dir", default=dbd.defaults.OUTPUT_DIR,
                        help="the directory in which the output directory will be created; " +
                        "this directory must already exist")
    parser.add_argument("-f", "--force", metavar="COMPONENT", nargs="*",
                        help="force rebuilding the images of the given COMPONENTs even if suitable " +
                        "images already exist; if specified without arguments, all images are rebuilt")
    parser.add_argument("-c", "--cache", metavar="CACHE_DIR", help="the directory used to cache the build stages")
    parser.add_argument("-s", "--cache_size", default=dbd.defaults.CACHE_SIZE,
                        help="the maximal number of (regular) files that are allowed to be in the cache")

    return parser

def _parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def _is_kerberos_enabled(input_conf: Dict[str, Any]) -> bool:
    return input_conf.get("kerberos", False)

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
                                  cache: Cache) -> Dict[str, ComponentImageBuilder]:
    image_builders: Dict[str, ComponentImageBuilder] = {}

    for component in components:
        assembly = assemblies[component]
        image_builder: ComponentImageBuilder

        try:
            module = importlib.import_module("dbd.{}".format(component))
            image_builder = module.__dict__["get_image_builder"](assembly, cache)
        except ModuleNotFoundError:
            image_builder = dbd.default_image_builder_module.get_image_builder(component, assembly, cache)

        image_builders[component] = image_builder

    return image_builders

def _get_assembly_from_resource_files(configuration: Configuration,
                                      components: List[str]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for component in components:
        assembly_file = configuration.get_assembly(component)
        with assembly_file.open() as file:
            text = file.read()
            assembly_dictionary = yaml.load(text)

            result[component] = assembly_dictionary

    return result

def _get_component_assemblies(configuration: Configuration, components: List[str]) -> Dict[str, Dict[str, Any]]:
    return _get_assembly_from_resource_files(configuration, components)

def _get_initial_configuration(input_conf: Dict[str, Any],
                               docker_repository: str,
                               resource_path: Path) -> Configuration:
    timestamp: str = str(int(time.time()))

    name = input_conf["name"]
    kerberos = _is_kerberos_enabled(input_conf)

    logging.info("Resource path: %s.", resource_path)

    return Configuration(name, timestamp, docker_repository, kerberos, resource_path)

def _build_component_images(components: List[str],
                            input_configuration: Dict[str, Dict[str, str]],
                            initial_configuration: Configuration,
                            image_builders: Dict[str, ComponentImageBuilder],
                            force_rebuild: List[str]) -> Tuple[Configuration, Optional[Exception]]:
    resulting_configuration = initial_configuration

    logging.info("Building components in the following order: %s.", components)

    for component in components:
        component_conf = input_configuration[component]
        image_builder = image_builders[component]
        force_rebuild_component = component in force_rebuild

        try:
            component_config = image_builder.build(component_conf, resulting_configuration, force_rebuild_component)
        # pylint: disable=broad-except
        except Exception as exception:

            return (resulting_configuration, exception)

        # pylint: enable=broad-except
        resulting_configuration.components[component] = component_config

    return (resulting_configuration, None)

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

def _raise_on_dependencies_without_configuration(components: List[str],
                                                 dependencies: Dict[str, List[str]]) -> None:
    deps_without_config = _dependencies_without_configuration(components, dependencies)
    if len(deps_without_config) > 0:
        msg_template = ("Error: the following components are not specified in the configuration but are needed as " +
                        "dependencies by other components: {}.")
        msg = msg_template.format((list(deps_without_config)))

        logging.error(msg)
        raise ValueError(msg)

def _get_sorted_nodes(dependencies: Dict[str, List[str]]) -> List[str]:
    dag = dbd.graph.build_graph_from_dependencies(dependencies)
    return dag.get_topologically_sorted_nodes()

def _get_cache_dir(args: argparse.Namespace, default_cache_dir: Path) -> Path:
    if args.cache is None:
        logging.info("Using the default cache directory: %s.", default_cache_dir)
        return default_cache_dir

    cache_dir = Path(args.cache).expanduser().resolve()
    logging.info("Using cache directory: %s", cache_dir)
    return cache_dir

def _get_cache(args: argparse.Namespace,
               default_cache_dir: Path,
               max_cache_size: int) -> Cache:
    cache_dir = _get_cache_dir(args, default_cache_dir)
    return Cache(cache_dir, max_size=max_cache_size)

def start_dbd(args: argparse.Namespace) -> None:
    """
    Starts the main dbd program.
    """

    input_conf = _parse_yaml(args.config_file)
    initial_configuration = _get_initial_configuration(input_conf,
                                                       dbd.defaults.DOCKER_REPOSITORY,
                                                       dbd.defaults.RESOURCE_PATH)

    components = _get_components(input_conf)

    assemblies = _get_component_assemblies(initial_configuration, components)
    dependencies = _get_dependencies_from_assemblies(assemblies)

    _raise_on_dependencies_without_configuration(components, dependencies)

    topologically_sorted_components = _get_sorted_nodes(dependencies)

    cache = _get_cache(args, dbd.defaults.CACHE_DIR, int(args.cache_size))
    image_builders = _get_component_image_builders(components, assemblies, cache)

    force_rebuild_components = _get_force_rebuild_components(args, components)
    (output_configuration, exception) = _build_component_images(topologically_sorted_components,
                                                                input_conf["components"],
                                                                initial_configuration,
                                                                image_builders,
                                                                force_rebuild_components)

    dbd.output.generate_output(input_conf, output_configuration, Path(args.output_dir), exception is not None)

    if exception:
        # We suppressed the exception to write output so that the user
        # knows what to clean up, and now we re-throw the exception.
        raise exception

    cache.enforce_max_size()

def main() -> None:
    """
    The entry point to the application. Run on the command line with `--help` to get information on usage.
    """

    logging.basicConfig(level=logging.INFO)
    args = _get_argument_parser().parse_args()

    # Check whether docker is installed and running.
    dbd.docker_setup.check_docker_daemon_running()

    start_dbd(args)

if __name__ == "__main__":
    main()
