"""
Tests for HOP and FOF halo finders.



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.convenience import \
    load
from yt.data_objects.particle_filters import \
    add_particle_filter
from yt_astro_analysis.halo_analysis.api import \
    HaloCatalog
from yt.testing import \
    requires_file, \
    assert_array_equal
from yt.utilities.answer_testing.framework import \
    data_dir_load

from yt_astro_analysis.utilities.testing import \
    TempDirTest

def dm(pfilter, data):
    return data["creation_time"] <= 0.
add_particle_filter("dm", dm, filtered_type='all',
                    requires=["creation_time"])

enzotiny = "enzo_tiny_cosmology/DD0046/DD0046"

class HaloFinderTest(TempDirTest):

    @requires_file(enzotiny)
    def test_halofinder_ptype(self):
        ds = data_dir_load(enzotiny)
        ds.add_particle_filter("dm")

        for method in ["fof", "hop"]:
            hc = HaloCatalog(data_ds=ds, finder_method=method,
                             output_dir="hc1",
                             finder_kwargs={"dm_only": True})
            hc.create()
            hc = HaloCatalog(data_ds=ds, finder_method=method,
                             output_dir="hc2",
                             finder_kwargs={"dm_only": False, "ptype": "dm"})
            hc.create()

            ds1 = load("hc1/hc1.0.h5")
            ds2 = load("hc2/hc2.0.h5")
            assert_array_equal(ds1.r["particle_mass"], ds2.r["particle_mass"])
