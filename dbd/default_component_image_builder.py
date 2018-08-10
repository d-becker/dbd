#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from pathlib import Path

import re
import tarfile

from typing import Dict, List, Optional, Tuple

import docker
import wget

from component_builder import ComponentConfig, ComponentImageBuilder, Configuration, DistType
from stage import Stage, StageChain

class CreateCacheStage(Stage):
    """
    A stage that creates a cache directory.

    Its precondition is that the directory in which the cache directory should be created needs to exist.

    If the cache directory already exists, executing this stage does nothing.
    """

    def __init__(self, parent_dir: Path) -> None:
        """
        Creates a `CreateCacheStage` object.

        Args:
            parent_dir: The directory in which to create the cache directory.

        """

        self._parent_dir = parent_dir.expanduser().resolve()
        self._cache_dir = self._parent_dir / "cache"

    def name(self) -> str:
        return "create_cache"

    def check_precondition(self) -> bool:
        return self._parent_dir.is_dir()

    def execute(self) -> None:
        self._cache_dir.mkdir(exist_ok=True)

class CreateTarfileStage(Stage):
    """
    A stage that takes a directory and creates a tar archive from it.

    Its precondition is that the source and the destination directories must exist.

    If the target file already exists, it is overwritten.
    """

    def __init__(self, source_dir: Path, dest_path: Path) -> None:
        """
        Creates a `CreateTarfileStage` object.

        Args:
            source_dir: The directory that is to be archived.
            dest_path: The path of the archive file to be created.
        """

        self._source_dir = source_dir.expanduser().resolve()
        self._dest_path = dest_path.expanduser().resolve()

    def name(self) -> str:
        return "create_tarfile"

    def check_precondition(self) -> bool:
        return self._source_dir.is_dir() and self._dest_path.parent.is_dir()

    def execute(self) -> None:
        with tarfile.open(self._dest_path, "w:gz") as tar:
            tar.add(str(self._source_dir), arcname=self._source_dir.name)

class Downloader(metaclass=ABCMeta):
    """
    An interface for classes that can download files from url's.
    """

    @abstractmethod
    def download(self, url: str, dest_path: Path) -> None:
        """
        Downloads a the file pointed to by the url to the destination pointed by `dest_path`.

        Args:
            url: The url of the file to download.
            dest_path: The path to which the file is to be downloaded.

        """

        pass

class DownloadFileStage(Stage):
    """
    A stage that downloads a file from a url.

    Its precondition is that the destination directory needs to exist.

    If the target file already exists, it is overwritten.

    If the url is invalid or downloading the file fails, the stage fails, too.
    """

    def __init__(self, downloader: Downloader, url: str, dest_path: Path) -> None:
        """
        Creates a `DownloadFileStage` object.

        Args:
            downloader: A `Downloader` object that will be used to download the file.
            url: The url of the file to download.
            dest_path: The path to which the file is to be downloaded.

        """

        self._downloader = downloader
        self._url = url
        self._dest_path = dest_path.expanduser().resolve()

    def name(self) -> str:
        return "download_file"

    def check_precondition(self) -> bool:
        return self._dest_path.parent.is_dir()

    def execute(self) -> None:
        self._downloader.download(self._url, self._dest_path)

class BuildDockerImageStage(Stage):
    """
    A stage that builds a docker image.

    Its precondition is that the provided build directory needs to exist and all of the provided file dependencies need
    to exist inside it.
    """

    def __init__(self,
                 docker_client: docker.DockerClient,
                 image_name: str,
                 dependency_images: Dict[str, str],
                 build_directory: Path,
                 file_dependencies: List[str]) -> None:
        """
        Created a `BuildDockerImageStage` object.

        Args:
            docker_client: The docker client object to use when building the image.
            image_name: The name that the built docker image should have.
            dependency_images: A dictionary where the names of the components that the current component
                depends on are the keys and those components' docker images' names are the values.
            build_directory: The directory where the Dockerfile and the other
                resources needed to build the docker image are located.
            file_dependencies: A list of filenames that must exist in the
                `build_directory` before the stage can be executed.

        """

        self._docker_client = docker_client
        self._image_name = image_name
        self._dependency_images = dependency_images
        self._build_directory = build_directory
        self._file_dependencies = file_dependencies

    def name(self) -> str:
        return "build_docker_image"

    def check_precondition(self) -> bool:
        if not self._build_directory.is_dir():
            return False

        for dep_file in self._file_dependencies:
            if not (self._build_directory / dep_file).exists():
                return False

        return True

    def execute(self) -> None:
        buildargs = {"{}_IMAGE".format(component.upper()) : image
                     for (component, image) in self._dependency_images.items()}

        self._docker_client.images.build(path=str(self._build_directory),
                                         buildargs=buildargs,
                                         tag=self._image_name,
                                         rm=True)

