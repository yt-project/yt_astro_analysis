"""
Unit test for the RADMC3D Exporter analysis module
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import os

import numpy as np
import numpy.testing as npt

from yt.testing import requires_file
from yt_astro_analysis.radmc3d_export.api import RadMC3DWriter
from yt_astro_analysis.utilities.testing import data_dir_load

etiny = "enzo_tiny_cosmology/DD0046/DD0046"


@requires_file(etiny)
def test_radmc3d_exporter_continuum(tmp_path):
    """
    This test is simply following the description in the docs for how to
    generate the necessary output files to run a continuum emission map from
    dust for one of our sample datasets.
    """
    os.chdir(tmp_path)

    field = ("gas", "dust_density")
    ds = data_dir_load(etiny)

    # Make up a dust density field where dust density is 1% of gas density
    dust_to_gas = 0.01

    def _DustDensity(field, data):
        return dust_to_gas * data["density"]

    ds.add_field(
        field,
        function=_DustDensity,
        sampling_type="cell",
        units="g/cm**3",
    )

    # try to write the output files
    writer = RadMC3DWriter(ds)
    writer.write_amr_grid()
    writer.write_dust_file(field, "dust_density.inp")

    # compute the sum of the values in the resulting file
    total = 0.0
    with open("dust_density.inp") as f:
        for i, line in enumerate(f):
            # skip header
            if i < 3:
                continue

            line = line.rstrip()
            total += np.float64(line)

    npt.assert_allclose(
        total,
        4.240471916352974e-27,
        rtol=1e-10,
        err_msg=f"Total value for {field} not equal.",
        verbose=True,
    )
