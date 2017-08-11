.. _importing:

Importing from ``yt_astro_analysis``
====================================

For every module that was moved from yt's analysis_modules to yt_astro_analysis,
all imports can be changed simply by substituting ``yt.analysis_modules`` with
``yt.extensions.astro_analysis``.  For example, the following

.. code-block:: python

   from yt.analysis_modules.ppv_cube.api import PPVCube

becomes

.. code-block:: python

   from yt.extensions.astro_analysis.ppv_cube.api import PPVCube
