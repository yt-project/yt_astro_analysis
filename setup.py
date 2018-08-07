import os
import glob
import sys
from sys import platform as _platform
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
from setuptools.command.build_py import build_py as _build_py
from setupext import \
    check_for_openmp, check_for_pyembree, read_embree_location, \
    in_conda_env
from distutils.version import LooseVersion
import pkg_resources


if sys.version_info < (2, 7):
    print("yt currently requires Python version 2.7")
    print("certain features may fail unexpectedly and silently with older versions.")
    sys.exit(1)

try:
    distribute_ver = \
        LooseVersion(pkg_resources.get_distribution("distribute").version)
    if distribute_ver < LooseVersion("0.7.3"):
        print("Distribute is a legacy package obsoleted by setuptools.")
        print("We strongly recommend that you just uninstall it.")
        print("If for some reason you cannot do it, you'll need to upgrade it")
        print("to latest version before proceeding:")
        print("    pip install -U distribute")
        sys.exit(1)
except pkg_resources.DistributionNotFound:
    pass  # yay!

VERSION = "0.0.1"

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')


if check_for_openmp() is True:
    omp_args = ['-fopenmp']
else:
    omp_args = None

if os.name == "nt":
    std_libs = []
else:
    std_libs = ["m"]

cython_extensions = [
    Extension("yt_astro_analysis.ppv_cube.ppv_utils",
              ["yt_astro_analysis/ppv_cube/ppv_utils.pyx"],
              libraries=std_libs),
]

extensions = [
    Extension("yt_astro_analysis.halo_finding.fof.EnzoFOF",
              ["yt_astro_analysis/halo_finding/fof/EnzoFOF.c",
               "yt_astro_analysis/halo_finding/fof/kd.c"],
              libraries=std_libs),
    Extension("yt_astro_analysis.halo_finding.hop.EnzoHop",
              glob.glob("yt_astro_analysis/halo_finding/hop/*.c")),
]

# ROCKSTAR
if os.path.exists("rockstar.cfg"):
    try:
        rd = open("rockstar.cfg").read().strip()
    except IOError:
        print("Reading Rockstar location from rockstar.cfg failed.")
        print("Please place the base directory of your")
        print("Rockstar install in rockstar.cfg and restart.")
        print("(ex: \"echo '/path/to/Rockstar-0.99' > rockstar.cfg\" )")
        sys.exit(1)

    rockstar_extdir = "yt_astro_analysis/halo_finding/rockstar"
    rockstar_extensions = [
        Extension("yt_astro_analysis.halo_finding.rockstar.rockstar_interface",
                  sources=[os.path.join(rockstar_extdir, "rockstar_interface.pyx")]),
        Extension("yt_astro_analysis.halo_finding.rockstar.rockstar_groupies",
                  sources=[os.path.join(rockstar_extdir, "rockstar_groupies.pyx")])
    ]
    for ext in rockstar_extensions:
        ext.library_dirs.append(rd)
        ext.libraries.append("rockstar")
        ext.define_macros.append(("THREADSAFE", ""))
        ext.include_dirs += [rd,
                             os.path.join(rd, "io"), os.path.join(rd, "util")]
    extensions += rockstar_extensions

# class build_py(_build_py):
#     def run(self):
#         # honor the --dry-run flag
#         if not self.dry_run:
#             target_dir = os.path.join(self.build_lib, 'yt')
#             src_dir = os.getcwd()
#             changeset = get_mercurial_changeset_id(src_dir)
#             self.mkpath(target_dir)
#             with open(os.path.join(target_dir, '__hg_version__.py'), 'w') as fobj:
#                 fobj.write("hg_version = '%s'\n" % changeset)
#         _build_py.run(self)

#     def get_outputs(self):
#         # http://bitbucket.org/yt_analysis/yt/issues/1296
#         outputs = _build_py.get_outputs(self)
#         outputs.append(
#             os.path.join(self.build_lib, 'yt', '__hg_version__.py')
#         )
#         return outputs


class build_ext(_build_ext):
    # subclass setuptools extension builder to avoid importing cython and numpy
    # at top level in setup.py. See http://stackoverflow.com/a/21621689/1382869
    def finalize_options(self):
        from Cython.Build import cythonize
        self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules)
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process
        # see http://stackoverflow.com/a/21621493/1382869
        if isinstance(__builtins__, dict):
            # sometimes this is a dict so we need to check for that
            # https://docs.python.org/3/library/builtins.html
            __builtins__["__NUMPY_SETUP__"] = False
        else:
            __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

class sdist(_sdist):
    # subclass setuptools source distribution builder to ensure cython
    # generated C files are included in source distribution.
    # See http://stackoverflow.com/a/18418524/1382869
    def run(self):
        # Make sure the compiled Cython files in the distribution are up-to-date
        from Cython.Build import cythonize
        cythonize(cython_extensions)
        _sdist.run(self)

setup(
    name="yt_astro_analysis",
    version=VERSION,
    description="yt astrophysical analysis modules extension",
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Environment :: Console",
                 "Intended Audience :: Science/Research",
                 "License :: OSI Approved :: BSD License",
                 "Operating System :: MacOS :: MacOS X",
                 "Operating System :: POSIX :: AIX",
                 "Operating System :: POSIX :: Linux",
                 "Programming Language :: C",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.4",
                 "Programming Language :: Python :: 3.5",
                 "Topic :: Scientific/Engineering :: Astronomy",
                 "Topic :: Scientific/Engineering :: Physics",
                 "Topic :: Scientific/Engineering :: Visualization"],
    keywords='astronomy astrophysics visualization ' +
    'amr adaptivemeshrefinement',
    entry_points={},
    packages=find_packages(),
    include_package_data = True,
    setup_requires=[
        'numpy',
        'cython>=0.24',
    ],
    install_requires=[
        'h5py',
        'matplotlib',
        'setuptools>=19.6',
        'sympy',
        'numpy',
        'IPython',
        'cython',
        'yt>=3.3.5',
    ],
    extras_require = {
        'hub':  ["girder_client"]
    },
    cmdclass={'sdist': sdist, 'build_ext': build_ext},
    author="The yt project",
    author_email="yt-dev@python.org",
    url="http://yt-project.org/",
    license="BSD",
    zip_safe=False,
    scripts=[],
    ext_modules=cython_extensions + extensions,
)
