#!/usr/bin/env python3

"""
This module contains a class that stores constant component-specific
information that does not depend on the actual build configuration.
"""

from typing import Any, Dict, List, Optional

class Assembly:
    """
    A class storing constant component-specific information that does not depend on the actual build configuration.
    """

    @staticmethod
    def from_dict(dictionary: Dict[str, Any]) -> "Assembly":
        """
        Creates a new `Assembly` object from a dictionary.

        Args:
            dictionary: The dictionary from which to create the `Assembly` object.

        Returns:
            The created `Assembly` object.

        """

        dictionary = dictionary.copy()
        dependencies = dictionary.pop("dependencies", [])
        if not isinstance(dependencies, list) or not all(map(lambda x: isinstance(x, str), dependencies)):
            raise TypeError("The 'dependencies' key must be associated with a value of type `List[str]`.")

        url_template = Assembly._pop_string(dictionary, "url")

        version_command = Assembly._pop_string(dictionary, "version_command")

        version_regex = Assembly._pop_string(dictionary, "version_regex")

        return Assembly(dependencies, url_template, version_command, version_regex, dictionary)

    @staticmethod
    def _pop_string(dictionary: Dict[str, Any], key: str) -> Optional[str]:
        value = dictionary.pop(key, None)
        if value is not None and not isinstance(value, str):
            raise TypeError("The '{}' key must be associated with a value of type `str` and not {}."
                            .format(key, type(value)))

        return value

    def __init__(self,
                 dependencies: List[str],
                 url_template: Optional[str],
                 version_command: Optional[str],
                 version_regex: Optional[str],
                 others: Optional[Dict[str, Any]] = None) -> None:
        """
        Creates a new `Assembly` object.

        Args:
            dependencies: The dependencies of the component.
            url_template: A url templated with the version number of the component, from which the release
                 archive can be downloaded. In the string, \"{0}\" is the placholder for the version number.
            version_command: The command that should be run inside the built docker container
                to retrieve its version number. The actual version number will be obtained by
                matching `version_regex` against the output of this command.
            version_regex: The regex that will be matched against the output
                of `version_command` to retrieve the actual version number.
            others: A dictionary possibly containing additional information.

        """

        self.dependencies = dependencies
        self.url_template = url_template
        self.version_command = version_command
        self.version_regex = version_regex
        self.others: Dict[str, Any] = others if others is not None else {}
