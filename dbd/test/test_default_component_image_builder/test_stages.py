#!/usr/bin/env python3

# pylint: disable=missing-docstring

from typing import cast, Any, Callable, Dict, List, Optional
from pathlib import Path

import docker

from default_component_image_builder.stages import (BuildDockerImageStage,
                                                    CreateTarfileStage,
                                                    Downloader,
                                                    DownloadFileStage)

from test.temp_dir_test_case import TmpDirTestCase

class TestCreateTarfileStage(TmpDirTestCase):
    def test_execute_creates_tarfile(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "file.tar.gz"

        stage = CreateTarfileStage("archive", source_dir)

        stage.execute(dest_path)

        self.assertTrue(dest_path.exists())

class TestDownloadFileStage(TmpDirTestCase):
    class MockDownloader(Downloader):
        def __init__(self) -> None:
            self._url: Optional[str] = None
            self._dest_path: Optional[Path] = None

        def download(self, url: str, dest_path: Path) -> None:
            self._url = url
            self._dest_path = dest_path
            dest_path.touch()

        def get_url(self) -> Optional[str]:
            return self._url

        def get_dest_path(self) -> Optional[Path]:
            return self._dest_path

    def test_execute_calls_downloader_with_correct_arguments(self) -> None:
        dest_path = self._tmp_dir_path / "file.tar.gz"
        self.assertTrue(dest_path.parent.exists())

        downloader = TestDownloadFileStage.MockDownloader()
        url = "www.something.com"
        stage = DownloadFileStage("archive", downloader, url)

        stage.execute(dest_path)

        self.assertEqual(url, downloader.get_url())

        called_dest_path_opt: Optional[Path] = downloader.get_dest_path()
        self.assertFalse(called_dest_path_opt is None)

        # It is safe to cast as we have just checked if it is None. This is needed by the typechecker.
        called_dest_path: Path = cast(Path, called_dest_path_opt)
        self.assertEqual(dest_path.expanduser().resolve(), called_dest_path.expanduser().resolve())

# The type checker (mypy) cannot handle the docker module, therefore it won't typecheck whether we pass a real
# docker.DockerClient object to methods. Therefore we don't need to wrap it in an interface.
class MockDockerClient:
    class Images:
        def __init__(self) -> None:
            self.called_args: Dict[Any, Any] = {}
            self.files_in_context: List[Path] = []
            self._images: List[str] = []

        def build(self, **kwargs: Dict[Any, Any]) -> None:
            self.called_args = kwargs

            if not isinstance(self.called_args["path"], str):
                raise ValueError("The path should be a string.")

            path = Path(self.called_args["path"])
            self.files_in_context = list(path.glob("**/*"))

        def get(self, image_name: str) -> None:
            if image_name not in self._images:
                raise docker.errors.ImageNotFound("Mocking docker client: the following image was not found: {}."
                                                  .format(image_name))

        def add_image(self, image_name: str) -> None:
            self._images.append(image_name)

    def __init__(self) -> None:
        self.images = MockDockerClient.Images()

class TestBuildDockerImageStage(TmpDirTestCase):
    @staticmethod
    def _populate_dir(directory: Path, files: List[Path]) -> None:
        for file in files:
            (directory / file).touch()

    def test_execute_calls_docker_client_with_correct_arguments(self) -> None:
        docker_client = MockDockerClient()

        build_context_resources = self._tmp_dir_path / "docker_context"
        build_context_resources.mkdir()
        files_in_build_context_resources = [Path("Dockerfile"), Path("file.tar.gz")]
        TestBuildDockerImageStage._populate_dir(build_context_resources, files_in_build_context_resources)

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {"component_a": "component_a_image_name",
                                             "component_b": "component_b_image_name"}

        input_file_name = "input_file.tar.gz"
        input_file = self._tmp_dir_path / input_file_name
        input_file.touch()

        stage = BuildDockerImageStage("docker",
                                      docker_client,
                                      image_name,
                                      dependency_images,
                                      build_context_resources)

        stage.execute(input_file)

        called_args = docker_client.images.called_args

        self.assertEqual(image_name, called_args["tag"])
        self.assertTrue(called_args["rm"])

        expected_buildargs = {"{}_IMAGE".format(component_name.upper()) : image_name
                              for (component_name, image_name) in dependency_images.items()}
        expected_buildargs["GENERATED_DIR"] = "generated"
        self.assertEqual(expected_buildargs, called_args["buildargs"])

        build_directory = Path(called_args["path"])
        files_in_build_directory: List[Path] = docker_client.images.files_in_context

        present_in_build_directory: Callable[[Path], bool] = lambda p: (build_directory / p) in files_in_build_directory
        self.assertTrue(all(map(present_in_build_directory, files_in_build_context_resources)))

        self.assertTrue((build_directory / "generated" / input_file.name) in files_in_build_directory)
