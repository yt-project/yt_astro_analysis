"""
HaloCatalog answer tests



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import os
import shutil
import tempfile

from yt.analysis_modules.halo_analysis.api import \
    HaloCatalog, \
    add_quantity
from yt.convenience import \
    load
from yt.testing import \
    assert_equal
from yt.utilities.answer_testing.framework import \
    AnswerTestingTest, \
    data_dir_load, \
    requires_ds

def _nstars(halo):
    sp = halo.data_object
    return (sp["all", "creation_time"] > 0).sum()
add_quantity("nstars", _nstars)

class HaloQuantityTest(AnswerTestingTest):
    _type_name = "HaloQuantity"
    _attrs = ()

<<<<<<< HEAD
    def __init__(self, data_ds_fn, halos_ds_fn):
        self.data_ds_fn = data_ds_fn
        self.halos_ds_fn = halos_ds_fn
        self.ds = data_dir_load(data_ds_fn)
=======
    def __init__(self, data_ds, halos_ds):
        self.data_ds = data_dir_load(data_ds)
        self.halos_ds = data_dir_load(halos_ds)
        self.ds = data_ds
>>>>>>> d04a35d0a... Adding halo quantity test.

    def run(self):
        curdir = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        os.chdir(tmpdir)

<<<<<<< HEAD
        dds = data_dir_load(self.data_ds_fn)
        hds = data_dir_load(self.halos_ds_fn)
        hc = HaloCatalog(
            data_ds=dds, halos_ds=hds,
            output_dir=os.path.join(tmpdir, str(dds)))
=======
        hc = HaloCatalog(
            data_ds=self.data_ds, halos_ds=self.halos_ds,
            output_dir=os.path.join(tmpdir, str(self.data_ds)))
>>>>>>> d04a35d0a... Adding halo quantity test.
        hc.add_callback("sphere")
        hc.add_quantity("nstars")
        hc.create()

<<<<<<< HEAD
        fn = os.path.join(tmpdir, str(dds),
                          "%s.0.h5" % str(dds))
=======
        fn = os.path.join(tmpdir, str(self.data_ds),
                          "%s.0.h5" % str(self.data_ds))
>>>>>>> d04a35d0a... Adding halo quantity test.
        ds = load(fn)
        ad = ds.all_data()
        mi, ma = ad.quantities.extrema("nstars")
        mean = ad.quantities.weighted_average_quantity(
            "nstars", "particle_ones")

        os.chdir(curdir)
        shutil.rmtree(tmpdir)
    
        return np.array([mean, mi, ma])

    def compare(self, new_result, old_result):
        assert_equal(new_result, old_result, verbose=True)

rh0 = "rockstar_halos/halos_0.0.bin"
e64 = "Enzo_64/DD0043/data0043"

@requires_ds(rh0)
@requires_ds(e64)
def test_halo_quantity():
<<<<<<< HEAD
    yield HaloQuantityTest(e64, rh0)
=======
    hds = data_dir_load(rh0)
    dds = data_dir_load(e64)
    yield HaloQuantityTest(dds, hds)
>>>>>>> d04a35d0a... Adding halo quantity test.
