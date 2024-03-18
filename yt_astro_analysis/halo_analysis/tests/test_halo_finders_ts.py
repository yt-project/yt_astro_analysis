import os
import sys

import pytest

import yt
from yt.frontends.halo_catalog.data_structures import YTHaloCatalogDataset
from yt.frontends.rockstar.data_structures import RockstarDataset
from yt.testing import requires_file

methods = {"fof": 2, "hop": 2, "rockstar": 3}
decimals = {"fof": 10, "hop": 10, "rockstar": 1}

etiny = "enzo_tiny_cosmology/32Mpc_32.enzo"


@requires_file(etiny)
def test_halo_finders(tmp_path):
    pytest.importorskip("mpi4py")
    from mpi4py import MPI

    os.chdir(tmp_path)

    filename = os.path.join(os.path.dirname(__file__), "run_halo_finder_ts.py")
    for method in methods:
        comm = MPI.COMM_SELF.Spawn(
            sys.executable,
            args=[filename, method, str(tmp_path)],
            maxprocs=methods[method],
        )
        comm.Disconnect()

        if method == "rockstar":
            hcfns = [f"halos_{i}.0.bin" for i in range(2)]
        else:
            hcfns = [os.path.join(f"DD{i:04d}", f"DD{i:04d}.0.h5") for i in [20, 46]]

        for hcfn in hcfns:
            ds = yt.load(tmp_path / "halo_catalogs" / method / hcfn)
            if method == "rockstar":
                ds.parameters["format_revision"] = 2
                ds_type = RockstarDataset
            else:
                ds_type = YTHaloCatalogDataset
            assert isinstance(ds, ds_type)
