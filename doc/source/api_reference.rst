.. _api_reference:

API Reference
=============

.. _halo_analysis_ref:

Halo Analysis
-------------

The ``HaloCatalog`` object is the primary means for performing custom analysis
on cosmological halos.  It is also the primary interface for halo finding.

.. autosummary::
   :toctree: generated/

   ~yt_astro_analysis.halo_analysis.halo_catalog.HaloCatalog
   ~yt_astro_analysis.halo_analysis.halo_finding_methods.HaloFindingMethod
   ~yt_astro_analysis.halo_analysis.halo_callbacks.HaloCallback
   ~yt_astro_analysis.halo_analysis.halo_callbacks.delete_attribute
   ~yt_astro_analysis.halo_analysis.halo_callbacks.halo_sphere
   ~yt_astro_analysis.halo_analysis.halo_callbacks.iterative_center_of_mass
   ~yt_astro_analysis.halo_analysis.halo_callbacks.load_profiles
   ~yt_astro_analysis.halo_analysis.halo_callbacks.phase_plot
   ~yt_astro_analysis.halo_analysis.halo_callbacks.profile
   ~yt_astro_analysis.halo_analysis.halo_callbacks.save_profiles
   ~yt_astro_analysis.halo_analysis.halo_callbacks.sphere_bulk_velocity
   ~yt_astro_analysis.halo_analysis.halo_callbacks.sphere_field_max_recenter
   ~yt_astro_analysis.halo_analysis.halo_callbacks.virial_quantities
   ~yt_astro_analysis.halo_analysis.halo_filters.HaloFilter
   ~yt_astro_analysis.halo_analysis.halo_filters.not_subhalo
   ~yt_astro_analysis.halo_analysis.halo_filters.quantity_value
   ~yt_astro_analysis.halo_analysis.halo_quantities.HaloQuantity
   ~yt_astro_analysis.halo_analysis.halo_quantities.bulk_velocity
   ~yt_astro_analysis.halo_analysis.halo_quantities.center_of_mass
   ~yt_astro_analysis.halo_analysis.halo_recipes.HaloRecipe
   ~yt_astro_analysis.halo_analysis.halo_recipes.calculate_virial_quantities

Halo Finding
------------

These provide direct access to the halo finders.  However, it is strongly
recommended to use the ``HaloCatalog``.

.. autosummary::
   :toctree: generated/

   ~yt_astro_analysis.halo_finding.halo_objects.FOFHaloFinder
   ~yt_astro_analysis.halo_finding.halo_objects.HOPHaloFinder
   ~yt_astro_analysis.halo_finding.rockstar.rockstar.RockstarHaloFinder

Cosmology Observation
---------------------

Light cone generation and simulation analysis.  (See also
:ref:`light-cone-generator`.)

.. autosummary::
   :toctree: generated/

   ~yt_astro_analysis.cosmological_observation.cosmology_splice.CosmologySplice
   ~yt_astro_analysis.cosmological_observation.light_cone.light_cone.LightCone

RADMC-3D exporting
------------------

.. autosummary::
   :toctree: generated/

   ~yt_astro_analysis.radmc3d_export.RadMC3DInterface.RadMC3DLayer
   ~yt_astro_analysis.radmc3d_export.RadMC3DInterface.RadMC3DWriter
