"""
halo finding



"""

# -----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import gc

import numpy as np

from yt.config import ytcfg
from yt.funcs import mylog
from yt.utilities.math_utils import get_rotation_matrix, periodic_dist
from yt.utilities.parallel_tools.parallel_analysis_interface import (
    ParallelAnalysisInterface,
)
from yt.utilities.physical_constants import mass_sun_cgs
from yt.utilities.physical_ratios import TINY, rho_crit_g_cm3_h2
from yt_astro_analysis.halo_analysis.halo_finding.fof.EnzoFOF import RunFOF
from yt_astro_analysis.halo_analysis.halo_finding.hop.EnzoHop import RunHOP


class Halo:
    """
    A data source that returns particle information about the members of a
    HOP-identified halo.
    """

    _distributed = False
    _processing = False
    _owner = 0
    indices = None
    extra_wrap = ["__getitem__"]

    def __init__(
        self,
        halo_list,
        id,
        indices=None,
        size=None,
        CoM=None,
        max_dens_point=None,
        group_total_mass=None,
        max_radius=None,
        bulk_vel=None,
        tasks=None,
        rms_vel=None,
        supp=None,
        ptype="all",
    ):
        self.ptype = ptype
        self.halo_list = halo_list
        self._max_dens = halo_list._max_dens
        self.id = id
        self.data = halo_list._data_source
        self.ds = self.data.ds
        self.gridsize = self.ds.domain_right_edge - self.ds.domain_left_edge
        if indices is not None:
            self.indices = halo_list._base_indices[indices]
        else:
            self.indices = None
        # We assume that if indices = None, the instantiator has OTHER plans
        # for us -- i.e., setting it somehow else
        self.size = size
        self.CoM = CoM
        self.max_dens_point = max_dens_point
        self.group_total_mass = group_total_mass
        self.max_radius = max_radius
        self.bulk_vel = bulk_vel
        self.tasks = tasks
        self.rms_vel = rms_vel
        self.bin_count = None
        self.overdensity = None
        # A supplementary data dict.
        if supp is None:
            self.supp = {}
        else:
            self.supp = supp
        self._saved_fields = {}
        self._ds_sort = None
        self._particle_mask = None

    @property
    def particle_mask(self):
        # Dynamically create the masking array for particles, and get
        # the data using standard yt methods.
        if self._particle_mask is not None:
            return self._particle_mask
        # This is from disk.
        pid = self.__getitem__("particle_index")
        # This is from the sphere.
        if self._name == "RockstarHalo":
            ds = self.ds.sphere(self.CoM, self._radjust * self.max_radius)
        elif self._name == "LoadedHalo":
            ds = self.ds.sphere(
                self.CoM,
                np.maximum(
                    self._radjust * self.ds.quan(self.max_radius, "code_length"),
                    self.ds.index.get_smallest_dx(),
                ),
            )
        sp_pid = ds["particle_index"]
        self._ds_sort = sp_pid.argsort()
        sp_pid = sp_pid[self._ds_sort]
        # This matches them up.
        self._particle_mask = np.in1d(sp_pid, pid)
        return self._particle_mask

    def center_of_mass(self):
        r"""Calculate and return the center of mass.

        The center of mass of the halo is directly calculated and returned.

        Examples
        --------
        >>> com = halos[0].center_of_mass()
        """
        if self.CoM is not None:
            return self.CoM
        pm = self["particle_mass"].in_units("Msun")
        c = {}
        # We shift into a box where the origin is the left edge
        c[0] = self["particle_position_x"] - self.ds.domain_left_edge[0]
        c[1] = self["particle_position_y"] - self.ds.domain_left_edge[1]
        c[2] = self["particle_position_z"] - self.ds.domain_left_edge[2]
        com = []
        for i in range(3):
            # A halo is likely periodic around a boundary if the distance
            # between the max and min particle
            # positions are larger than half the box.
            # So skip the rest if the converse is true.
            # Note we might make a change here when periodicity-handling is
            # fully implemented.
            if (c[i].max() - c[i].min()) < (self.ds.domain_width[i] / 2.0):
                com.append(c[i])
                continue
            # Now we want to flip around only those close to the left boundary.
            sel = c[i] <= (self.ds.domain_width[i] / 2)
            c[i][sel] += self.ds.domain_width[i]
            com.append(c[i])

        c = (com * pm).sum(axis=1) / pm.sum()
        c = self.ds.arr(c, "code_length")

        return c % self.ds.domain_width + self.ds.domain_left_edge

    def maximum_density(self):
        r"""Return the HOP-identified maximum density. Not applicable to
        FOF halos.

        Return the HOP-identified maximum density. Not applicable to FOF halos.

        Examples
        --------
        >>> max_dens = halos[0].maximum_density()
        """
        if self.max_dens_point is not None:
            return self.max_dens_point[0]
        return self._max_dens[self.id][0]

    def maximum_density_location(self):
        r"""Return the location HOP identified as maximally dense. Not
        applicable to FOF halos.

        Return the location HOP identified as maximally dense.

        Examples
        --------
        >>> max_dens_loc = halos[0].maximum_density_location()
        """
        if self.max_dens_point is not None:
            return self.max_dens_point[1:]
        return np.array(
            [
                self._max_dens[self.id][1],
                self._max_dens[self.id][2],
                self._max_dens[self.id][3],
            ]
        )

    def total_mass(self):
        r"""Returns the total mass in solar masses of the halo.

        Returns the total mass in solar masses of just the particles in the
        halo.

        Examples
        --------
        >>> halos[0].total_mass()
        """
        if self.group_total_mass is not None:
            return self.group_total_mass
        return self["particle_mass"].in_units("Msun").sum()

    def bulk_velocity(self):
        r"""Returns the mass-weighted average velocity in cm/s.

        This calculates and returns the mass-weighted average velocity of just
        the particles in the halo in cm/s.

        Examples
        --------
        >>> bv = halos[0].bulk_velocity()
        """
        if self.bulk_vel is not None:
            return self.bulk_vel
        pm = self["particle_mass"].in_units("Msun")
        vx = (self["particle_velocity_x"] * pm).sum()
        vy = (self["particle_velocity_y"] * pm).sum()
        vz = (self["particle_velocity_z"] * pm).sum()
        return self.ds.arr([vx, vy, vz], vx.units) / pm.sum()

    def rms_velocity(self):
        r"""Returns the mass-weighted RMS velocity for the halo
        particles in cgs units.

        Calculate and return the mass-weighted RMS velocity for just the
        particles in the halo.  The bulk velocity of the halo is subtracted
        before computation.

        Examples
        --------
        >>> rms_vel = halos[0].rms_velocity()
        """
        if self.rms_vel is not None:
            return self.rms_vel
        bv = self.bulk_velocity()
        pm = self["particle_mass"].in_units("Msun")
        sm = pm.sum()
        vx = (self["particle_velocity_x"] - bv[0]) * pm / sm
        vy = (self["particle_velocity_y"] - bv[1]) * pm / sm
        vz = (self["particle_velocity_z"] - bv[2]) * pm / sm
        s = vx**2.0 + vy**2.0 + vz**2.0
        ms = np.mean(s)
        return np.sqrt(ms) * pm.size

    def maximum_radius(self, center_of_mass=True):
        r"""Returns the maximum radius in the halo for all particles,
        either from the point of maximum density or from the
        center of mass.

        The maximum radius from the most dense point is calculated.  This
        accounts for periodicity.

        Parameters
        ----------
        center_of_mass : bool
            True chooses the center of mass when
            calculating the maximum radius.
            False chooses from the maximum density location for HOP halos
            (it has no effect for FOF halos).
            Default = True.

        Examples
        --------
        >>> radius = halos[0].maximum_radius()
        """
        if self.max_radius is not None:
            return self.max_radius
        if center_of_mass:
            center = self.center_of_mass()
        else:
            center = self.maximum_density_location()
        rx = np.abs(self["particle_position_x"] - center[0])
        ry = np.abs(self["particle_position_y"] - center[1])
        rz = np.abs(self["particle_position_z"] - center[2])
        DW = self.data.ds.domain_right_edge - self.data.ds.domain_left_edge
        r = np.sqrt(
            np.minimum(rx, DW[0] - rx) ** 2.0
            + np.minimum(ry, DW[1] - ry) ** 2.0
            + np.minimum(rz, DW[2] - rz) ** 2.0
        )
        return r.max()

    def __getitem__(self, key):
        return self.data[(self.ptype, key)][self.indices]

    def get_sphere(self, center_of_mass=True):
        r"""Returns a sphere source.

        This will generate a new, empty sphere source centered on this halo,
        with the maximum radius of the halo. This can be used like any other
        data container in yt.

        Parameters
        ----------
        center_of_mass : bool, optional
            True chooses the center of mass when
            calculating the maximum radius.
            False chooses from the maximum density location for HOP halos
            (it has no effect for FOF halos).
            Default = True.

        Returns
        -------
        sphere : `yt.data_objects.api.YTSphere`
            The empty data source.

        Examples
        --------
        >>> sp = halos[0].get_sphere()
        """
        if center_of_mass:
            center = self.center_of_mass()
        else:
            center = self.maximum_density_location()
        radius = self.maximum_radius()
        # A bit of a long-reach here...
        sphere = self.data.ds.sphere(center, radius=radius)
        return sphere

    def get_size(self):
        if self.size is not None:
            return self.size
        return self.indices.size

    def virial_mass(self, virial_overdensity=200.0, bins=300):
        r"""Return the virial mass of the halo in Msun,
        using only the particles
        in the halo (no baryonic information used).

        The virial mass is calculated, using the built in `Halo.virial_info`
        functionality.  The mass is then returned.

        Parameters
        ----------
        virial_overdensity : float
            The overdensity threshold compared to the universal average when
            calculating the virial mass. Default = 200.
        bins : int
            The number of spherical bins used to calculate overdensities.
            Default = 300.

        Returns
        -------
        mass : float
            The virial mass in solar masses of the particles in the halo.  -1
            if not virialized.

        Examples
        --------
        >>> vm = halos[0].virial_mass()
        """
        self.virial_info(bins=bins)
        vir_bin = self.virial_bin(virial_overdensity=virial_overdensity, bins=bins)
        if vir_bin != -1:
            return self.mass_bins[vir_bin]
        else:
            return -1

    def virial_radius(self, virial_overdensity=200.0, bins=300):
        r"""Return the virial radius of the halo in code units.

        The virial radius of the halo is calculated, using only the particles
        in the halo (no baryonic information used). Returns -1 if the halo is
        not virialized.

        Parameters
        ----------
        virial_overdensity : float
            The overdensity threshold compared to the universal average when
            calculating the virial radius. Default = 200.
        bins : integer
            The number of spherical bins used to calculate overdensities.
            Default = 300.

        Returns
        -------
        radius : float
            The virial radius in code units of the particles in the halo.  -1
            if not virialized.

        Examples
        --------
        >>> vr = halos[0].virial_radius()
        """
        self.virial_info(bins=bins)
        vir_bin = self.virial_bin(virial_overdensity=virial_overdensity, bins=bins)
        if vir_bin != -1:
            return self.radial_bins[vir_bin]
        else:
            return -1

    def virial_bin(self, virial_overdensity=200.0, bins=300):
        r"""Returns the bin index of the virial radius of the halo. Generally,
        it is better to call virial_radius instead, which calls this function
        automatically.
        """
        self.virial_info(bins=bins)
        over = self.overdensity > virial_overdensity
        if over.any():
            vir_bin = max(np.arange(bins + 1)[over])
            return vir_bin
        else:
            return -1

    def virial_info(self, bins=300):
        r"""Calculates the virial information for the halo. Generally, it is
        better to call virial_radius or virial_mass instead, which calls this
        function automatically.
        """
        # Skip if we've already calculated for this number of bins.
        if self.bin_count == bins and self.overdensity is not None:
            return None
        self.bin_count = bins
        # Cosmology
        h = self.ds.hubble_constant
        Om_matter = self.ds.omega_matter
        z = self.ds.current_redshift
        period = self.ds.domain_right_edge - self.ds.domain_left_edge
        thissize = self.get_size()
        rho_crit = rho_crit_g_cm3_h2 * h**2.0 * Om_matter  # g cm^-3
        Msun2g = mass_sun_cgs
        rho_crit = rho_crit * ((1.0 + z) ** 3.0)
        # Get some pertinent information about the halo.
        self.mass_bins = self.ds.arr(
            np.zeros(self.bin_count + 1, dtype="float64"), "Msun"
        )
        dist = np.empty(thissize, dtype="float64")
        cen = self.center_of_mass()
        mark = 0
        # Find the distances to the particles. I don't like this much, but I
        # can't see a way to eliminate a loop like this, either here or in yt.
        for pos in zip(
            self["particle_position_x"],
            self["particle_position_y"],
            self["particle_position_z"],
        ):
            dist[mark] = periodic_dist(cen, pos, period)
            mark += 1
        # Set up the radial bins.
        # Multiply min and max to prevent issues with digitize below.
        self.radial_bins = np.logspace(
            np.log10(min(dist) * 0.99 + TINY),
            np.log10(max(dist) * 1.01 + 2 * TINY),
            num=self.bin_count + 1,
        )
        self.radial_bins = self.ds.arr(self.radial_bins, "code_length")
        # Find out which bin each particle goes into, and add the particle
        # mass to that bin.
        inds = np.digitize(dist, self.radial_bins) - 1
        if self["particle_position_x"].size > 1:
            for index in np.unique(inds):
                self.mass_bins[index] += np.sum(
                    self["particle_mass"][inds == index]
                ).in_units("Msun")
        # Now forward sum the masses in the bins.
        for i in range(self.bin_count):
            self.mass_bins[i + 1] += self.mass_bins[i]
        # Calculate the over densities in the bins.
        self.overdensity = (
            self.mass_bins
            * Msun2g
            / (4.0 / 3.0 * np.pi * rho_crit * (self.radial_bins) ** 3.0)
        )

    def _get_ellipsoid_parameters_basic(self):
        np.seterr(all="ignore")
        # check if there are 4 particles to form an ellipsoid
        # neglecting to check if the 4 particles in the same plane,
        # that is almost certainly never to occur,
        # will deal with it later if it ever comes up
        if np.size(self["particle_position_x"]) < 4:
            mylog.warning("Too few particles for ellipsoid parameters.")
            return (0, 0, 0, 0, 0, 0, 0)
        # Calculate the parameters that describe the ellipsoid of
        # the particles that constitute the halo. This function returns
        # all the parameters except for the center of mass.
        com = self.center_of_mass()
        position = [
            self["particle_position_x"],
            self["particle_position_y"],
            self["particle_position_z"],
        ]
        # Locate the furthest particle from com, its vector length and index
        DW = np.array([self.gridsize[0], self.gridsize[1], self.gridsize[2]])
        position = [position[0] - com[0], position[1] - com[1], position[2] - com[2]]
        # different cases of particles being on other side of boundary
        for axis in range(np.size(DW)):
            cases = np.array(
                [position[axis], position[axis] + DW[axis], position[axis] - DW[axis]]
            )
            # pick out the smallest absolute distance from com
            position[axis] = np.choose(np.abs(cases).argmin(axis=0), cases)
        # find the furthest particle's index
        r = np.sqrt(position[0] ** 2 + position[1] ** 2 + position[2] ** 2)
        A_index = r.argmax()
        mag_A = r.max()
        # designate the A vector
        A_vector = (position[0][A_index], position[1][A_index], position[2][A_index])
        # designate the e0 unit vector
        e0_vector = A_vector / mag_A
        # locate the tB particle position by finding the max B
        e0_vector_copy = np.empty((np.size(position[0]), 3), dtype="float64")
        for i in range(3):
            e0_vector_copy[:, i] = e0_vector[i]
        rr = np.array(
            [position[0], position[1], position[2]]
        ).T  # Similar to tB_vector in old code.
        tC_vector = np.cross(e0_vector_copy, rr)
        te2 = tC_vector.copy()
        for dim in range(3):
            te2[:, dim] *= np.sum(tC_vector**2.0, axis=1) ** (-0.5)
        te1 = np.cross(te2, e0_vector_copy)
        length = np.abs(
            -np.sum(rr * te1, axis=1)
            * (1.0 - np.sum(rr * e0_vector_copy, axis=1) ** 2.0 * mag_A**-2.0)
            ** (-0.5)
        )
        # This problem apparently happens sometimes, that the NaNs are turned
        # into infs, which messes up the nanargmax below.
        length[length == np.inf] = 0.0
        tB_index = np.nanargmax(length)  # ignores NaNs created above.
        mag_B = length[tB_index]
        e1_vector = te1[tB_index]
        e2_vector = te2[tB_index]
        temp_e0 = rr.copy()
        temp_e1 = rr.copy()
        temp_e2 = rr.copy()
        for dim in range(3):
            temp_e0[:, dim] = e0_vector[dim]
            temp_e1[:, dim] = e1_vector[dim]
            temp_e2[:, dim] = e2_vector[dim]
        length = np.abs(
            np.sum(rr * temp_e2, axis=1)
            * (
                1
                - np.sum(rr * temp_e0, axis=1) ** 2.0 * mag_A**-2.0
                - np.sum(rr * temp_e1, axis=1) ** 2.0 * mag_B**-2.0
            )
            ** (-0.5)
        )
        length[length == np.inf] = 0.0
        tC_index = np.nanargmax(length)
        mag_C = length[tC_index]
        # tilt is calculated from the rotation about x axis
        # needed to align e1 vector with the y axis
        # after e0 is aligned with x axis
        # find the t1 angle needed to rotate about z axis to align e0 onto x-z plane
        t1 = np.arctan(-e0_vector[1] / e0_vector[0])
        RZ = get_rotation_matrix(t1, (0, 0, 1))
        r1 = np.dot(RZ, e0_vector)
        # find the t2 angle needed to rotate about y axis to align e0 to x
        t2 = np.arctan(r1[2] / r1[0])
        RY = get_rotation_matrix(t2, (0, 1, 0))
        r2 = np.dot(RY, np.dot(RZ, e1_vector))
        # find the tilt angle needed to rotate about x axis to align e1 to y and e2 to z
        tilt = np.arctan(-r2[2] / r2[1])
        return (mag_A, mag_B, mag_C, e0_vector[0], e0_vector[1], e0_vector[2], tilt)


