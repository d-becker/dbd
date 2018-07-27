#!/usr/bin/env python3

import io, shutil
from pathlib import Path
from typing import Any, Dict, List

import yaml

from component_builder import Configuration, DistType

def extend_docker_compose_dict(original: Dict[str, Dict[str, Any]], other: Dict[str, Dict[str, Any]]):
    for key in other.keys():
        if key not in original:
            original[key] = dict()

        original_inner_dict: Dict[str, Any] = original[key]
        other_inner_dict: Dict[str, Any] = other[key]

        intersection = set(original_inner_dict.keys()).intersection(set(other_inner_dict.keys()))

        if len(intersection) > 0:
            raise ValueError("Multiple definitions of the following in section {}: {}.".format(key, intersection))

        original_inner_dict.update(other_inner_dict)

def generate_docker_compose_file_text(sorted_components: List[str], configuration: Configuration) -> str:
    document_body: Dict[str, Dict[str, Any]] = dict()
    
    for component in sorted_components:
        file_path = configuration.resource_path / component / "docker-compose_part.yaml"
        file_text: str
        with file_path.open() as file:
            component_docker_compose_dict = yaml.load(file)
            extend_docker_compose_dict(document_body, component_docker_compose_dict)

    document = {"version": "3"}
    document.update(document_body)
    return yaml.dump(document, default_style=None)

def generate_output(sorted_components: List[str], configuration: Configuration, output_location: Path) -> None:
    if not output_location.is_dir():
        raise ValueError("The provided output location is not a directory.")

    out = output_location / "{}_{}".format(configuration.name, configuration.timestamp)
    out.mkdir()

    with (out / "output_configuration.yaml").open("w") as file:
        config_report = generate_config_report(configuration)
        file.write(config_report)

    with (out / ".env").open("w") as file:
        env_file_text = generate_env_file_text(configuration)
        file.write(env_file_text)

    # TODO: to be deleted.
    docker_dependency_dir = configuration.resource_path / "docker"
    docker_dependency_files = docker_dependency_dir.glob("*")
    for dependency_file in docker_dependency_files:
        shutil.copy(str(dependency_file), str(out))

    docker_compose_file_text = generate_docker_compose_file_text(sorted_components, configuration)
    with (out / "docker-compose.yaml").open("w") as docker_compose_file:
        docker_compose_file.write(docker_compose_file_text)

def generate_config_report(configuration: Configuration) -> str:
    text = io.StringIO()

    text.write("name: {}\n".format(configuration.name))
    text.write("timestamp: {}\n".format(configuration.timestamp))
    text.write("components:\n")

    indentation = "  "
    for component, config in configuration.components.items():
        text.write(indentation + component + ":\n")

        text.write(indentation * 2 + "dist_type: "
                   + ("release" if config.dist_type == DistType.RELEASE else "snapshot")
                   + "\n")
        text.write(indentation * 2 + "version: " + config.version + "\n")
        text.write(indentation * 2 + "image_name: " + config.image_name + "\n")
    
    return text.getvalue()

def generate_env_file_text(configuration: Configuration) -> str:
    text = io.StringIO()

    for component, config in configuration.components.items():
        variable_name = "{}_IMAGE".format(component.upper())
        variable_value = config.image_name

        text.write("{}={}\n".format(variable_name, variable_value))

    return text.getvalue()
