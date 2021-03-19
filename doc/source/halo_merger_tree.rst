.. _merger_tree:

Merger Trees
============

Merger trees can be created for :ref:`rockstar_finding` halo catalogs using
`consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`__.
The resulting merger tree data can be loaded with
`ytree <http://ytree.readthedocs.io>`__. Note, halo finding must be done on
a series of snapshots for this to work (see :ref:`halo_finding_time_series`).

For halo catalogs created with :ref:`fof_finding` or :ref:`hop_finding`, the
`treefarm <https://treefarm.readthedocs.io/>`__ package can be used for
generating merger trees. For this to work, member particles from halos must
also be saved (see :ref:`saving_halo_particles`). These merger trees can also
be loaded with `ytree <http://ytree.readthedocs.io>`__.
