#!/usr/bin/env python3

"""
This module contains the logic that generates the dictionary of the output docker-compose file.
"""

from typing import Any, Dict, Union

Services = Dict[str, Dict[str, Any]]

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

def _apply_service_customisations(original_services: Dict[str, Dict[str, Any]],
                                  customisations: Services) -> None:
    for service_to_customise in customisations:
        if service_to_customise not in original_services:
            raise ValueError("Trying to customise non-existing service: {}.".format(service_to_customise))

        original_services[service_to_customise].update(customisations[service_to_customise])



def generate_docker_compose_file_dict(docker_compose_parts: Dict[str, Dict[str, Union[Services, Any]]],
                                      customised_services: Dict[str, Services]) -> Dict[str, Dict[str, Any]]:
    """
    Takes a dictionary of partial docker-compose file dictionaries and a dictionary of service customisations and
    produces a final docker-compose file dictionary which will contain the services of the components that are the
    keys in `docker_compose_parts`. The service customisations overwrite the default values. Adding new services will
    raise `ValueError`.

    Args:
        docker_compose_parts: A dictionary where the keys are the names of the components
            and the values are the default docker-compose files parsed into a dictionary.
        customised_services: A dictionary where the keys are the names of the components and the values are
            dictionaries containing docker-compose configuration that should be added to the services section
            of the resulting docker-compose file. The configuration key-value pairs within each service override
            the default values if they exist, otherwise they are added to the configuration. However, adding new
            services is not allowed.

    Returns:
        A dictionary from which the resulting docker-compose file can be generated.

    Raises:
        ValueError: thrown if there is a service in `customised_services` that
            does not exist in the default docker-compose partial files.

    """

    document_body: Dict[str, Dict[str, Any]] = dict()

    for component in docker_compose_parts:
        docker_compose_part = docker_compose_parts[component]
        services: Services = docker_compose_part["services"]
        _apply_service_customisations(services,
                                      customised_services.get(component, {}))
        _extend_docker_compose_dict(document_body, docker_compose_part)

    document: Dict[str, Any] = {"version": "3"}
    document.update(document_body)

    return document
