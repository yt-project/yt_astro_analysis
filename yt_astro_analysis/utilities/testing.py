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
import warnings

import yt
from yt.config import ytcfg


def data_dir_load(fn, *args, **kwargs):
    # wrap yt.load but only load from test_data_dir
    path = os.path.join(ytcfg.get("yt", "test_data_dir"), fn)
    return yt.load(path, *args, **kwargs)


def requires_sim(sim_fn, sim_type, file_check=False):
    warnings.warn(
        "yt_astro_analysis.utilities.testing.requires_sim "
        "is deprecated and will be removed in a future version. "
        "Please consider implementing your own solution.",
        DeprecationWarning,
        stacklevel=2,
    )
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
    warnings.warn(
        "yt_astro_analysis.utilities.testing.can_run_sim "
        "is deprecated and will be removed in a future version. "
        "Please consider implementing your own solution.",
        DeprecationWarning,
        stacklevel=2,
    )
    from yt.data_objects.time_series import SimulationTimeSeries
    from yt.loaders import load_simulation
    from yt.utilities.answer_testing.framework import AnswerTestingTest

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
