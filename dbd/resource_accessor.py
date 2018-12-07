#!/usr/bin/env python3

from pathlib import Path

class ResourceAccessor:
    def __init__(self, resource_path: Path) -> None:
                 # kerberos: bool) -> None:
        self._resource_path = resource_path
        # self._kerberos = kerberos

    def get_resource_dir(self, component_name: str) -> Path:
        return self._resource_path / component_name

    def get_assembly(self, component_name: str) -> Path:
        return self.get_resource_dir(component_name) / "assembly.yaml"

    def get_compose_config_part(self, component_name: str) -> Path:
        return self.get_resource_dir(component_name) / "compose-config_part"

    def get_docker_compose_part(self, component_name: str) -> Path:
        return self.get_resource_dir(component_name) / "docker-compose_part.yaml"

    def get_docker_context(self, component_name: str) -> Path:
        return self.get_resource_dir(component_name) / "docker_context"
