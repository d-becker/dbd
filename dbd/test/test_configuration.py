#!/usr/bin/env python3

# pylint: disable=missing-docstring

from pathlib import Path

import unittest

from  dbd.configuration import Configuration

class TestConfiguration(unittest.TestCase):
    NAME: str = "config_name"
    TIMESTAMP: str = "123456789"
    REPOSITORY: str = "dbd"
    RESOURCE_PATH: Path = Path("path/to/resources")

    COMPONENT: str = "any_component"

    UNSECURE: str = "unsecure"
    KERBEROS: str = "kerberos"

    @staticmethod
    def _get_default_configuration() -> Configuration:
        return Configuration(TestConfiguration.NAME,
                             TestConfiguration.TIMESTAMP,
                             TestConfiguration.REPOSITORY,
                             False,
                             TestConfiguration.RESOURCE_PATH)

    @staticmethod
    def _get_default_configuration_security(kerberos: bool) -> Configuration:
        return Configuration(TestConfiguration.NAME,
                             TestConfiguration.TIMESTAMP,
                             TestConfiguration.REPOSITORY,
                             kerberos,
                             TestConfiguration.RESOURCE_PATH)

    def test_name(self) -> None:
        configuration = TestConfiguration._get_default_configuration()

        self.assertEqual(TestConfiguration.NAME, configuration.name)

    def test_timestamp(self) -> None:
        configuration = TestConfiguration._get_default_configuration()

        self.assertEqual(TestConfiguration.TIMESTAMP, configuration.timestamp)

    def test_repository(self) -> None:
        configuration = TestConfiguration._get_default_configuration()

        self.assertEqual(TestConfiguration.REPOSITORY, configuration.repository)

    def test_kerberos_true(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(True)

        self.assertTrue(configuration.kerberos)

    def test_kerberos_false(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(False)

        self.assertFalse(configuration.kerberos)

    def test_get_resource_dir(self) -> None:
        configuration = TestConfiguration._get_default_configuration()

        self.assertEqual(TestConfiguration.RESOURCE_PATH / TestConfiguration.COMPONENT,
                         configuration.get_resource_dir(TestConfiguration.COMPONENT))

    def test_get_assembly_unsecure(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(False)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.UNSECURE
                    / "assembly.yaml")
        self.assertEqual(expected, configuration.get_assembly(TestConfiguration.COMPONENT))

    def test_get_assembly_kerberos(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(True)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.KERBEROS
                    / "assembly.yaml")
        self.assertEqual(expected, configuration.get_assembly(TestConfiguration.COMPONENT))

    def test_get_compose_config_part_unsecure(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(False)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.UNSECURE
                    / "compose-config_part")
        self.assertEqual(expected, configuration.get_compose_config_part(TestConfiguration.COMPONENT))

    def test_get_compose_config_part_kerberos(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(True)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.KERBEROS
                    / "compose-config_part")
        self.assertEqual(expected, configuration.get_compose_config_part(TestConfiguration.COMPONENT))

    def test_get_docker_compose_part_unsecure(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(False)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.UNSECURE
                    / "docker-compose_part.yaml")
        self.assertEqual(expected, configuration.get_docker_compose_part(TestConfiguration.COMPONENT))

    def test_get_docker_compose_part_kerberos(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(True)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.KERBEROS
                    / "docker-compose_part.yaml")
        self.assertEqual(expected, configuration.get_docker_compose_part(TestConfiguration.COMPONENT))

    def test_get_docker_context_unsecure(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(False)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.UNSECURE
                    / "docker_context")
        self.assertEqual(expected, configuration.get_docker_context(TestConfiguration.COMPONENT))

    def test_get_docker_context_kerberos(self) -> None:
        configuration = TestConfiguration._get_default_configuration_security(True)

        expected = (TestConfiguration.RESOURCE_PATH
                    / TestConfiguration.COMPONENT
                    / TestConfiguration.KERBEROS
                    / "docker_context")
        self.assertEqual(expected, configuration.get_docker_context(TestConfiguration.COMPONENT))