class ImageBuiltStage(Stage):
    def __init__(self, docker_client: docker.DockerClient, image_name: str) -> None:
        self._docker_client = docker_client
        self._image_name = image_name

    def name(self) -> str:
        return "image_built"

    def check_precondition(self) -> bool:
        try:
            self._docker_client.images.get(self._image_name)
        except docker.errors.ImageNotFound:
            return False
        else:
            return True

    def execute(self) -> None:
        pass

class StageListBuilder(metaclass=ABCMeta):
    """
    An interface for classes that build lists of `Stage` objects according to the provided configuration.
    """

    @abstractmethod
    def build_stage_list(self,
                         docker_client: docker.DockerClient,
                         component_name: str,
                         image_name: str,
                         url_template: str,
                         dependencies: List[str],
                         file_dependencies: List[str],
                         component_config: Dict[str, str],
                         built_config: Configuration) -> List[Stage]:
        """
        Builds and returns a list of `Stage` objects according to the provided configration.

        Args:
            component_config: A dictionary that contains (usually user-provided)
                configuration information about the component.
            built_config: A `Configuration` object that contains information about
                previously built components and images. This should never be modified.

        """

        pass

class DefaultDownloader(Downloader):
   def download(self, url: str, dest_path: Path) -> None:
       wget.download(url, out=str(dest_path))
    
class DefaultStageListBuilder(StageListBuilder):
    def build_stage_list(self,
                         docker_client: docker.DockerClient,
                         component_name: str,
                         image_name: str,
                         url_template: str,
                         dependencies: List[str],
                         file_dependencies: List[str],
                         component_config: Dict[str, str],
                         built_config: Configuration) -> List[Stage]:
        # TODO: Change directories to enable meaningful caching.
        resource_dir = built_config.resource_path / component_name
        cache_dir = resource_dir / "cache"
        (dist_type, argument) = dist_type_and_arg(component_config)
        archive_dest_path = cache_dir / "{}.tar.gz".format(component_name)

        stage_list: List[Stage] = [
            self._create_cache_stage(resource_dir),
            self._archive_retrieval_stage(archive_dest_path, dist_type, argument, url_template),
            self._build_docker_image_stage(docker_client, image_name,
                                           resource_dir, dependencies,
                                           built_config.components, file_dependencies),
            ImageBuiltStage(docker_client, image_name)]

        return stage_list
        
    def _create_cache_stage(self, resource_dir: Path) -> Stage:
        return CreateCacheStage(resource_dir)

    def _archive_retrieval_stage(self,
                                 archive_dest_path: Path,
                                 dist_type: DistType,
                                 argument: str,
                                 url_template: str) -> Stage:
        archive_retrieval_stage: Stage
        if dist_type == DistType.RELEASE:
            downloader = DefaultDownloader()
            version = argument
            url = url_template.format(version)
            return DownloadFileStage(downloader, url, archive_dest_path)
        elif dist_type == DistType.SNAPSHOT:
            source_dir = Path(argument)
            return CreateTarfileStage(source_dir, archive_dest_path)
        else:
            raise ValueError("Unexpected DistType value.")

    def _build_docker_image_stage(self,
                                  docker_client: docker.DockerClient,
                                  image_name: str,
                                  build_directory: Path,
                                  dependencies: List[str],
                                  component_configs: Dict[str, ComponentConfig],
                                  file_dependencies: List[str]) -> Stage:
        dependency_images = {dependency : component_configs[dependency].image_name for dependency in dependencies}

        return BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

