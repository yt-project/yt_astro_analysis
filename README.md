# The yt Astro Analysis Extension


[![PyPI version](https://badge.fury.io/py/yt-astro-analysis.svg)](https://badge.fury.io/py/yt-astro-analysis)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/yt-astro-analysis/badges/version.svg)](https://anaconda.org/conda-forge/yt-astro-analysis)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1458961.svg)](https://doi.org/10.5281/zenodo.1458961)
[![Powered by NumFOCUS](https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A)](https://numfocus.org)

[![CircleCI](https://circleci.com/gh/yt-project/yt_astro_analysis.svg?style=svg)](https://circleci.com/gh/yt-project/yt_astro_analysis)
[![codecov](https://codecov.io/gh/yt-project/yt_astro_analysis/branch/main/graph/badge.svg)](https://codecov.io/gh/yt-project/yt_astro_analysis)
[![Documentation Status](https://readthedocs.org/projects/yt-astro-analysis/badge/?version=latest)](https://yt-astro-analysis.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/yt-project/yt_astro_analysis/main.svg)](https://results.pre-commit.ci/latest/github/yt-project/yt_astro_analysis/main)

[![yt-project](https://img.shields.io/static/v1?label="works%20with"&message="yt"&color="blueviolet")](https://yt-project.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

This is yt_astro_analysis, the [yt](https://github.com/yt-project/yt) extension
package for astrophysical analysis. This package contains
functionality for:

 * Halo finding and analysis
 * Lightcones
 * Planning cosmological simulations for making lightcones and lightrays
 * Exporting to the RADMC-3D radiation transport code
 * Creating PPV FITS cubes

This is primarily machinery that used to be in yt's
analysis_modules. These were made into a separate package to allow yt
to become less astro-specifc and to allow these modules to be
developed on their own schedule.

## Installation

Full installation documentation can also be found
[here](https://yt-astro-analysis.readthedocs.io/en/latest/Installation.html).

### Stable

Get the latest release via pip as
```shell
python -m pip install yt-astro-analysis
```

Or with conda, as
```shell
conda install -c conda-forge yt-astro-analysis
```

Note, the package name is spelled with hyphens (`yt-astro-analysis`)
when installing from pip or conda. With pip, the package name can be
spelled with either hyphens or underscores, but with conda it must
always be hyphens.

### From source

To build `yt_astro_analysis` from source, clone the git repository and install
as

```shell
git clone https://github.com/yt-project/yt_astro_analysis
cd yt_astro_analysis
python -m pip install -e .
```

### Installing with Rockstar support

In order to run the Rockstar halo finder from within yt_astro_analysis, it is
necessary to install yt_astro_analysis from source.
You will need to install `rockstar-galaxies` from either
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
python -m pip install -e .
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

```python
from yt.analysis_modules.ppv_cube.api import PPVCube
```
becomes
```python
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
