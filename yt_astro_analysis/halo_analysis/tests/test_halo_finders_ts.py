import os
import sys

from yt.frontends.halo_catalog.data_structures import YTHaloCatalogDataset
from yt.frontends.rockstar.data_structures import RockstarDataset
from yt.loaders import load
from yt_astro_analysis.utilities.testing import TempDirTest

_fields = (
    ("halos", "particle_position_x"),
    ("halos", "particle_position_y"),
    ("halos", "particle_position_z"),
    ("halos", "particle_mass"),
)

methods = {"fof": 2, "hop": 2, "rockstar": 3}
decimals = {"fof": 10, "hop": 10, "rockstar": 1}

etiny = "enzo_tiny_cosmology/32Mpc_32.enzo"


class HaloFinderTimeSeriesTest(TempDirTest):
    def test_halo_finders(self):
        from mpi4py import MPI

        filename = os.path.join(os.path.dirname(__file__), "run_halo_finder_ts.py")
        for method in methods:
            comm = MPI.COMM_SELF.Spawn(
                sys.executable,
                args=[filename, method, self.tmpdir],
                maxprocs=methods[method],
            )
            comm.Disconnect()

            if method == "rockstar":
                hcfns = [f"halos_{i}.0.bin" for i in range(2)]
            else:
                hcfns = [
                    os.path.join(f"DD{i:04d}", f"DD{i:04d}.0.h5") for i in [20, 46]
                ]

            for hcfn in hcfns:
                fn = os.path.join(self.tmpdir, "halo_catalogs", method, hcfn)

                ds = load(fn)
                if method == "rockstar":
                    ds.parameters["format_revision"] = 2
                    ds_type = RockstarDataset
                else:
                    ds_type = YTHaloCatalogDataset
                assert isinstance(ds, ds_type)
