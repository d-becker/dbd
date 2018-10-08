#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import Any, Dict, Union

import unittest

import dbd.output.docker_compose_generator

class TestGenerateDockerComposeFileDict(unittest.TestCase):
    def setUp(self) -> None:
        self.docker_compose_parts: Dict[str, Dict[str, Union[dbd.output.docker_compose_generator.Services, Any]]] = {
            "hadoop": {
                "services": {
                    "namenode": {
                        "image": "${HADOOP_IMAGE}",
                        "hostname": "namenode"
                    }
                }
            },
            "oozie": {
                "services": {
                    "oozieserver": {
                        "image": "${OOZIE_IMAGE",
                        "ports": ["11000:11000"]
                    },
                    "historyserver": {
                        "image" : "${OOZIE_IMAGE}"
                    }
                }
            }
        }

    def test_service_customisation_ok(self) -> None:
        customisations: dbd.output.docker_compose_generator.Services = {}

        customisations["hadoop"] = {
            "namenode": {"hostname": "nn"}
        }

        customisations["oozie"] = {
            "oozieserver" : {"ports" : ["11000:11000", "11002:11002"]},
            "historyserver" : {"ports" : ["8000:8000"]}
        }

        result = dbd.output.docker_compose_generator.generate_docker_compose_file_dict(self.docker_compose_parts,
                                                                                       customisations)

        expected_namenode = {"image": "${HADOOP_IMAGE}",
                             "hostname": "nn"}
        self.assertEqual(expected_namenode, result["services"]["namenode"])

        expected_oozieserver = {"image": "${OOZIE_IMAGE",
                                "ports" : ["11000:11000", "11002:11002"]}
        self.assertEqual(expected_oozieserver, result["services"]["oozieserver"])

        expected_historyserver = {"image" : "${OOZIE_IMAGE}",
                                  "ports" : ["8000:8000"]}
        self.assertEqual(expected_historyserver, result["services"]["historyserver"])

    def test_service_customisation_adding_new_service_fails(self) -> None:
        customisations = {
            "oozie": {
                "new_service": {"ports" : ["8500:8500"]}
            }
        }

        with self.assertRaises(ValueError):
            dbd.output.docker_compose_generator.generate_docker_compose_file_dict(self.docker_compose_parts,
                                                                                  customisations)
