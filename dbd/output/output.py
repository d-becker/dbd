#!/usr/bin/env python3

"""
This module contains the functions that are used in generating the output of the configuration build process.
"""

import io
from pathlib import Path
from typing import Any, Dict, List

import yaml

from dbd.configuration import Configuration
from dbd.component_config import DistType

import dbd.defaults

import dbd.output.docker_compose_generator

def generate_compose_config_file_text(sorted_components: List[str], configuration: Configuration) -> str:
    """
    Generates the contents of the compose-config file.

    Args:
        sorted_components: The names of the components in the order they were built.
        configuration: The `Configuration` object that contains the information about the configuration of the build.

    Returns:
        The contents of the compose-config file.

    """

    text = io.StringIO()
    for component in sorted_components:
        file_path = configuration.get_compose_config_part(component)

        if file_path.exists():
            with file_path.open() as file:
                contents = file.read()

                comment = "# {}\n".format(component)

                text.write(comment)
                text.write(contents + "\n\n")

    return text.getvalue()

def generate_config_report(configuration: Configuration, build_failed: bool) -> str:
    """
    Generates the contents of the output_configuration.yaml file.

    Args:
        configuration: The `Configuration` object that contains the information about the configuration of the build.
        build_failed: Whether the build failed.

    Returns:
        The contents of the output_configuration.yaml file.

    """

    text = io.StringIO()

    text.write("name: {}\n".format(configuration.name))
    text.write("timestamp: {}\n".format(configuration.timestamp))
    text.write("build_successful: {}\n".format(not build_failed))
    text.write("component-order: {}\n".format(configuration.get_component_order()))
    text.write("components:\n")

    indentation = "  "
    for component, config in configuration.components.items():
        text.write(indentation + component + ":\n")

        text.write(indentation * 2 + "dist_type: "
                   + ("release" if config.dist_type == DistType.RELEASE else "snapshot")
                   + "\n")
        text.write(indentation * 2 + "version: " + config.version + "\n")
        text.write(indentation * 2 + "image_name: " + config.image_name + "\n")
        text.write(indentation * 2 + "reused: " + str(config.reused).lower() + "\n")

    return text.getvalue()

def generate_env_file_text(configuration: Configuration) -> str:
    """
    Generates the contents of the ".env" file.

    Args:
        configuration: The `Configuration` object that contains the information about the configuration of the build.

    Returns:
        The contents of the ".env" file.

    """

    text = io.StringIO()

    for component, config in configuration.components.items():
        variable_name = "{}_IMAGE".format(component.upper())
        variable_value = config.image_name

        text.write("{}={}\n".format(variable_name, variable_value))

    return text.getvalue()

def generate_docker_compose_file_text(input_component_config: Dict[str, Any], configuration: Configuration) -> str:
    """
    Generates the contents of the docker-compose file.

    Args:
        input_component_config: The "components" section of the `BuildConfiguration` dictionary.
        configuration: The `Configuration` object that contains the information about the configuration of the build.

    Returns:
        The contents of the docker-compose file as a string.

    """

    docker_compose_parts = {}
    for component in input_component_config:
        file_path = configuration.get_docker_compose_part(component)
        with file_path.open() as file:
            docker_compose_part = yaml.load(file)
            docker_compose_parts[component] = docker_compose_part

    if configuration.kerberos:
        krb5 = dbd.defaults.KERBEROS_SERVICE_CONFIG
        docker_compose_parts["krb5"] = yaml.load(krb5)

    customised_services = {component : value.get("services", {})
                           for component, value in input_component_config.items()}

    docker_compose_dict = dbd.output.docker_compose_generator.generate_docker_compose_file_dict(docker_compose_parts,
                                                                                                customised_services)
    return yaml.dump(docker_compose_dict, default_style=None)

def generate_output(input_config: Dict[str, Any],
                    configuration: Configuration,
                    output_location: Path,
                    build_failed: bool) -> None:
    """
    Generates the output of the building process.

    Args:
        input_conf: The dictionary that contains the contents of the `BuildConfiguration` file, provided by the user.
        configuration: The `Configuration` object that contains the information about the configuration of the build.
        output_location: The directory in which the output should be generated.
        build_failed: If this parameter is `True`, only the 'output_configuration.yaml' file will be generated.

    Raises:
        ValueError: If `output_location` does not point to an existing directory.

    """

    components = input_config["components"].keys()

    if not output_location.is_dir():
        raise ValueError("The provided output location is not a directory.")

    out = output_location / "{}_{}".format(configuration.name, configuration.timestamp)
    out.mkdir()

    with (out / "output_configuration.yaml").open("w") as file:
        config_report = generate_config_report(configuration, build_failed)
        file.write(config_report)

    if build_failed:
        return

    with (out / ".env").open("w") as file:
        env_file_text = generate_env_file_text(configuration)
        file.write(env_file_text)

    docker_compose_file_text = generate_docker_compose_file_text(input_config["components"],
                                                                 configuration)
    with (out / "docker-compose.yaml").open("w") as docker_compose_file:
        docker_compose_file.write(docker_compose_file_text)

    compose_config_file_text = generate_compose_config_file_text(components, configuration)
    with (out / "compose-config").open("w") as compose_config_file:
        compose_config_file.write(compose_config_file_text)