class HOPHalo(Halo):
    _name = "HOPHalo"
    pass


class FOFHalo(Halo):
    def maximum_density(self):
        r"""Not implemented."""
        return -1

    def maximum_density_location(self):
        r"""Not implemented."""
        return self.center_of_mass()


class HaloList:

    _fields = ["particle_position_%s" % ax for ax in "xyz"]

    def __init__(self, data_source, redshift=-1, ptype="all"):
        """
        Run hop on *data_source* with a given density *threshold*.
        Returns an iterable collection of
        *HopGroup* items.
        """
        self._data_source = data_source
        self.ptype = ptype
        self._groups = []
        self._max_dens = {}
        self.__obtain_particles()
        self._run_finder()
        mylog.info("Parsing outputs")
        self._parse_output()
        mylog.debug("Finished. (%s)", len(self))
        self.redshift = redshift

    def __obtain_particles(self):
        ii = slice(None)
        self.particle_fields = {}
        for field in self._fields:
            tot_part = self._data_source[(self.ptype, field)].size
            if field == "particle_index":
                self.particle_fields[field] = self._data_source[(self.ptype, field)][
                    ii
                ].astype("int64")
            else:
                self.particle_fields[field] = self._data_source[(self.ptype, field)][
                    ii
                ].astype("float64")
            del self._data_source[(self.ptype, field)]
        self._base_indices = np.arange(tot_part)[ii]
        gc.collect()

    def _parse_output(self):
        unique_ids = np.unique(self.tags)
        counts = np.bincount(self.tags + 1)
        sort_indices = np.argsort(self.tags)
        grab_indices = np.indices(self.tags.shape).ravel()[sort_indices]
        dens = self.densities[sort_indices]
        cp = 0
        for i in unique_ids:
            cp_c = cp + counts[i + 1]
            if i == -1:
                cp += counts[i + 1]
                continue
            group_indices = grab_indices[cp:cp_c]
            self._groups.append(
                self._halo_class(self, i, group_indices, ptype=self.ptype)
            )
            md_i = np.argmax(dens[cp:cp_c])
            px, py, pz = (
                self.particle_fields["particle_position_%s" % ax][group_indices]
                for ax in "xyz"
            )
            self._max_dens[i] = (dens[cp:cp_c][md_i], px[md_i], py[md_i], pz[md_i])
            cp += counts[i + 1]

    def __len__(self):
        return len(self._groups)

    def __iter__(self):
        yield from self._groups

    def __getitem__(self, key):
        return self._groups[key]


