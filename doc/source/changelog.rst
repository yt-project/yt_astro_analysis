.. _changelog:

ChangeLog
=========

This is a log of changes to yt_astro_analysis over its release history.

Contributors
------------

The `CREDITS file
<https://github.com/yt-project/yt_astro_analysis/blob/main/CREDITS>`__
contains the most up-to-date list of everyone who has contributed to the
yt_astro_analysis source code.

Version 1.1.2
-------------

Release date: *January 23, 2023*

Bugfixes
^^^^^^^^

 * Fix compatibility with numpy 1.24 (numpy.float was removed) `PR #169 <https://github.com/yt-project/yt_astro_analysis/pull/169>`__
 * Build wheels for Python 3.11 `PR #170 <https://github.com/yt-project/yt_astro_analysis/pull/170>`__

Documentation and tests
^^^^^^^^^^^^^^^^^^^^^^^
 * Update package name for conda/pip installation. `PR #138 <https://github.com/yt-project/yt_astro_analysis/pull/138>`__
 * Hotfix CI (workaround upstream change of behaviour) `PR #145 <https://github.com/yt-project/yt_astro_analysis/pull/145>`__
 * Test on Python 3.11 `PR #163 <https://github.com/yt-project/yt_astro_analysis/pull/163>`__
 * Switch ubuntu image to 20.04 `PR #167 <https://github.com/yt-project/yt_astro_analysis/pull/167>`__

Requirements
^^^^^^^^^^^^
 * Drop support for CPython 3.7 `PR #157 <https://github.com/yt-project/yt_astro_analysis/pull/157>`__

**Full Changelog**: https://github.com/yt-project/yt_astro_analysis/compare/yt_astro_analysis-1.1.1...yt_astro_analysis-1.1.2


Version 1.1.1
-------------

Release date: *January 27, 2022*

Bugfixes
^^^^^^^^

 * Make sure to initialize index before checking particle types `PR #127 <https://github.com/yt-project/yt_astro_analysis/pull/127>`__
 * Fix broken example with halo plotting `PR #132 <https://github.com/yt-project/yt_astro_analysis/pull/132>`__
 * Make total particles a 64 bit integer `PR #133 <https://github.com/yt-project/yt_astro_analysis/pull/133>`__
 * Set output directory properly for rockstar halo finder `PR #134 <https://github.com/yt-project/yt_astro_analysis/pull/134>`__

**Full Changelog**: https://github.com/yt-project/yt_astro_analysis/compare/yt_astro_analysis-1.1.0...yt_astro_analysis-1.1.1

Version 1.1
-----------

Release date: *December 9, 2021*

New Features
^^^^^^^^^^^^

 * The HaloCatalog has been significantly refactored
   `PR #58 <https://github.com/yt-project/yt_astro_analysis/pull/58>`__, `PR #62 <https://github.com/yt-project/yt_astro_analysis/pull/62>`__ with
   the following additional improvements:

     * the interface to the Rockstar halo finder is now compatible with the latest version of Rockstar Galaxies `PR #55 <https://github.com/yt-project/yt_astro_analysis/pull/55>`__
     * all halo finders now support being run with time-series of datasets
     * halo particle ids now savable with FoF and HOP halo finders `PR #52 <https://github.com/yt-project/yt_astro_analysis/pull/52>`__
     * looping over halos is done with io chunks instead of ds.all_data for a significant speedup and reduction in memory
     * Allow more flexibility for specifying rockstar particle mass `PR #84 <https://github.com/yt-project/yt_astro_analysis/pull/84>`__
     * Add restart option for rockstar `PR #82 <https://github.com/yt-project/yt_astro_analysis/pull/82>`__
     * Adding an outer_radius parameter to the iterative COM callback `PR #34 <https://github.com/yt-project/yt_astro_analysis/pull/34>`__

 * Remove the sunyaev_zeldovich analysis module. This is now `ytsz <https://github.com/jzuhone/ytsz>`__. `PR #79 <https://github.com/yt-project/yt_astro_analysis/pull/79>`__
 * Drop support for python 3.6 `PR #100 <https://github.com/yt-project/yt_astro_analysis/pull/100>`__, `PR #101 <https://github.com/yt-project/yt_astro_analysis/pull/101>`__

Minor Enhancements and Bugfixes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 * significant project management and ci improvements `PR #89 <https://github.com/yt-project/yt_astro_analysis/pull/89>`__, `PR #90 <https://github.com/yt-project/yt_astro_analysis/pull/90>`__, `PR #91 <https://github.com/yt-project/yt_astro_analysis/pull/91>`__, `PR #92 <https://github.com/yt-project/yt_astro_analysis/pull/92>`__, `PR #96 <https://github.com/yt-project/yt_astro_analysis/pull/96>`__, `PR #95 <https://github.com/yt-project/yt_astro_analysis/pull/95>`__, `PR #97 <https://github.com/yt-project/yt_astro_analysis/pull/97>`__, `PR #108 <https://github.com/yt-project/yt_astro_analysis/pull/108>`__, `PR #109 <https://github.com/yt-project/yt_astro_analysis/pull/109>`__
 * Add annotate_halos function `PR #98 <https://github.com/yt-project/yt_astro_analysis/pull/98>`__
 * only access particle_type field in rockstar if it exists and is needed `PR #111 <https://github.com/yt-project/yt_astro_analysis/pull/111>`__
 * fix light cone projections with weight fields `PR #37 <https://github.com/yt-project/yt_astro_analysis/pull/37>`__
 * Fix HaloCatalog progress bar `PR #40 <https://github.com/yt-project/yt_astro_analysis/pull/40>`__
 * clarify rockstar error message about using the wrong number of MPI processes `PR #42 <https://github.com/yt-project/yt_astro_analysis/pull/42>`__, `PR #113 <https://github.com/yt-project/yt_astro_analysis/pull/113>`__
 * check derived_field_list for base fields `PR #43 <https://github.com/yt-project/yt_astro_analysis/pull/43>`__
 * allow cosmology splice from a single dataset `PR #49 <https://github.com/yt-project/yt_astro_analysis/pull/49>`__
 * Fix iterator `PR #68 <https://github.com/yt-project/yt_astro_analysis/pull/68>`__
 * Support new config file format `PR #65 <https://github.com/yt-project/yt_astro_analysis/pull/65>`__
 * Enable circleci testing `PR #44 <https://github.com/yt-project/yt_astro_analysis/pull/44>`__
 * Add max_box_fraction to plan_cosmology_splice `PR #76 <https://github.com/yt-project/yt_astro_analysis/pull/76>`__
 * Fix HaloCatalog output_dir `PR #81 <https://github.com/yt-project/yt_astro_analysis/pull/81>`__
 * remove deprecated dm_only keyword from halo finder `PR #57 <https://github.com/yt-project/yt_astro_analysis/pull/57>`__
 * update amr_grid.inp `PR #77 <https://github.com/yt-project/yt_astro_analysis/pull/77>`__

`Full Changelog <https://github.com/yt-project/yt_astro_analysis/compare/yt_astro_analysis-1.0.0...yt_astro_analysis-1.1.0>`__

Version 1.0
-----------

Release date: *October 11, 2018*

This is initial stable release of yt_astro_analysis. Before this, all
code in here was contained in the `yt package's
<https://github.com/yt-project/yt>`__ ``analysis_modules``
submodule. Version 1.0 of yt_astro_analysis is functionally identical
to the ``analysis_modules`` from yt version 3.5.0.
