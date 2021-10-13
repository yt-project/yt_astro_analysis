"""
testing utilities



"""

# -----------------------------------------------------------------------------
# Copyright (c) 2017, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import os
import shutil
import tempfile
from unittest import TestCase

from yt.config import ytcfg
from yt.data_objects.time_series import SimulationTimeSeries
from yt.loaders import load_simulation
from yt.utilities.answer_testing.framework import AnswerTestingTest


class TempDirTest(TestCase):
    """
    A test class that runs in a temporary directory and
    removes it afterward.
    """

    def setUp(self):
        self.curdir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.curdir)
        shutil.rmtree(self.tmpdir)


def requires_sim(sim_fn, sim_type, file_check=False):
    from functools import wraps

    from nose import SkipTest

    def ffalse(func):
        @wraps(func)
        def fskip(*args, **kwargs):
            raise SkipTest

        return fskip

    def ftrue(func):
        return func

    if not can_run_sim(sim_fn, sim_type, file_check):
        return ffalse
    else:
        return ftrue


def can_run_sim(sim_fn, sim_type, file_check=False):
    result_storage = AnswerTestingTest.result_storage
    if isinstance(sim_fn, SimulationTimeSeries):
        return result_storage is not None
    path = ytcfg.get("yt", "test_data_dir")
    if not os.path.isdir(path):
        return False
    if file_check:
        return os.path.isfile(os.path.join(path, sim_fn)) and result_storage is not None
    try:
        load_simulation(sim_fn, sim_type)
    except FileNotFoundError:
        if ytcfg.get("yt", "internals", "strict_requires"):
            if result_storage is not None:
                result_storage["tainted"] = True
            raise
        return False
    return result_storage is not None
