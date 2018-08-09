#!/usr/bin/env python3

import tarfile

from pathlib import Path
from typing import Dict, List, Optional

import docker
import wget

from component_builder import DistType, ComponentConfig, ComponentImageBuilder, Configuration
import utils

# TODO: remove this file

class BaseImageBuilder(ComponentImageBuilder):
    def __init__(self,
                 component_name: str,
                 dependencies: List[str],
                 url_template: str,
                 version_command: str,
                 version_regex: str) -> None:
        self._name = component_name
        self._dependencies = dependencies
        self._url_template = url_template # A string with {0} which will be formatted with the version.
        self._docker_client = docker.from_env()
        self._version_command = version_command
        self._version_regex = version_regex

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List[str]:
        return self._dependencies

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        (dist_type, argument) = utils.dist_type_and_arg(component_config)
        image_name = self._get_image_name(dist_type,
                                          argument if dist_type == DistType.RELEASE else None,
                                          built_config)

        reuse_existing_image = (not force_rebuild
                                and dist_type == DistType.RELEASE
                                and utils.image_exists_locally(self._docker_client, image_name))

        if reuse_existing_image:
            print("Reusing existing {} image: {}.".format(self.name(), image_name))
        else:
            with utils.TmpDirHandler(self._get_resource_dir(built_config.resource_path)) as tmp_dir:
                if dist_type == DistType.RELEASE:
                    release_version = argument
                    self._prepare_tarfile_release(release_version, tmp_dir, built_config)
                elif dist_type == DistType.SNAPSHOT:
                    path = Path(argument)
                    self._prepare_tarfile_snapshot(path, tmp_dir, built_config)
                else:
                    raise ValueError("Unexpected DistType value.")

                self._build_docker_image(image_name, built_config)

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            version = utils.find_out_version_from_image(self._docker_client,
                                                        image_name,
                                                        self.name(),
                                                        self._version_command,
                                                        self._version_regex)

        return ComponentConfig(dist_type, version, image_name)

    def _prepare_tarfile_release(self,
                                 version: str,
                                 tmp_dir: Path,
                                 _built_config: Configuration) -> None:
        url = self._url_template.format(version)
        print("Downloading {} release version {} from {}.".format(self.name(), version, url))

        out_path = tmp_dir / "{}.tar.gz".format(self.name())
        wget.download(url, out=str(out_path.expanduser()))

        print()

    def _prepare_tarfile_snapshot(self,
                                  path: Path,
                                  tmp_dir: Path,
                                  _built_config: Configuration) -> None:
        print("Preparing {} snapshot version from path {}.".format(self.name(), path))

        with tarfile.open(tmp_dir / "{}.tar.gz".format(self.name()), "w:gz") as tar:
            tar.add(str(path.expanduser()), arcname=path.name)

    def _build_docker_image(self,
                            image_name: str,
                            built_config: Configuration) -> None:
        print("Building docker image {}.".format(image_name))

        # Providing the dependencies as arguments
        buildargs: Dict[str, str] = dict()

        for dependency in self.dependencies():
            dependency_image_name = built_config.components[dependency].image_name
            buildargs["{}_IMAGE".format(dependency.upper())] = dependency_image_name

        dockerfile_path = self._get_resource_dir(built_config.resource_path)
        self._docker_client.images.build(path=str(dockerfile_path), buildargs=buildargs, tag=image_name, rm=True)
        print("Docker image built.")

    def _get_image_name(self,
                        dist_type: DistType,
                        version: Optional[str],
                        built_config: Configuration) -> str:
        template = "{repository}/{component}:{component_tag}{dependencies_tag}"

        component_tag: str
        if dist_type == DistType.RELEASE:
            if version is None:
                raise ValueError("The version is None but release mode is specified.")
            component_tag = version
        elif dist_type == DistType.SNAPSHOT:
            component_tag = "snapshot_{}".format(built_config.timestamp)
        else:
            raise RuntimeError("Unexpected value of DistType.")

        dependencies_tag: str
        dependencies = self.dependencies()
        dependencies.sort()

        deps_join_list: List[str] = [""]
        for dependency in dependencies:
            dependency_tag = built_config.components[dependency].image_name.split(":")[-1]
            deps_join_list.append(dependency + dependency_tag)

        dependencies_tag = "_".join(deps_join_list)

        return template.format(repository=built_config.repository,
                               component=self.name(),
                               component_tag=component_tag,
                               dependencies_tag=dependencies_tag)

    def _get_resource_dir(self, global_resource_path: Path) -> Path:
        return global_resource_path / self.name()
