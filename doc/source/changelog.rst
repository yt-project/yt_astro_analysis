.. _changelog:

ChangeLog
=========

This is a log of changes to yt_astro_analysis over its release history.

Contributors
------------

The `CREDITS file
<https://github.com/yt-project/yt_astro_analysis/blob/master/CREDITS>`__
contains the most up-to-date list of everyone who has contributed to the
yt_astro_analysis source code.

Version 1.1
-----------

Release date: *December 9, 2021*

New Features
^^^^^^^^^^^^

 * The HaloCatalog has been significantly refactored
   https://github.com/yt-project/yt_astro_analysis/pull/58, https://github.com/yt-project/yt_astro_analysis/pull/62 with
   the following additional improvements:

     * the interface to the Rockstar halo finder is now compatible with the latest version of Rockstar Galaxies https://github.com/yt-project/yt_astro_analysis/pull/55
     * all halo finders now support being run with time-series of datasets
     * halo particle ids now savable with FoF and HOP halo finders https://github.com/yt-project/yt_astro_analysis/pull/52
     * looping over halos is done with io chunks instead of ds.all_data for a significant speedup and reduction in memory
     * Allow more flexibility for specifying rockstar particle mass https://github.com/yt-project/yt_astro_analysis/pull/84
     * Add restart option for rockstar https://github.com/yt-project/yt_astro_analysis/pull/82
     * Adding an outer_radius parameter to the iterative COM callback https://github.com/yt-project/yt_astro_analysis/pull/34

 * Remove the sunyaev_zeldovich analysis module. This is now [pyxsim](http://hea-www.cfa.harvard.edu/~jzuhone/pyxsim/). https://github.com/yt-project/yt_astro_analysis/pull/79
 * Drop support for python 3.6 https://github.com/yt-project/yt_astro_analysis/pull/100, https://github.com/yt-project/yt_astro_analysis/pull/101

Minor Enhancements and Bugfixes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 * significant project management and ci improvements https://github.com/yt-project/yt_astro_analysis/pull/89, https://github.com/yt-project/yt_astro_analysis/pull/90, https://github.com/yt-project/yt_astro_analysis/pull/91, https://github.com/yt-project/yt_astro_analysis/pull/92, https://github.com/yt-project/yt_astro_analysis/pull/96, https://github.com/yt-project/yt_astro_analysis/pull/95, https://github.com/yt-project/yt_astro_analysis/pull/97, https://github.com/yt-project/yt_astro_analysis/pull/108, https://github.com/yt-project/yt_astro_analysis/pull/109
 * Add annotate_halos function https://github.com/yt-project/yt_astro_analysis/pull/98
 * only access particle_type field in rockstar if it exists and is needed https://github.com/yt-project/yt_astro_analysis/pull/111
 * fix light cone projections with weight fields https://github.com/yt-project/yt_astro_analysis/pull/37
 * Fix HaloCatalog progress bar https://github.com/yt-project/yt_astro_analysis/pull/40
 * clarify rockstar error message about using the wrong number of MPI processes https://github.com/yt-project/yt_astro_analysis/pull/42, https://github.com/yt-project/yt_astro_analysis/pull/113
 * check derived_field_list for base fields https://github.com/yt-project/yt_astro_analysis/pull/43
 * allow cosmology splice from a single dataset https://github.com/yt-project/yt_astro_analysis/pull/49
 * Fix iterator https://github.com/yt-project/yt_astro_analysis/pull/68
 * Support new config file format https://github.com/yt-project/yt_astro_analysis/pull/65
 * Enable circleci testing https://github.com/yt-project/yt_astro_analysis/pull/44
 * Add max_box_fraction to plan_cosmology_splice https://github.com/yt-project/yt_astro_analysis/pull/76
 * Fix HaloCatalog output_dir https://github.com/yt-project/yt_astro_analysis/pull/81
 * remove deprecated dm_only keyword from halo finder https://github.com/yt-project/yt_astro_analysis/pull/57
 * update amr_grid.inp https://github.com/yt-project/yt_astro_analysis/pull/77

**Full Changelog**: https://github.com/yt-project/yt_astro_analysis/compare/yt_astro_analysis-1.0.0...yt_astro_analysis-1.1.0

Version 1.0
-----------

Release date: *October 11, 2018*

This is initial stable release of yt_astro_analysis. Before this, all
code in here was contained in the `yt package's
<https://github.com/yt-project/yt>`__ ``analysis_modules``
submodule. Version 1.0 of yt_astro_analysis is functionally identical
to the ``analysis_modules`` from yt version 3.5.0.
