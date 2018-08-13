#!/usr/bin/env python3

from pathlib import Path

import tempfile
import unittest

class TmpDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_dir_path = Path(self._tmp_dir.name)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()
