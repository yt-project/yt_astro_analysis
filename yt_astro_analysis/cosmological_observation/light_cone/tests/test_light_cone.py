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

import h5py
import numpy as np
import numpy.testing as npt
import pytest
import unyt as un

import yt  # noqa
from yt.testing import requires_file
from yt_astro_analysis.cosmological_observation.api import LightCone

ETC = "enzo_tiny_cosmology/32Mpc_32.enzo"
_funits = {
    "density": un.unyt_quantity(1, "g/cm**3"),
    "temperature": un.unyt_quantity(1, "K"),
    "length": un.unyt_quantity(1, "cm"),
}


@requires_file(ETC)
@pytest.mark.parametrize(
    "field, weight_field, expected",
    [
        (
            "density",
            None,
            [6.0000463633868075e-05, 1.1336502301470154e-05, 0.08970763360935877],
        ),
        (
            "temperature",
            "density",
            [37.79481498628398, 0.018410545597485613, 543702.4613479003],
        ),
    ],
)
def test_light_cone_projection(tmp_path, field, weight_field, expected):
    parameter_file = ETC
    simulation_type = "Enzo"
    field = field
    weight_field = weight_field

    os.chdir(tmp_path)
    lc = LightCone(
        parameter_file,
        simulation_type,
        near_redshift=0.0,
        far_redshift=0.1,
        observer_redshift=0.0,
        time_data=False,
    )
    lc.calculate_light_cone_solution(seed=123456789, filename="LC/solution.txt")
    lc.project_light_cone(
        (600.0, "arcmin"),
        (60.0, "arcsec"),
        field,
        weight_field=weight_field,
        save_stack=True,
    )

    dname = f"{field}_{weight_field}"
    with h5py.File("LC/LightCone.h5", mode="r") as fh:
        data = fh[dname][()]
        units = fh[dname].attrs["units"]
        if weight_field is None:
            punits = _funits[field] * _funits["length"]
        else:
            punits = _funits[field] * _funits[weight_field] * _funits["length"]
            wunits = fh[f"weight_field_{weight_field}"].attrs["units"]
            pwunits = _funits[weight_field] * _funits["length"]
            assert wunits == str(pwunits.units)
    assert units == str(punits.units)

    mean = np.nanmean(data)
    mi = np.nanmin(data[data.nonzero()])
    ma = np.nanmax(data)
    npt.assert_equal([mean, mi, ma], expected, verbose=True)