class DefaultComponentImageBuilder(ComponentImageBuilder):
    # TODO: Add more information to the docstring about how the images are built (using stages) and how it can be
    # customised (for example by adding stages through providing a different stage_list_builder).

    """
    A class that implements the common functionality that is needed to implement the `ComponentImageBuilder`
    interface. The constructor parameters make it possible to customise the behaviour to fit the actual component.

    """

    def __init__(self,
                 component_name: str,
                 dependencies: List[str],
                 file_dependencies: List[str],
                 url_template: str,
                 version_command: str,
                 version_regex: str,
                 stage_list_builder: StageListBuilder) -> None:
        self._name = component_name
        self._dependencies = dependencies
        self._file_dependencies = file_dependencies
        self._url_template = url_template # A string with {0} which will be formatted with the version.
        self._version_command = version_command
        self._version_regex = version_regex
        self._stage_list_builder = stage_list_builder

        self._docker_client = docker.from_env()

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List[str]:
        return self._dependencies

    def build(self,
              component_config: Dict[str, str],
              built_config: Configuration,
              force_rebuild: bool = False) -> ComponentConfig:
        (dist_type, argument) = dist_type_and_arg(component_config)
        image_name = self._get_image_name(dist_type,
                                          argument if dist_type == DistType.RELEASE else None,
                                          built_config)
        
        stages = self._stage_list_builder.build_stage_list(self._docker_client,
                                                           self.name(),
                                                           image_name,
                                                           self._url_template,
                                                           self.dependencies(),
                                                           self._file_dependencies,
                                                           component_config,
                                                           built_config)
        stage_executor = StageChain(stages)

        if force_rebuild:
            stage_executor.execute_in_order()
        else:
            stage_executor.execute_needed()

        version: str
        if dist_type == DistType.RELEASE:
            version = argument
        else:
            version = find_out_version_from_image(self._docker_client,
                                                  image_name,
                                                  self.name(),
                                                  self._version_command,
                                                  self._version_regex)

        return ComponentConfig(dist_type, version, image_name)

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


def dist_type_and_arg(component_config: Dict[str, str]) -> Tuple[DistType, str]:
        """
        Returns the distribution type (release or snapshot) and the corresponding argument
        (version or path to snapshot buid) from a component configuration dictionary.

        Args:
            component_config: A dictionary containing information about a component.

        Returns:
            The distribution type (release or snapshot) and the corresponding argument (version or path to snapshot buid).

        """

        release_specified = "release" in component_config
        snapshot_specified = "snapshot" in component_config

        if release_specified and snapshot_specified:
            raise ValueError("Both release and snapshot mode specified.")

        if not release_specified and not snapshot_specified:
            raise ValueError("None of release and snapshot mode specified.")

        # pylint: disable=no-else-return
        if release_specified:
            version = component_config["release"]
            return (DistType.RELEASE, version)
        else:
            path = component_config["snapshot"]
            return (DistType.SNAPSHOT, path)

def find_out_version_from_image(docker_client: docker.DockerClient,
                                image_name: str,
                                component_name: str,
                                command: str,
                                regex: str) -> str:
    """
    Retrieves the version of a component from a docker image.

    Args:
        docker_client: The docker client object to use when starting the container.
        image_name: The name of the docker image from which the version should be retrieved.
        componenet_name: The name of the component the version of which should be retrieved.
        command: The command to run inside the docker container - the output should contain the version number.
        regex: A regular expression that will be matched against the output of `command` using the `re.search`
            function. Group 1 of the regex should catch the verion number string.
    Returns: The version number as a string.
    Raises: ValueError: If no match is found.

    """

    # Workaround: exit 0 is needed, otherwise the container exits with status 1 for some reason.
    command_to_use = "{} && exit 0".format(command)
    response_bytes = docker_client.containers.run(image_name, command_to_use, auto_remove=True)
    response = response_bytes.decode()

    match = re.search(regex, response)

    if match is None:
        raise ValueError("No {} version found.".format(component_name))

    version = match.group(1)
    return version
