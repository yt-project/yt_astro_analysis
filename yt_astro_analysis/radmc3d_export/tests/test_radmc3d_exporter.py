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
import shutil
import tempfile

import numpy as np

import yt
from yt.testing import assert_allclose
from yt.utilities.answer_testing.framework import AnswerTestingTest, requires_ds
from yt_astro_analysis.radmc3d_export.api import RadMC3DWriter


class RadMC3DValuesTest(AnswerTestingTest):
    """

    This test writes out a "dust_density.inp" file,
    reads it back in, and checks the sum of the
    values for degradation.

    """

    _type_name = "RadMC3DValuesTest"
    _attrs = ("field",)

    def __init__(self, ds_fn, field, decimals=10):
        super().__init__(ds_fn)
        self.field = field
        self.decimals = decimals

    def run(self):

        # Set up in a temp dir
        tmpdir = tempfile.mkdtemp()
        curdir = os.getcwd()
        os.chdir(tmpdir)

        # try to write the output files
        writer = RadMC3DWriter(self.ds)
        writer.write_amr_grid()
        writer.write_dust_file(self.field, "dust_density.inp")

        # compute the sum of the values in the resulting file
        total = 0.0
        with open("dust_density.inp") as f:
            for i, line in enumerate(f):

                # skip header
                if i < 3:
                    continue

                line = line.rstrip()
                total += np.float64(line)

        # clean up
        os.chdir(curdir)
        shutil.rmtree(tmpdir)

        return total

    def compare(self, new_result, old_result):
        err_msg = f"Total value for {self.field} not equal."
        assert_allclose(
            new_result,
            old_result,
            10.0 ** (-self.decimals),
            err_msg=err_msg,
            verbose=True,
        )


etiny = "enzo_tiny_cosmology/DD0046/DD0046"


@requires_ds(etiny)
def test_radmc3d_exporter_continuum():
    """
    This test is simply following the description in the docs for how to
    generate the necessary output files to run a continuum emission map from
    dust for one of our sample datasets.
    """

    ds = yt.load(etiny)

    # Make up a dust density field where dust density is 1% of gas density
    dust_to_gas = 0.01

    def _DustDensity(field, data):
        return dust_to_gas * data["density"]

    ds.add_field(
        ("gas", "dust_density"),
        function=_DustDensity,
        sampling_type="cell",
        units="g/cm**3",
    )

    yield RadMC3DValuesTest(ds, ("gas", "dust_density"))
