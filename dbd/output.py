#!/usr/bin/env python3

"""
This module contains the functions that are used in generating the output of the configuration build process.
"""

import io
from pathlib import Path
from typing import Any, Dict, List

import yaml

from component_builder import Configuration, DistType

def _extend_docker_compose_dict(original: Dict[str, Dict[str, Any]], other: Dict[str, Dict[str, Any]]) -> None:
    for key in other.keys():
        if key not in original:
            original[key] = dict()

        original_inner_dict: Dict[str, Any] = original[key]
        other_inner_dict: Dict[str, Any] = other[key]

        intersection = set(original_inner_dict.keys()).intersection(set(other_inner_dict.keys()))

        if len(intersection) > 0:
            raise ValueError("Multiple definitions of the following in section {}: {}.".format(key, intersection))

        original_inner_dict.update(other_inner_dict)

def _generate_docker_compose_file_text(sorted_components: List[str], resource_path: Path) -> str:
    document_body: Dict[str, Dict[str, Any]] = dict()

    for component in sorted_components:
        file_path = resource_path / component / "docker-compose_part.yaml"

        if file_path.exists():
            with file_path.open() as file:
                component_docker_compose_dict = yaml.load(file)
                _extend_docker_compose_dict(document_body, component_docker_compose_dict)

    document: Dict[str, Any] = {"version": "3"}
    document.update(document_body)
    return yaml.dump(document, default_style=None)

def _generate_compose_config_file_text(sorted_components: List[str], resource_path: Path) -> str:
    text = io.StringIO()
    for component in sorted_components:
        file_path = resource_path / component / "compose-config_part"

        if file_path.exists():
            with file_path.open() as file:
                contents = file.read()

                comment = "# {}\n".format(component)

                text.write(comment)
                text.write(contents + "\n\n")

    return text.getvalue()

def _generate_config_report(configuration: Configuration) -> str:
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

def _generate_env_file_text(configuration: Configuration) -> str:
    text = io.StringIO()

    for component, config in configuration.components.items():
        variable_name = "{}_IMAGE".format(component.upper())
        variable_value = config.image_name

        text.write("{}={}\n".format(variable_name, variable_value))

    return text.getvalue()

def generate_output(sorted_components: List[str], configuration: Configuration, output_location: Path) -> None:
    """
    Generates the output of the configuration building process.

    Args:
        sorted_components: The components that were present in the configuration in topologically sorted order.
        configuration: The `Configuration` object that contains the information about the configuration build.
        output_location: The directory in which the output should be generated.

    Raises:
        ValueError: If `output_location` does not point to an existing directory.

    """

    if not output_location.is_dir():
        raise ValueError("The provided output location is not a directory.")

    out = output_location / "{}_{}".format(configuration.name, configuration.timestamp)
    out.mkdir()

    with (out / "output_configuration.yaml").open("w") as file:
        config_report = _generate_config_report(configuration)
        file.write(config_report)

    with (out / ".env").open("w") as file:
        env_file_text = _generate_env_file_text(configuration)
        file.write(env_file_text)

    docker_compose_file_text = _generate_docker_compose_file_text(sorted_components, configuration.resource_path)
    with (out / "docker-compose.yaml").open("w") as docker_compose_file:
        docker_compose_file.write(docker_compose_file_text)

    compose_config_file_text = _generate_compose_config_file_text(sorted_components, configuration.resource_path)
    with (out / "compose-config").open("w") as compose_config_file:
        compose_config_file.write(compose_config_file_text)
