#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

from typing import cast, Any, Dict, List, Optional
from pathlib import Path

import docker

from default_component_image_builder.stages import (BuildDockerImageStage,
                                                    CreateTarfileStage, Downloader,
                                                    DownloadFileStage, ImageBuiltStage)

from test.temp_dir_test_case import TmpDirTestCase

class TestCreateTarfileStage(TmpDirTestCase):
    def test_check_precondition_returns_false_when_source_dir_does_not_exist(self) -> None:
        source_dir = self._tmp_dir_path / "non/existent/directory/"
        self.assertFalse(source_dir.exists())

        dest_path = self._tmp_dir_path / "file.tar.gz"
        self.assertTrue(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_source_dir_is_not_a_directory(self) -> None:
        source_dir = self._tmp_dir_path / "source_file"
        source_dir.touch()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "file.tar.gz"
        self.assertTrue(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_dest_path_prefix_does_not_exist(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "non/existent/directory/file.tar.gz"
        self.assertFalse(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertTrue(result)

    def test_check_precondition_returns_true_when_all_is_ok(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "file.tar.gz"
        self.assertTrue(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertTrue(result)

    def test_execute_creates_tarfile(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "file.tar.gz"

        stage = CreateTarfileStage(source_dir, dest_path)

        self.assertTrue(stage.check_precondition())
        stage.execute()

        self.assertTrue(dest_path.exists())

    def test_execute_creates_missing_parents(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "non/existent/directory/file.tar.gz"
        self.assertFalse(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        self.assertTrue(stage.check_precondition())
        stage.execute()

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
        stage = DownloadFileStage(downloader, url, dest_path)

        self.assertTrue(stage.check_precondition())
        stage.execute()

        self.assertEqual(url, downloader.get_url())

        called_dest_path_opt: Optional[Path] = downloader.get_dest_path()
        self.assertFalse(called_dest_path_opt is None)

        # It is safe to cast as we have just checked if it is None. This is needed by the typechecker.
        called_dest_path: Path = cast(Path, called_dest_path_opt)
        self.assertEqual(dest_path.expanduser().resolve(), called_dest_path.expanduser().resolve())

    def test_execute_creates_missing_parents(self) -> None:
        dest_path = self._tmp_dir_path / "some/directory/file.tar.gz"
        self.assertFalse(dest_path.parent.exists())

        downloader = TestDownloadFileStage.MockDownloader()
        url = "www.something.com"
        stage = DownloadFileStage(downloader, url, dest_path)

        stage.execute()

        self.assertTrue(dest_path.exists())

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
    def test_check_precondition_returns_false_when_build_directory_does_not_exist(self) -> None:
        docker_client = MockDockerClient()

        build_context = self._tmp_dir_path / "non/existent/directory"
        self.assertFalse(build_context.exists())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        file_dependencies: List[Path] = []

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_context, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_build_directory_is_not_a_directory(self) -> None:
        docker_client = MockDockerClient()

        build_context = self._tmp_dir_path / "file"
        build_context.touch()
        self.assertTrue(build_context.exists())
        self.assertFalse(build_context.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        file_dependencies: List[Path] = []

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_context, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_some_file_dependencies_do_not_exist(self) -> None:
        docker_client = MockDockerClient()

        build_context = self._tmp_dir_path / "directory"
        build_context.mkdir()
        self.assertTrue(build_context.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}

        file_dependencies: List[Path] = [build_context / "some_file.txt",
                                         build_context / "another_file.tar.gz"]
        file_dependencies[0].touch()

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_context, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_all_is_ok(self) -> None:
        docker_client = MockDockerClient()

        build_context = self._tmp_dir_path / "directory"
        build_context.mkdir()
        self.assertTrue(build_context.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}

        file_dependencies: List[Path] = [build_context / "some_file.txt",
                                         build_context / "another_file.tar.gz"]
        for file_dependency in file_dependencies:
            file_dependency.touch()

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_context, file_dependencies)

        result = stage.check_precondition()
        self.assertTrue(result)

    @staticmethod
    def _populate_dir(directory: Path, files: List[Path]) -> None:
        for file in files:
            (directory / file).touch()

    def test_execute_calls_docker_client_with_correct_arguments(self) -> None:
        docker_client = MockDockerClient()

        static_build_context = self._tmp_dir_path / "docker_context"
        static_build_context.mkdir()
        files_in_static_build_context = [Path("Dockerfile"), Path("file.tar.gz")]
        TestBuildDockerImageStage._populate_dir(static_build_context, files_in_static_build_context)

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {"component_a": "component_a_image_name",
                                             "component_b": "component_b_image_name"}

        generated_dir = self._tmp_dir_path / "generated"
        generated_dir.mkdir()
        file_dependencies: List[Path] = [Path("file_dep1.txt"), Path("file_dep2.txt")]
        TestBuildDockerImageStage._populate_dir(generated_dir, file_dependencies)

        stage = BuildDockerImageStage(docker_client,
                                      image_name,
                                      dependency_images,
                                      static_build_context,
                                      list(map(lambda p: generated_dir / p, file_dependencies)))

        self.assertTrue(stage.check_precondition())

        stage.execute()

        called_args = docker_client.images.called_args

        self.assertEqual(image_name, called_args["tag"])
        self.assertTrue(called_args["rm"])

        expected_buildargs = {"{}_IMAGE".format(component_name.upper()) : image_name
                              for (component_name, image_name) in dependency_images.items()}
        expected_buildargs["GENERATED_DIR"] = "generated"
        self.assertEqual(expected_buildargs, called_args["buildargs"])

        real_context = Path(called_args["path"])
        files_in_real_context: List[Path] = docker_client.images.files_in_context

        # TODO: make it more readable.
        self.assertTrue(all(map(lambda p: (real_context / p) in files_in_real_context,
                                files_in_static_build_context)))
        self.assertTrue(all(map(lambda p: (real_context / "generated" / p) in files_in_real_context,
                                file_dependencies)))

class TestImageBuiltStage(unittest.TestCase):
    def test_check_precondition_returns_false_when_image_does_not_exist(self) -> None:
        docker_client = MockDockerClient()
        image_name = "nonexistent_image"

        stage = ImageBuiltStage(docker_client, image_name)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_image_exists(self) -> None:
        docker_client = MockDockerClient()
        image_name = "existing_image"
        docker_client.images.add_image(image_name)

        stage = ImageBuiltStage(docker_client, image_name)

        result = stage.check_precondition()
        self.assertTrue(result)
