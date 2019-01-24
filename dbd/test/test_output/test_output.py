#!/usr/bin/env python3

# pylint: disable=missing-docstring

from pathlib import Path

import tempfile

from typing import Dict

import unittest

import yaml

from dbd.configuration import Configuration
from dbd.component_config import ComponentConfig, DistType

import dbd.output.output

class TestOutput(unittest.TestCase):
    def test_generate_env_file_text(self) -> None:
        configuration = Configuration("configuration_name", "0001", "dbd", False, Path())

        dist_type = DistType.RELEASE
        version = "1.0.0"
        reused = False

        for i in range(4):
            configuration.components["component{}".format(i)] = ComponentConfig(
                dist_type,
                version,
                "image{}".format(i),
                reused)

        expected_env_file_text = """\
COMPONENT0_IMAGE=image0
COMPONENT1_IMAGE=image1
COMPONENT2_IMAGE=image2
COMPONENT3_IMAGE=image3
"""

        self.assertEqual(expected_env_file_text, dbd.output.output.generate_env_file_text(configuration))


    def test_generate_config_report(self) -> None:
        config_name = "configuration_name"
        timestamp = "1548328077"
        build_failed = False

        configuration = Configuration(config_name, timestamp, "dbd", False, Path())
        configuration.components["component1"] = ComponentConfig(DistType.RELEASE, "1.0.0.", "image1", True)
        configuration.components["component2"] = ComponentConfig(DistType.SNAPSHOT, "2.0.0.", "image2", False)

        result = dbd.output.output.generate_config_report(configuration, build_failed)
        yaml_dict = yaml.load(result)

        self.assertEqual(config_name, yaml_dict.get("name"))
        self.assertEqual(timestamp, str(yaml_dict.get("timestamp")))
        self.assertEqual(build_failed, not yaml_dict.get("build_successful"))
        self.assertEqual(["component1", "component2"], yaml_dict.get("component-order"))

        components = yaml_dict.get("components")
        self.assertIsNotNone(components)

        component1 = components.get("component1")
        self._assert_component_properties(configuration, "component1", component1)

        component2 = components.get("component2")
        self._assert_component_properties(configuration, "component2", component2)

    def _assert_component_properties(self,
                                     configuration: Configuration,
                                     component_name: str,
                                     component_dict: Dict[str, str]) -> None:
        self.assertIsNotNone(component_dict)

        component_dist_type = ("release"
                               if configuration.components[component_name].dist_type == DistType.RELEASE
                               else "snapshot")
        self.assertEqual(component_dist_type, component_dict["dist_type"])
        self.assertEqual(configuration.components[component_name].version, component_dict["version"])
        self.assertEqual(configuration.components[component_name].image_name, component_dict["image_name"])
        self.assertEqual(configuration.components[component_name].reused, component_dict["reused"])

    @staticmethod
    def _write_file(path: Path, text: str) -> None:
        with open(path, "w") as output_file:
            output_file.write(text)

    @staticmethod
    def _write_docker_compose_files(resource_dir: Path, component_name: str, compose_config_part: str) -> None:
        component_dir = resource_dir / component_name / "unsecure"
        component_dir.mkdir(parents=True, exist_ok=True)

        TestOutput._write_file(component_dir / "compose-config_part", compose_config_part)

    def test_generate_compose_config_file_text(self) -> None:
        component1_name = "component1"
        component2_name = "component2"

        compose_config_part1 = """\
CORE-SITE.XML_fs.default.name=hdfs://namenode:9000
CORE-SITE.XML_fs.defaultFS=hdfs://namenode:9000"""

        compose_config_part2 = """\
CORE-SITE.XML_hadoop.proxyuser.oozie.hosts=*
CORE-SITE.XML_hadoop.proxyuser.oozie.groups=*"""

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            TestOutput._write_docker_compose_files(tmp_dir, component1_name, compose_config_part1)
            TestOutput._write_docker_compose_files(tmp_dir, component2_name, compose_config_part2)

            configuration = Configuration("configuration_name", "0001", "dbd", False, tmp_dir)

            result = dbd.output.output.generate_compose_config_file_text([component1_name, component2_name],
                                                                         configuration)

        lines_component1 = compose_config_part1.split("\n")
        lines_component2 = compose_config_part2.split("\n")

        input_lines = lines_component1 + lines_component2

        output_lines = result.split("\n")

        for line in input_lines:
            self.assertIn(line, output_lines)

    def test_generate_docker_compose_file_text_customised_service_no_kerberos(self) -> None:
        self._test_generate_docker_compose_file_text_customised_service(False)

    def test_generate_docker_compose_file_text_customised_service_with_kerberos(self) -> None:
        self._test_generate_docker_compose_file_text_customised_service(True)

    def _test_generate_docker_compose_file_text_customised_service(self, kerberos: bool) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)

            middle_path = "kerberos" if kerberos else "unsecure"
            resource_dir = tmp_dir / "hadoop" / middle_path
            resource_dir.mkdir(exist_ok=True, parents=True)
            docker_compose_part = """\
services:
   resourcemanager:
      image: ${HADOOP_IMAGE}
   nodemanager:
      image: ${HADOOP_IMAGE}
"""

            with open(resource_dir / "docker-compose_part.yaml", "w") as output_file:
                output_file.write(docker_compose_part)

            build_config_file_text = """\
name: oozie500hadoop265
components:
  hadoop:
    release: 2.6.5
    services:
      nodemanager:
        ports:
          - 11000:11000
          - 11002:11002"""

            input_conf = yaml.load(build_config_file_text)
            input_component_config = input_conf["components"]

            configuration = Configuration("configuration_name", "0001", "dbd", kerberos, tmp_dir)

            result = dbd.output.output.generate_docker_compose_file_text(input_component_config, configuration)

        result_dict = yaml.load(result)
        self.assertEqual(input_component_config["hadoop"]["services"]["nodemanager"]["ports"],
                         result_dict["services"]["nodemanager"]["ports"])
        self.assertEqual(kerberos, "krb5" in result_dict["services"])
