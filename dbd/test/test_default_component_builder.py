#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import tempfile
from typing import cast, Any, Dict, List, Optional
from pathlib import Path

import docker

from default_component_image_builder import DefaultComponentImageBuilder, StageListBuilder
from default_component_image_builder import BuildDockerImageStage, CreateCacheStage, CreateTarfileStage, Downloader, DownloadFileStage
from stage import Stage

class TmpDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_dir_path = Path(self._tmp_dir.name)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

class TestCreateCacheStage(TmpDirTestCase):
    def test_check_precondition_returns_false_when_parent_dir_does_not_exist(self) -> None:
        parent_dir = self._tmp_dir_path / "non/existent/directory/"
        self.assertFalse(parent_dir.exists())

        stage = CreateCacheStage(parent_dir)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_parent_dir_is_not_a_directory(self) -> None:
        parent_dir = self._tmp_dir_path / "file"
        parent_dir.touch()
        self.assertTrue(parent_dir.exists())

        stage = CreateCacheStage(parent_dir)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_parent_dir_exists(self) -> None:
        parent_dir = self._tmp_dir_path
        stage = CreateCacheStage(parent_dir)

        result = stage.check_precondition()
        self.assertTrue(result)

    def test_execute_creates_cache_directory(self) -> None:
        parent_dir = self._tmp_dir_path
        stage = CreateCacheStage(parent_dir)

        self.assertTrue(stage.check_precondition())
        stage.execute()
        cache_dir = parent_dir / "cache"
        self.assertTrue(cache_dir.exists())

    def test_execute_does_nothing_if_cache_directory_already_exists(self) -> None:
        parent_dir = self._tmp_dir_path

        cache_dir = parent_dir / "cache"
        cache_dir.mkdir()

        file_in_cache = cache_dir / "file"
        file_in_cache.touch()

        stage = CreateCacheStage(parent_dir)

        self.assertTrue(stage.check_precondition())
        stage.execute()

        self.assertTrue(cache_dir.exists())
        self.assertTrue(file_in_cache.exists())

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

    def test_check_precondition_returns_false_when_dest_path_prefix_does_not_exist(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "non/existent/directory/file.tar.gz"
        self.assertFalse(dest_path.parent.exists())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_dest_path_prefix_is_not_a_directory(self) -> None:
        source_dir = self._tmp_dir_path / "source"
        source_dir.mkdir()
        self.assertTrue(source_dir.exists())

        dest_path = self._tmp_dir_path / "dest/file.tar.gz"
        dest_path.parent.touch()
        self.assertTrue(dest_path.parent.exists())
        self.assertFalse(dest_path.parent.is_dir())

        stage = CreateTarfileStage(source_dir, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

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

class TestDownloadFileStage(TmpDirTestCase):
    class MockDownloader(Downloader):
        def __init__(self) -> None:
            self._url: Optional[str] = None
            self._dest_path: Optional[Path] = None

        def download(self, url: str, dest_path: Path) -> None:
            self._url = url
            self._dest_path = dest_path

        def get_url(self) -> Optional[str]:
            return self._url

        def get_dest_path(self) -> Optional[Path]:
            return self._dest_path

    def test_check_precondition_returns_false_when_dest_path_prefix_does_not_exist(self) -> None:
        dest_path = self._tmp_dir_path / "non/existent/directory/file.tar.gz"
        self.assertFalse(dest_path.parent.exists())

        downloader = TestDownloadFileStage.MockDownloader()
        url = "www.something.com"
        stage = DownloadFileStage(downloader, url, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_dest_path_prefix_is_not_a_directory(self) -> None:
        dest_path = self._tmp_dir_path / "dest/file.tar.gz"
        dest_path.parent.touch()
        self.assertTrue(dest_path.parent.exists())
        self.assertFalse(dest_path.parent.is_dir())

        downloader = TestDownloadFileStage.MockDownloader()
        url = "www.something.com"
        stage = DownloadFileStage(downloader, url, dest_path)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_dest_path_prefix_exists(self) -> None:
        dest_path = self._tmp_dir_path / "file.tar.gz"
        self.assertTrue(dest_path.parent.exists())

        downloader = TestDownloadFileStage.MockDownloader()
        url = "www.something.com"
        stage = DownloadFileStage(downloader, url, dest_path)

        result = stage.check_precondition()
        self.assertTrue(result)

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

class TestBuildDockerImageStage(TmpDirTestCase):
    class MockDockerClient:
        class Images:
            def build(self, **kwargs: Dict[Any, Any]) -> None:
                self.called_args = kwargs
        
        def __init__(self) -> None:
            self.images = TestBuildDockerImageStage.MockDockerClient.Images()
        

    def test_check_precondition_returns_false_when_build_directory_does_not_exist(self) -> None:
        docker_client = TestBuildDockerImageStage.MockDockerClient()
        
        build_directory = self._tmp_dir_path / "non/existent/directory"
        self.assertFalse(build_directory.exists())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        file_dependencies: List[str] = []
        
        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_build_directory_is_not_a_directory(self) -> None:
        docker_client = TestBuildDockerImageStage.MockDockerClient()
        
        build_directory = self._tmp_dir_path / "file"
        build_directory.touch()
        self.assertTrue(build_directory.exists())
        self.assertFalse(build_directory.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        file_dependencies: List[str] = []

        # TODO: Check why mypy doesn't catch passing the mock docker client as that is not of the correct type.
        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_false_when_some_file_dependencies_do_not_exist(self) -> None:
        docker_client = TestBuildDockerImageStage.MockDockerClient()
        
        build_directory = self._tmp_dir_path / "directory"
        build_directory.mkdir()
        self.assertTrue(build_directory.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        
        file_dependencies: List[str] = ["some_file.txt", "another_file.tar.gz"]
        (build_directory / file_dependencies[0]).touch()

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_all_is_ok(self) -> None:
        docker_client = TestBuildDockerImageStage.MockDockerClient()
        
        build_directory = self._tmp_dir_path / "directory"
        build_directory.mkdir()
        self.assertTrue(build_directory.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {}
        
        file_dependencies: List[str] = ["some_file.txt", "another_file.tar.gz"]
        for file_dependency in file_dependencies:
            (build_directory / file_dependency).touch()

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

        result = stage.check_precondition()
        self.assertTrue(result)

    def test_execute_calls_docker_client_with_correct_arguments(self) -> None:
        docker_client = TestBuildDockerImageStage.MockDockerClient()
        
        build_directory = self._tmp_dir_path / "directory"
        build_directory.mkdir()
        self.assertTrue(build_directory.is_dir())

        image_name = "some_image_name"
        dependency_images: Dict[str, str] = {"component_a": "component_a_image_name",
                                             "component_b": "component_b_image_name"}
        
        file_dependencies: List[str] = []

        stage = BuildDockerImageStage(docker_client, image_name, dependency_images, build_directory, file_dependencies)

        self.assertTrue(stage.check_precondition())

        stage.execute()

        called_args = docker_client.images.called_args
        
        self.assertEqual(str(build_directory), called_args["path"])
        self.assertEqual(image_name, called_args["tag"])
        self.assertTrue(called_args["rm"])

        expected_buildargs = {"{}_IMAGE".format(component_name.upper()) : image_name
                              for (component_name, image_name) in dependency_images.items()}
        self.assertEqual(expected_buildargs, called_args["buildargs"])
