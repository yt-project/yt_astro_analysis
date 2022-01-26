"""
Operations to run Rockstar



"""

# -----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from unyt import unyt_quantity

from yt.config import ytcfg
from yt.data_objects.static_output import Dataset
from yt.data_objects.time_series import DatasetSeries
from yt.funcs import is_root, mylog
from yt.utilities.parallel_tools.parallel_analysis_interface import (
    ParallelAnalysisInterface,
    ProcessorPool,
)

try:
    from yt_astro_analysis.halo_analysis.halo_finding.rockstar import rockstar_interface
except ImportError:
    mylog.warning(
        "Cannot import the rockstar interface.  Rockstar will not run.\n"
        "If you need Rockstar, see the installation instructions at "
        "http://yt-astro-analysis.readthedocs.io/."
    )
    rockstar_interface = None

import os
import socket
import time

import numpy as np


class InlineRunner(ParallelAnalysisInterface):
    def __init__(self):
        # If this is being run inline, num_readers == comm.size, always.
        psize = ytcfg.get("yt", "internals", "global_parallel_size")
        self.num_readers = psize
        # No choice for you, everyone's a writer too!
        self.num_writers = psize

    def run(self, handler, pool):
        # If inline, we use forks.
        server_pid = 0
        # Start a server on only one machine/fork.
        if pool.comm.rank == 0:
            server_pid = os.fork()
            if server_pid == 0:
                handler.start_server()
                os._exit(0)
        # Start writers on all.
        writer_pid = 0
        time.sleep(0.05 + pool.comm.rank / 10.0)
        writer_pid = os.fork()
        if writer_pid == 0:
            handler.start_writer()
            os._exit(0)
        # Everyone's a reader!
        time.sleep(0.05 + pool.comm.rank / 10.0)
        handler.start_reader()
        # Make sure the forks are done, which they should be.
        if writer_pid != 0:
            os.waitpid(writer_pid, 0)
        if server_pid != 0:
            os.waitpid(server_pid, 0)

    def setup_pool(self):
        pool = ProcessorPool()
        # Everyone is a reader, and when we're inline, that's all that matters.
        readers = np.arange(ytcfg.get("yt", "internals", "global_parallel_size"))
        pool.add_workgroup(ranks=readers, name="readers")
        return pool, pool.workgroups[0]


class StandardRunner(ParallelAnalysisInterface):
    def __init__(self, num_readers, num_writers):
        self.num_readers = num_readers
        psize = ytcfg.get("yt", "internals", "global_parallel_size")
        if num_writers is None:
            self.num_writers = psize - num_readers - 1
        else:
            self.num_writers = min(num_writers, psize)
        if self.num_readers + self.num_writers + 1 != psize:
            raise RuntimeError(
                "The number of MPI processes (%i) does not equal the "
                "number of readers (%i) plus the number of writers "
                "(%i) plus 1 server" % (psize, self.num_readers, self.num_writers)
            )

    def run(self, handler, wg):
        # Not inline so we just launch them directly from our MPI threads.
        if wg.name == "server":
            handler.start_server()
        if wg.name == "readers":
            time.sleep(0.05)
            handler.start_reader()
        if wg.name == "writers":
            time.sleep(0.1)
            handler.start_writer()

    def setup_pool(self):
        pool = ProcessorPool()
        pool, workgroup = ProcessorPool.from_sizes(
            [
                (1, "server"),
                (self.num_readers, "readers"),
                (self.num_writers, "writers"),
            ]
        )
        return pool, workgroup