class HOPHaloList(HaloList):
    """
    Run hop on *data_source* with a given density *threshold*.
    Returns an iterable collection of *HopGroup* items.
    """

    _name = "HOP"
    _halo_class = HOPHalo
    _fields = ["particle_position_%s" % ax for ax in "xyz"] + ["particle_mass"]

    def __init__(self, data_source, threshold=160.0, ptype="all"):
        self.threshold = threshold
        mylog.info("Initializing HOP")
        HaloList.__init__(self, data_source, ptype=ptype)

    def _run_finder(self):
        self.densities, self.tags = RunHOP(
            self.particle_fields["particle_position_x"] / self.period[0],
            self.particle_fields["particle_position_y"] / self.period[1],
            self.particle_fields["particle_position_z"] / self.period[2],
            self.particle_fields["particle_mass"].in_units("Msun"),
            self.threshold,
        )
        self.particle_fields["densities"] = self.densities
        self.particle_fields["tags"] = self.tags


class FOFHaloList(HaloList):
    _name = "FOF"
    _halo_class = FOFHalo

    def __init__(self, data_source, link=0.2, redshift=-1, ptype="all"):
        self.link = link
        mylog.info("Initializing FOF")
        HaloList.__init__(self, data_source, redshift=redshift, ptype=ptype)

    def _run_finder(self):
        self.tags = RunFOF(
            self.particle_fields["particle_position_x"] / self.period[0],
            self.particle_fields["particle_position_y"] / self.period[1],
            self.particle_fields["particle_position_z"] / self.period[2],
            self.link,
        )
        self.densities = np.ones(self.tags.size, dtype="float64") * -1
        self.particle_fields["densities"] = self.densities
        self.particle_fields["tags"] = self.tags


