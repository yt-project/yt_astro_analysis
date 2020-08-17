# The yt Astro Analysis Extension

[![Users' Mailing List](https://img.shields.io/badge/Users-List-lightgrey.svg)](https://mail.python.org/archives/list/yt-users@python.org//)
[![Devel Mailing List](https://img.shields.io/badge/Devel-List-lightgrey.svg)](https://mail.python.org/archives/list/yt-dev@python.org//)
[![CircleCI](https://circleci.com/gh/yt-project/yt_astro_analysis.svg?style=svg)](https://circleci.com/gh/yt-project/yt_astro_analysis)
[![codecov](https://codecov.io/gh/yt-project/yt_astro_analysis/branch/master/graph/badge.svg)](https://codecov.io/gh/yt-project/yt_astro_analysis)
[![Documentation Status](https://readthedocs.org/projects/yt-astro-analysis/badge/?version=latest)](https://yt-astro-analysis.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/yt-astro-analysis.svg)](https://badge.fury.io/py/yt-astro-analysis)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/yt_astro_analysis.svg)](https://anaconda.org/conda-forge/yt_astro_analysis)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1458961.svg)](https://doi.org/10.5281/zenodo.1458961)
[![Data Hub](https://img.shields.io/badge/data-hub-orange.svg)](https://hub.yt/)
[![Powered by NumFOCUS](https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A)](https://numfocus.org)

This is yt_astro_analysis, the [yt](https://github.com/yt-project/yt) extension
package for astrophysical analysis.  This is primarily machinery that used to be
in yt's analysis_modules.  These were made into a separate package to allow yt to
become less astro-specifc and to allow these modules to be developed on their own
schedule.

## Installation

Full installation documentation can also be found
[here](https://yt-astro-analysis.readthedocs.io/en/latest/Installation.html).

To install yt_astro_analysis, you will first need to 
[install yt](https://github.com/yt-project/yt#installation). Then do,

```
$ pip install yt_astro_analysis
```

If you use conda, do,

```
$ conda install -c conda-forge yt_astro_analysis
```

If you would like to build `yt_astro_analysis` from source, clone the git
repository and install like this:

```
git clone https://github.com/yt-project/yt_astro_analysis
cd yt_astro_analysis
pip install -e .
```

### Installing with Rockstar support

In order to run the Rockstar halo finder from within yt_astro_analysis, you will
need to install ``rockstar-galaxies`` from either
[John Wise's
repository](https://bitbucket.org/jwise77/rockstar-galaxies) or [Peter
Behroozi's
repository](https://bitbucket.org/pbehroozi/rockstar-galaxies). To
install Rockstar, do the following:

```
git clone https://bitbucket.org/jwise77/rockstar-galaxies
cd rockstar-galaxies
make lib
```

Then, go into the yt_astro_analysis source directory and add a file called
"rockstar.cfg" with the path the Rockstar repo you just cloned.  Then, install
yt_astro_analysis.

```
cd yt_astro_analysis
echo <path_to_rockstar> > rockstar.cfg
pip install -e .
```

Finally, you'll need to make sure that the location of
``librockstar-galaxies.so`` is in your LD_LIBRARY_PATH.

```
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<path_to_rockstar>
```

## Importing from yt_astro_analysis

For every module that was moved from yt's analysis_modules to yt_astro_analysis,
all imports can be changed simply by substituting ``yt.analysis_modules`` with
``yt.extensions.astro_analysis``.  For example, the following

```
from yt.analysis_modules.ppv_cube.api import PPVCube
```
becomes
```
from yt.extensions.astro_analysis.ppv_cube.api import PPVCube
```

## Contributing

We really want your contributions!  As an official
[yt-project](https://yt-project.org/) extension, everything in the
[yt Contributor Guide](https://github.com/yt-project/yt#contributing) applies
here.

If you'd rather make your own standalone package, we want to support that, too!
Please, consider making your package a
[yt extension](https://yt-project.org/extensions.html).

## Resources

As an extension of the [yt-project](https://yt-project.org/), the
[yt resources](https://github.com/yt-project/yt#resources) are available for help.

 * The latest documentation can be found at https://yt-astro-analysis.readthedocs.io/
