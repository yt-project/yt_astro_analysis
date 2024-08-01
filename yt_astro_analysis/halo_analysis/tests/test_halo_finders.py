import os
import sys

import pytest

from yt.frontends.halo_catalog.data_structures import YTHaloCatalogDataset
from yt.frontends.rockstar.data_structures import RockstarDataset
from yt.loaders import load
from yt.testing import assert_allclose_units, requires_file

_expected = {
    "fof": {
        ("halos", "particle_position_x"): (
            [0.5395228362545148, 0.009322612122839679, 0.9851068812956318],
            "unitary",
        ),
        ("halos", "particle_position_y"): (
            [0.5622196217878699, 0.003041142049505119, 0.9959844650128505],
            "unitary",
        ),
        ("halos", "particle_position_z"): (
            [0.5203774727457908, 0.0007079871575761398, 0.9990256781592326],
            "unitary",
        ),
        ("halos", "particle_mass"): (
            [5874503393478.599, 719586865542.6366, 46593249543885.67],
            "Msun",
        ),
    },
    "hop": {
        ("halos", "particle_position_x"): (
            [0.5541340411242247, 0.054537564738846515, 0.9874987118674894],
            "unitary",
        ),
        ("halos", "particle_position_y"): (
            [0.5230348494537058, 0.02430675276218758, 0.9654696366375637],
            "unitary",
        ),
        ("halos", "particle_position_z"): (
            [0.4661933399047146, 0.0049056915980563165, 0.9985715364094563],
            "unitary",
        ),
        ("halos", "particle_mass"): (
            [13744109131864.344, 4407469551448.649, 38677794022916.664],
            "Msun",
        ),
    },
    "rockstar": {
        ("halos", "particle_position_x"): (
            [16.706823560058094, 1.2783197164535522, 31.622468948364258],
            "Mpccm/h",
        ),
        ("halos", "particle_position_y"): (
            [16.977042329115946, 0.745559811592102, 31.82260513305664],
            "Mpccm/h",
        ),
        ("halos", "particle_position_z"): (
            [15.993848544652344, 0.15180185437202454, 31.95146942138672],
            "Mpccm/h",
        ),
        ("halos", "particle_mass"): (
            [5220228205450.492, 126287495168.0, 27593818505216.0],
            "Msun/h",
        ),
    },
}


methods = {"fof": 2, "hop": 2, "rockstar": 3}
decimals = {"fof": 10, "hop": 10, "rockstar": 1}

etiny = "enzo_tiny_cosmology/DD0046/DD0046"


@requires_file(etiny)
def test_halo_finders_single(tmp_path):
    pytest.importorskip("mpi4py")
    from mpi4py import MPI

    os.chdir(tmp_path)

    filename = os.path.join(os.path.dirname(__file__), "run_halo_finder.py")
    for method in methods:
        comm = MPI.COMM_SELF.Spawn(
            sys.executable,
            args=[filename, method, str(tmp_path)],
            maxprocs=methods[method],
        )
        comm.Disconnect()

        if method == "rockstar":
            hcfn = "halos_0.0.bin"
        else:
            hcfn = os.path.join("DD0046", "DD0046.0.h5")

        ds = load(tmp_path / "halo_catalogs" / method / hcfn)
        if method == "rockstar":
            ds.parameters["format_revision"] = 2
            ds_type = RockstarDataset
        else:
            ds_type = YTHaloCatalogDataset
        assert isinstance(ds, ds_type)

        expected_results = _expected[method]
        for field, expected in expected_results.items():
            obj = ds.all_data()
            field = obj._determine_fields(field)[0]
            weight_field = (field[0], "particle_ones")
            avg = obj.quantities.weighted_average_quantity(field, weight=weight_field)
            mi, ma = obj.quantities.extrema(field)

            expected_value, expected_units = expected
            assert_allclose_units(
                [avg, mi, ma],
                ds.arr(expected_value, expected_units),
                10.0 ** (-decimals[method]),
                err_msg=f"Field values for {field} not equal.",
                verbose=True,
            )