class GenericHaloFinder(HaloList, ParallelAnalysisInterface):
    def __init__(self, ds, data_source, padding=0.0, ptype="all"):
        ParallelAnalysisInterface.__init__(self)
        self.ds = ds
        self.index = ds.index
        self.center = (
            np.array(data_source.right_edge) + np.array(data_source.left_edge)
        ) / 2.0
        self.ptype = ptype

    def _parse_halolist(self, threshold_adjustment):
        groups = []
        max_dens = {}
        hi = 0
        LE, RE = self.bounds
        for halo in self._groups:
            this_max_dens = halo.maximum_density_location()
            # if the most dense particle is in the box, keep it
            if np.all((this_max_dens >= LE) & (this_max_dens <= RE)):
                # Now we add the halo information to OURSELVES, taken from the
                # self.hop_list
                # We need to mock up the HOPHaloList thingie, so we need to
                #     set self._max_dens
                max_dens_temp = list(self._max_dens[halo.id])[0] / threshold_adjustment
                max_dens[hi] = [max_dens_temp] + list(self._max_dens[halo.id])[1:4]
                groups.append(self._halo_class(self, hi, ptype=self.ptype))
                groups[-1].indices = halo.indices
                self.comm.claim_object(groups[-1])
                hi += 1
        del self._groups, self._max_dens  # explicit >> implicit
        self._groups = groups
        self._max_dens = max_dens

    def _join_halolists(self):
        groups = {self.comm.rank: len(self)}
        groups = self.comm.par_combine_object(groups, datatype="dict", op="join")

        ngroups = np.array([groups[rank] for rank in sorted(groups)])
        offsets = ngroups.cumsum() - ngroups
        my_offset = offsets[self.comm.rank]
        for halo in self:
            halo.id += my_offset

    def _reposition_particles(self, bounds):
        # This only does periodicity.  We do NOT want to deal with anything
        # else.  The only reason we even do periodicity is the
        LE, RE = bounds
        dw = self.ds.domain_right_edge - self.ds.domain_left_edge
        for i, ax in enumerate("xyz"):
            arr = self._data_source[self.ptype, "particle_position_%s" % ax]
            arr[arr < LE[i] - self.padding] += dw[i]
            arr[arr > RE[i] + self.padding] -= dw[i]


