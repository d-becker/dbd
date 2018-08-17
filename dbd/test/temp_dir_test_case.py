#!/usr/bin/env python3

"""
This module contains a base class for test cases that use a temporary directory.
"""

from pathlib import Path

import tempfile
import unittest

class TmpDirTestCase(unittest.TestCase):
    """
    A base class for test that use a temporary directory.
    """

    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_dir_path = Path(self._tmp_dir.name)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()
