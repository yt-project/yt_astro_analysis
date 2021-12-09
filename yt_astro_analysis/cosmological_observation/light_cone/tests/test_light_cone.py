"""
light cone generator test



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

import numpy as np

from yt.testing import assert_equal
from yt.units.yt_array import YTQuantity
from yt.utilities.answer_testing.framework import AnswerTestingTest
from yt.utilities.on_demand_imports import _h5py as h5py
from yt_astro_analysis.cosmological_observation.api import LightCone
from yt_astro_analysis.utilities.testing import requires_sim

ETC = "enzo_tiny_cosmology/32Mpc_32.enzo"
_funits = {
    "density": YTQuantity(1, "g/cm**3"),
    "temperature": YTQuantity(1, "K"),
    "length": YTQuantity(1, "cm"),
}


class LightConeProjectionTest(AnswerTestingTest):
    _type_name = "LightConeProjection"
    _attrs = ()

    def __init__(self, parameter_file, simulation_type, field, weight_field=None):
        self.parameter_file = parameter_file
        self.simulation_type = simulation_type
        self.ds = os.path.basename(self.parameter_file)
        self.field = field
        self.weight_field = weight_field

    @property
    def storage_name(self):
        return "_".join(
            (os.path.basename(self.parameter_file), self.field, str(self.weight_field))
        )

    def run(self):
        # Set up in a temp dir
        tmpdir = tempfile.mkdtemp()
        curdir = os.getcwd()
        os.chdir(tmpdir)

        lc = LightCone(
            self.parameter_file,
            self.simulation_type,
            0.0,
            0.1,
            observer_redshift=0.0,
            time_data=False,
        )
        lc.calculate_light_cone_solution(seed=123456789, filename="LC/solution.txt")
        lc.project_light_cone(
            (600.0, "arcmin"),
            (60.0, "arcsec"),
            self.field,
            weight_field=self.weight_field,
            save_stack=True,
        )

        dname = f"{self.field}_{self.weight_field}"
        fh = h5py.File("LC/LightCone.h5", mode="r")
        data = fh[dname][()]
        units = fh[dname].attrs["units"]
        if self.weight_field is None:
            punits = _funits[self.field] * _funits["length"]
        else:
            punits = (
                _funits[self.field] * _funits[self.weight_field] * _funits["length"]
            )
            wunits = fh["weight_field_%s" % self.weight_field].attrs["units"]
            pwunits = _funits[self.weight_field] * _funits["length"]
            assert wunits == str(pwunits.units)
        assert units == str(punits.units)
        fh.close()

        # clean up
        os.chdir(curdir)
        shutil.rmtree(tmpdir)

        mean = data.mean()
        mi = data[data.nonzero()].min()
        ma = data.max()
        return np.array([mean, mi, ma])

    def compare(self, new_result, old_result):
        assert_equal(new_result, old_result, verbose=True)


@requires_sim(ETC, "Enzo")
def test_light_cone_projection():
    yield LightConeProjectionTest(ETC, "Enzo", "density")
    yield LightConeProjectionTest(ETC, "Enzo", "temperature", weight_field="density")