class HOPHaloFinder(GenericHaloFinder, HOPHaloList):
    r"""HOP halo finder.

    Halos are built by:
    1. Calculating a density for each particle based on a smoothing kernel.
    2. Recursively linking particles to other particles from lower density
    particles to higher.
    3. Geometrically proximate chains are identified and
    4. merged into final halos following merging rules.

    Lower thresholds generally produce more halos, and the largest halos
    become larger. Also, halos become more filamentary and over-connected.

    Eisenstein and Hut. "HOP: A New Group-Finding Algorithm for N-Body
    Simulations." ApJ (1998) vol. 498 pp. 137-142

    Parameters
    ----------
    ds : `Dataset`
        The dataset on which halo finding will be conducted.
    subvolume : `yt.data_objects.data_containers.YTSelectionContainer`, optional
        A region over which HOP will be run, which can be used to run HOP
        on a subvolume of the full volume. Default = None, which defaults
        to the full volume automatically.
    threshold : float
        The density threshold used when building halos. Default = 160.0.
    ptype : string
        The particle type to be used for halo finding.
        Default: 'all'.
    padding : float
        When run in parallel, the finder needs to surround each subvolume
        with duplicated particles for halo finidng to work. This number
        must be no smaller than the radius of the largest halo in the box
        in code units. Default = 0.02.
    total_mass : float
        If HOP is run on the same dataset mulitple times, the total mass
        of particles in Msun units in the full volume can be supplied here
        to save time.
        This must correspond to the particles being operated on, meaning
        if stars are included in the halo finding, they must be included
        in this mass as well, and visa-versa.
        If halo finding on a subvolume, this still corresponds with the
        mass in the entire volume.
        Default = None, which means the total mass is automatically
        calculated.
    save_particles : bool
        If True, output member particles for each halo.
        Default: True.

    Examples
    --------
    >>> import yt
    >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
    >>> data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
    >>> hc = HaloCatalog(data_ds=data_ds, finder_method='hop',
    ...                  finder_kwargs={"threshold": 160})
    >>> hc.create()
    """

    def __init__(
        self,
        ds,
        subvolume=None,
        threshold=160,
        dm_only=False,
        ptype="all",
        padding=0.02,
        total_mass=None,
        save_particles=True,
    ):
        if subvolume is not None:
            ds_LE = np.array(subvolume.left_edge)
            ds_RE = np.array(subvolume.right_edge)
        self.period = ds.domain_right_edge - ds.domain_left_edge
        self.save_particles = save_particles
        self._data_source = ds.all_data()
        GenericHaloFinder.__init__(self, ds, self._data_source, padding, ptype=ptype)
        # do it once with no padding so the total_mass is correct
        # (no duplicated particles), and on the entire volume, even if only
        # a small part is actually going to be used.
        self.padding = 0.0
        padded, LE, RE, self._data_source = self.partition_index_3d(
            ds=self._data_source, padding=self.padding
        )

        if dm_only:
            raise RuntimeError(
                "dm_only has been removed. "
                + "Use ptype to specify a particle type, instead."
            )

        self.ptype = ptype

        # For scaling the threshold, note that it's a passthrough
        if total_mass is None:
            total_mass = self.comm.mpi_allreduce(
                self._data_source.quantities.total_quantity(
                    (self.ptype, "particle_mass")
                ).in_units("Msun"),
                op="sum",
            )
        # MJT: Note that instead of this, if we are assuming that the particles
        # are all on different processors, we should instead construct an
        # object representing the entire domain and sum it "lazily" with
        # Derived Quantities.
        if subvolume is not None:
            self._data_source = ds.region([0.0] * 3, ds_LE, ds_RE)
        else:
            self._data_source = ds.all_data()
        self.padding = padding  # * ds["unitary"] # This should be clevererer
        padded, LE, RE, self._data_source = self.partition_index_3d(
            ds=self._data_source, padding=self.padding
        )
        self.bounds = (LE, RE)
        # sub_mass can be skipped if subvolume is not used and this is not
        # parallel.
        if (
            subvolume is None
            and ytcfg.get("yt", "internals", "topcomm_parallel_size") == 1
        ):
            sub_mass = total_mass
        else:
            sub_mass = self._data_source.quantities.total_quantity(
                (self.ptype, "particle_mass")
            ).in_units("Msun")
        HOPHaloList.__init__(
            self, self._data_source, threshold * total_mass / sub_mass, ptype=self.ptype
        )
        self._parse_halolist(total_mass / sub_mass)
        self._join_halolists()


