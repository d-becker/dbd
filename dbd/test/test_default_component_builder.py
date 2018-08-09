#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import tempfile
from typing import List
from pathlib import Path

from default_component_image_builder import DefaultComponentImageBuilder, StageListBuilder
from default_component_image_builder import CreateCacheStage
from stage import Stage

class TestCreateCacheStage(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_dir_path = Path(self._tmp_dir.name)

    def tearDown(self):
        self._tmp_dir.cleanup()
    
    def test_check_precondition_returns_false_when_parent_dir_does_not_exist(self):
        parent_dir = self._tmp_dir_path / "non/existent/directory/"
        self.assertFalse(parent_dir.exists())

        stage = CreateCacheStage(parent_dir)

        result = stage.check_precondition()
        self.assertFalse(result)

    def test_check_precondition_returns_true_when_parent_dir_exists(self):
        parent_dir = self._tmp_dir_path
        stage = CreateCacheStage(parent_dir)

        result = stage.check_precondition()
        self.assertTrue(result)

    def test_execute_creates_cache_directory(self):
        parent_dir = self._tmp_dir_path
        stage = CreateCacheStage(parent_dir)

        self.assertTrue(stage.check_precondition())
        stage.execute()
        cache_dir = parent_dir / "cache"
        self.assertTrue(cache_dir.exists())

    def test_execute_does_nothing_if_cache_directory_already_exists(self):
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
            
