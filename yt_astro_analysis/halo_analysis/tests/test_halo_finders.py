import os
import shutil
import sys
import tempfile

from yt.frontends.halo_catalog.data_structures import YTHaloCatalogDataset
from yt.frontends.rockstar.data_structures import RockstarDataset
from yt.loaders import load
from yt.utilities.answer_testing.framework import FieldValuesTest, requires_ds

_fields = (
    ("halos", "particle_position_x"),
    ("halos", "particle_position_y"),
    ("halos", "particle_position_z"),
    ("halos", "particle_mass"),
)

methods = {"fof": 2, "hop": 2, "rockstar": 3}
decimals = {"fof": 10, "hop": 10, "rockstar": 1}

etiny = "enzo_tiny_cosmology/DD0046/DD0046"


@requires_ds(etiny, big_data=True)
def test_halo_finders_single():
    from mpi4py import MPI

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    filename = os.path.join(os.path.dirname(__file__), "run_halo_finder.py")
    for method in methods:
        comm = MPI.COMM_SELF.Spawn(
            sys.executable, args=[filename, method, tmpdir], maxprocs=methods[method]
        )
        comm.Disconnect()

        if method == "rockstar":
            hcfn = "halos_0.0.bin"
        else:
            hcfn = os.path.join("DD0046", "DD0046.0.h5")
        fn = os.path.join(tmpdir, "halo_catalogs", method, hcfn)

        ds = load(fn)
        if method == "rockstar":
            ds.parameters["format_revision"] = 2
            ds_type = RockstarDataset
        else:
            ds_type = YTHaloCatalogDataset
        assert isinstance(ds, ds_type)

        for field in _fields:
            my_test = FieldValuesTest(
                ds, field, particle_type=True, decimals=decimals[method]
            )
            my_test.suffix = method
            yield my_test

    os.chdir(curdir)
    shutil.rmtree(tmpdir)