class FOFHaloFinder(GenericHaloFinder, FOFHaloList):
    r"""Friends-of-friends halo finder.

    Halos are found by linking together all pairs of particles closer than
    some distance from each other. Particles may have multiple links,
    and halos are found by recursively linking together all such pairs.

    Larger linking lengths produce more halos, and the largest halos
    become larger. Also, halos become more filamentary and over-connected.

    Davis et al. "The evolution of large-scale structure in a universe
    dominated by cold dark matter." ApJ (1985) vol. 292 pp. 371-394

    Parameters
    ----------
    ds : `Dataset`
        The dataset on which halo finding will be conducted.
    subvolume : `yt.data_objects.data_containers.YTSelectionContainer`, optional
        A region over which HOP will be run, which can be used to run HOP
        on a subvolume of the full volume. Default = None, which defaults
        to the full volume automatically.
    link : float
        If positive, the interparticle distance (compared to the overall
        average) used to build the halos. If negative, this is taken to be
        the *actual* linking length, and no other calculations will be
        applied.  Default = 0.2.
    ptype : string
        The type of particle to be used for halo finding.
        Default: 'all'.
    padding : float
        When run in parallel, the finder needs to surround each subvolume
        with duplicated particles for halo finidng to work. This number
        must be no smaller than the radius of the largest halo in the box
        in code units. Default = 0.02.
    save_particles : bool
        If True, output member particles for each halo.
        Default: True.

    Examples
    --------
    >>> import yt
    >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
    >>> data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
    >>> hc = HaloCatalog(data_ds=data_ds, finder_method='fof',
    ...                  finder_kwargs={"link": 0.2})
    >>> hc.create()
    """

    def __init__(
        self,
        ds,
        subvolume=None,
        link=0.2,
        dm_only=False,
        ptype="all",
        padding=0.02,
        save_particles=True,
    ):
        if subvolume is not None:
            ds_LE = np.array(subvolume.left_edge)
            ds_RE = np.array(subvolume.right_edge)
        self.period = ds.domain_right_edge - ds.domain_left_edge
        self.ds = ds
        self.index = ds.index
        self.redshift = ds.current_redshift
        self.save_particles = save_particles
        self._data_source = ds.all_data()
        GenericHaloFinder.__init__(self, ds, self._data_source, padding)
        self.padding = 0.0  # * ds["unitary"] # This should be clevererer
        # get the total number of particles across all procs, with no padding
        padded, LE, RE, self._data_source = self.partition_index_3d(
            ds=self._data_source, padding=self.padding
        )

        if dm_only:
            raise RuntimeError(
                "dm_only has been removed. "
                + "Use ptype to specify a particle type, instead."
            )

        self.ptype = ptype

        if link > 0.0:
            n_parts = self.comm.mpi_allreduce(
                self._data_source[self.ptype, "particle_ones"].size, op="sum"
            )
            # get the average spacing between particles
            # l = ds.domain_right_edge - ds.domain_left_edge
            # vol = l[0] * l[1] * l[2]
            # Because we are now allowing for datasets with non 1-periodicity,
            # but symmetric, vol is always 1.
            vol = 1.0
            avg_spacing = (float(vol) / n_parts) ** (1.0 / 3.0)
            linking_length = link * avg_spacing
        else:
            linking_length = np.abs(link)
        self.padding = padding
        if subvolume is not None:
            self._data_source = ds.region([0.0] * 3, ds_LE, ds_RE)
        else:
            self._data_source = ds.all_data()
        padded, LE, RE, self._data_source = self.partition_index_3d(
            ds=self._data_source, padding=self.padding
        )
        self.bounds = (LE, RE)
        # reflect particles around the periodic boundary
        # self._reposition_particles((LE, RE))
        # here is where the FOF halo finder is run
        mylog.info("Using a linking length of %0.3e", linking_length)
        FOFHaloList.__init__(
            self,
            self._data_source,
            linking_length,
            redshift=self.redshift,
            ptype=self.ptype,
        )
        self._parse_halolist(1.0)
        self._join_halolists()
