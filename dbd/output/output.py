#!/usr/bin/env python3

"""
This module contains the functions that are used in generating the output of the configuration build process.
"""

import io
from pathlib import Path
from typing import Any, Dict, List

import yaml

from dbd.component_builder import Configuration, DistType
import dbd.output.docker_compose_generator

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

def _generate_docker_compose_file_text(input_component_config: Dict[str, Any], resource_path: Path) -> str:
    docker_compose_parts = {}
    for component in input_component_config:
        file_path = resource_path / component / "docker-compose_part.yaml"
        with file_path.open() as file:
            docker_compose_part = yaml.load(file)
            docker_compose_parts[component] = docker_compose_part

    customised_services = {component : value.get("services", {})
                           for component, value in input_component_config.items()}

    docker_compose_dict = dbd.output.docker_compose_generator.generate_docker_compose_file_dict(docker_compose_parts,
                                                                                                customised_services)
    return yaml.dump(docker_compose_dict, default_style=None)

def generate_output(input_config: Dict[str, Any],
                    configuration: Configuration,
                    output_location: Path) -> None:
    """
    Generates the output of the building process.

    Args:
        input_conf: The dictionary that contains the contents of the `BuildConfiguration` file, provided by the user.
        configuration: The `Configuration` object that contains the information about the configuration build.
        output_location: The directory in which the output should be generated.

    Raises:
        ValueError: If `output_location` does not point to an existing directory.

    """

    components = input_config["components"].keys()

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

    docker_compose_file_text = _generate_docker_compose_file_text(input_config["components"],
                                                                  configuration.resource_path)
    with (out / "docker-compose.yaml").open("w") as docker_compose_file:
        docker_compose_file.write(docker_compose_file_text)

    compose_config_file_text = _generate_compose_config_file_text(components, configuration.resource_path)
    with (out / "compose-config").open("w") as compose_config_file:
        compose_config_file.write(compose_config_file_text)
