#!/usr/bin/env python3

import importlib, os, re, shutil, sys, time, __main__

from pathlib import Path
from typing import Any, Dict, List

import docker, yaml

import hadoop, oozie, graph
from component_builder import Configuration, DistType

def parse_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def get_components(conf: Dict[str, Any]) -> List[str]:
    return list(conf["components"].keys())
    
def main() -> None:
    filename = sys.argv[1]
    conf = parse_yaml(filename)

    timestamp: str = str(int(time.time()))
    repository = "dbd"
    resource_path = Path(__main__.__file__).parent.resolve().parent / "resources"

    configuration = Configuration(timestamp, repository, resource_path)

    print("Components: {}.".format(get_components(conf)))

    components = get_components(conf)

    component_modules = [(name, importlib.import_module(name)) for name in components]

    image_builders = dict([(name, module.__dict__["ImageBuilder"]()) for (name, module) in component_modules])

    dependencies = dict([(name, image_builders[name].dependencies()) for name in components])
    print(dependencies)

    dag = graph.build_graph_from_dependencies(dependencies)
    topologically_sorted_components = dag.get_topologically_sorted_nodes()

    for component in topologically_sorted_components:
        component_conf = conf["components"][component]
        image_builder = image_builders[component]
        component_config = image_builder.build(component_conf, configuration)
        configuration.components[component] = component_config

main()
        