class RockstarHaloFinder(ParallelAnalysisInterface):
    r"""Spawns the Rockstar Halo finder, distributes particles and finds halos.

    Rockstar has three main processes: reader, writer, and the
    server which coordinates reader/writer processes.

    Parameters
    ----------
    ts : ~yt.data_objects.time_series.DatasetSeries, ~yt.data_objects.static_output.Dataset
        The dataset or datsets on which halo finding will be run. If you intend
        to make a merger tree later, you must run Rockstar using a DatasetSeries
        containing all the snapshot to be included.
    num_readers : int
        The number of reader can be increased from the default
        of 1 in the event that a single snapshot is split among
        many files. This can help in cases where performance is
        IO-limited. Default is 1. If run inline, it is
        equal to the number of MPI threads.
    num_writers : int
        The number of writers determines the number of processing threads
        as well as the number of threads writing output data.
        The default is set to comm.size-num_readers-1. If run inline,
        the default is equal to the number of MPI threads.
    outbase : str
        This is where the out*list files that Rockstar makes should be
        placed. Default is 'rockstar_halos'.
    particle_type : str
        This is the "particle type" that can be found in the data.  This can be
        a filtered particle or an inherent type.
    mass_field : optional, str
        The field to be used for the particle masses. The sampled field will be
        (<particle_type>, <mass_field>). This can be used to provide alternative
        particle masses for halo finding.
        Default: "particle_mass"
    star_types : str list/array
        The types (as returned by data((particle_type, particle_type)) to be
        recognized as star particles.
    force_res : float
        This parameter specifies the force resolution that Rockstar uses
        in units of Mpccm/h (comoving Mpc/h).
        If no value is provided, this parameter is automatically set to
        the width of the smallest grid element in the simulation from the
        last data snapshot (i.e. the one where time has evolved the
        longest) in the time series:
        ``ds_last.index.get_smallest_dx().to("Mpccm/h")``.
    initial_metric_scaling : float
        The position element of the fof distance metric is divided by this
        parameter, set to 1 by default. If the initial_metric_scaling=0.1 the
        position element will have 10 times more weight than the velocity element,
        biasing the metric towards position information more so than velocity
        information. That was found to be needed for hydro-ART simulations
        with 10's of parsecs resolution.
        Default: 1.0.
    non_dm_metric_scaling : float
        The metric scaling to be used for non-dm particles. The effect of
        this parameter is currently unknown.
        Default: 10.
    suppress_galaxies : int
        Wether to include non-dm halos (i.e. galaxies) in the catalogs. The effect
        of this parameter is currently unknown.
        Default: 1.
    total_particles : int
        If supplied, this is a pre-calculated total number of particles present
        in the simulation. For example, this is useful when analyzing a series
        of snapshots where the number of dark matter particles should not
        change and this will save some disk access time. If left unspecified,
        it will be calculated automatically. Default: ``None``.
    particle_mass : optional, None, float, tuple, or :class:`~unyt.array.unyt_quantity`
        If supplied, this mass will be used to calculate the average particle
        spacing used in the friend-of-friends algorithm. The particle spacing
        will be (particle_mass / omega_matter * rho_cr)^1/3. If None, the mass
        is set as the minimum of all particles to be read. If a float, units
        are assumed to be in Msun/h. If a tuple, the format is assume to be
        (<value>, <units>). If a :class:`~unyt.array.unyt_quantity`, it must
        be convertible to units of Msun/h. To modify the masses of particles
        used for halo finding, see the mass_field keyword.
        Default: ``None``.
    restart : optional, bool
        Set to True to have rockstar restart from the first uncompleted
        snapshot. If False, rockstar will start at the first snapshot in the
        simulation.
        Default: False

    Returns
    -------
    None

    Examples
    --------

    To use the script below you must run it using MPI:
    `mpirun -np 4 python run_rockstar.py`

    >>> import yt
    >>> yt.enable_parallelism()
    >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
    >>> data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
    >>> hc = HaloCatalog(data_ds=data_ds, finder_method='rockstar',
    ...                  finder_kwargs={"num_readers": 1, "num_writers": 2})
    >>> hc.create()

    """

    def __init__(
        self,
        ts,
        num_readers=1,
        num_writers=None,
        outbase="rockstar_halos",
        particle_type="all",
        mass_field="particle_mass",
        star_types=None,
        force_res=None,
        initial_metric_scaling=1.0,
        non_dm_metric_scaling=10.0,
        suppress_galaxies=1,
        total_particles=None,
        dm_only=False,
        particle_mass=None,
        min_halo_size=25,
        restart=False,
    ):

        if is_root():
            mylog.info("The citation for the Rockstar halo finder can be found at")
            mylog.info("http://adsabs.harvard.edu/abs/2013ApJ...762..109B")
        ParallelAnalysisInterface.__init__(self)
        # Decide how we're working.
        if ytcfg.get("yt", "inline"):
            self.runner = InlineRunner()
        else:
            self.runner = StandardRunner(num_readers, num_writers)
        self.restart = restart
        self.num_readers = self.runner.num_readers
        self.num_writers = self.runner.num_writers
        mylog.info(
            "Rockstar is using %d readers and %d writers",
            self.num_readers,
            self.num_writers,
        )
        # Note that Rockstar does not support subvolumes.
        # We assume that all of the snapshots in the time series
        # use the same domain info as the first snapshots.
        if not isinstance(ts, DatasetSeries):
            ts = DatasetSeries([ts])
        self.ts = ts
        self.particle_type = particle_type
        if star_types is None:
            star_types = []
        self.star_types = star_types
        self.outbase = outbase
        self.min_halo_size = min_halo_size
        if force_res is None:
            tds = ts[-1]  # Cache a reference
            self.force_res = tds.index.get_smallest_dx().to("Mpccm/h")
            # We have to delete now to wipe the index
            del tds
        else:
            self.force_res = force_res
        self.initial_metric_scaling = initial_metric_scaling
        self.non_dm_metric_scaling = non_dm_metric_scaling
        self.suppress_galaxies = suppress_galaxies
        self.total_particles = total_particles
        self.dm_only = dm_only
        self.particle_mass = particle_mass
        self.mass_field = mass_field
        # Setup pool and workgroups.
        self.pool, self.workgroup = self.runner.setup_pool()
        p = self._setup_parameters(ts)
        params = self.comm.mpi_bcast(p, root=self.pool["readers"].ranks[0])
        self.__dict__.update(params)
        self.handler = rockstar_interface.RockstarInterface(self.ts)

    def _setup_parameters(self, ts):
        if self.workgroup.name != "readers":
            return None
        tds = ts[0]
        tds.index
        ptype = self.particle_type
        if ptype not in tds.particle_types and ptype != "all":
            has_particle_filter = tds.add_particle_filter(ptype)
            if not has_particle_filter:
                raise RuntimeError("Particle type (filter) %s not found." % (ptype))

        dd = tds.all_data()
        # Get DM particle mass.
        particle_mass = self.particle_mass
        if particle_mass is None:
            pmass_min, pmass_max = dd.quantities.extrema(
                (ptype, self.mass_field), non_zero=True
            )
            particle_mass = pmass_min
        elif isinstance(particle_mass, (tuple, list)) and len(particle_mass) == 2:
            particle_mass = tds.quan(*particle_mass)
        elif not isinstance(particle_mass, unyt_quantity):
            particle_mass = tds.quan(particle_mass, "Msun / h")
        particle_mass.convert_to_units("Msun / h")

        p = {}
        if self.total_particles is None:
            # Get total_particles in parallel.
            tp = dd.quantities.total_quantity((ptype, "particle_ones"))
            p["total_particles"] = int(tp)
            mylog.info("Total Particle Count: %d.", int(tp))
        p["left_edge"] = tds.domain_left_edge.in_units("Mpccm/h")
        p["right_edge"] = tds.domain_right_edge.in_units("Mpccm/h")
        p["center"] = tds.domain_center.in_units("Mpccm/h")
        p["particle_mass"] = self.particle_mass = particle_mass
        del tds
        return p

    def __del__(self):
        try:
            self.pool.free_all()
        except AttributeError:
            # This really only acts to cut down on the misleading
            # error messages when/if this class is called incorrectly
            # or some other error happens and self.pool hasn't been created
            # already.
            pass

    def _get_hosts(self):
        if self.comm.rank == 0 or self.comm.size == 1:

            # Temporary mac hostname fix
            try:
                server_address = socket.gethostname()
                socket.gethostbyname(server_address)
            except socket.gaierror:
                server_address = "localhost"

            sock = socket.socket()
            sock.bind(("", 0))
            port = sock.getsockname()[-1]
            del sock
        else:
            server_address, port = None, None
        self.server_address, self.port = self.comm.mpi_bcast((server_address, port))
        self.server_address = bytearray(str(self.server_address), "utf-8")
        self.port = bytearray(str(self.port), "utf-8")

    def run(self, block_ratio=1, callbacks=None, restart=False):
        """ """
        if block_ratio != 1:
            raise NotImplementedError
        self._get_hosts()
        # Find restart output number
        num_outputs = len(self.ts)
        restart = restart or self.restart
        if restart:
            restart_file = os.path.join(self.outbase, "restart.cfg")
            if not os.path.exists(restart_file):
                raise RuntimeError("Restart file %s not found" % (restart_file))
            with open(restart_file) as restart_fh:
                for par in restart_fh:
                    if par.startswith("RESTART_SNAP"):
                        restart_num = int(par.split("=")[1])
                    if par.startswith("NUM_WRITERS"):
                        num_writers = int(par.split("=")[1])
            if num_writers != self.num_writers:
                raise RuntimeError(
                    "Number of writers in restart has changed from the original "
                    "run (OLD = %d, NEW = %d).  To avoid problems in the "
                    "restart, choose the same number of writers."
                    % (num_writers, self.num_writers)
                )
            # Remove the datasets that were already analyzed
            self.ts._pre_outputs = self.ts._pre_outputs[restart_num:]
        else:
            restart_num = 0
        outbase = bytearray(self.outbase, "utf-8")
        self.handler.setup_rockstar(
            self.server_address,
            self.port,
            num_outputs,
            np.int64(self.total_particles),
            self.particle_type,
            self.mass_field,
            star_types=self.star_types,
            particle_mass=self.particle_mass,
            parallel=self.comm.size > 1,
            num_readers=self.num_readers,
            num_writers=self.num_writers,
            writing_port=-1,
            block_ratio=block_ratio,
            outbase=outbase,
            force_res=self.force_res,
            initial_metric_scaling=self.initial_metric_scaling,
            non_dm_metric_scaling=self.non_dm_metric_scaling,
            suppress_galaxies=self.suppress_galaxies,
            callbacks=callbacks,
            restart_num=restart_num,
            min_halo_size=self.min_halo_size,
        )
        # Make the directory to store the halo lists in.
        if not self.outbase:
            self.outbase = os.getcwd()
        if self.comm.rank == 0 and not restart:
            if not os.path.exists(self.outbase):
                os.makedirs(self.outbase)
            # Make a record of which dataset corresponds to which set of
            # output files because it will be easy to lose this connection.
            fp = open(os.path.join(self.outbase, "datasets.txt"), "w")
            fp.write("# dsname\tindex\n")
            for i, ds in enumerate(self.ts.outputs):
                if isinstance(ds, Dataset):
                    fn = ds.parameter_filename
                else:
                    fn = ds
                dsloc = os.path.join(os.path.relpath(fn))
                line = f"{dsloc}\t{i}\n"
                fp.write(line)
            fp.close()
        # This barrier makes sure the directory exists before it might be used.
        self.comm.barrier()
        if self.comm.size == 1:
            self.handler.call_rockstar()
        else:
            # And run it!
            self.runner.run(self.handler, self.workgroup)
        self.comm.barrier()
        self.pool.free_all()
