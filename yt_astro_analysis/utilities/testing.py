"""
testing utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
import shutil
import tempfile
from unittest import \
    TestCase

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

def requires_sim(sim_fn, sim_type, big_data=False, file_check=False):
    from functools import wraps

    from nose import SkipTest

    def ffalse(func):
        @wraps(func)
        def fskip(*args, **kwargs):
            raise SkipTest

        return fskip

    def ftrue(func):
        return func

    if not run_big_data and big_data:
        return ffalse
    elif not can_run_sim(sim_fn, sim_type, file_check):
        return ffalse
    else:
        return ftrue
