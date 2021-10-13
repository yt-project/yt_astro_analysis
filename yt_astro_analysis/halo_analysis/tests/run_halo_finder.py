import os
import sys

from mpi4py import MPI

import yt
from yt.data_objects.particle_filters import particle_filter
from yt_astro_analysis.halo_analysis import HaloCatalog

yt.enable_parallelism()

method = sys.argv[1]
data_dir = sys.argv[2]
comm = MPI.Comm.Get_parent()

methods = {
    "fof": {"ptype": "dark_matter"},
    "hop": {"ptype": "dark_matter"},
    "rockstar": {"num_readers": 1, "num_writers": 1, "particle_type": "dark_matter"},
}


@particle_filter("dark_matter", requires=["creation_time"])
def _dm_filter(pfilter, data):
    return data[pfilter.filtered_type, "creation_time"] <= 0.0


ds = yt.load("enzo_tiny_cosmology/DD0046/DD0046")
ds.add_particle_filter("dark_matter")

output_dir = os.path.join(data_dir, "halo_catalogs", method)
hc = HaloCatalog(
    data_ds=ds,
    output_dir=output_dir,
    finder_method=method,
    finder_kwargs=methods[method],
)
hc.create()

comm.Disconnect()
