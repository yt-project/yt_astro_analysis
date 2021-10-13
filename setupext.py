import contextlib
import glob
import os
import subprocess
import sys
import tempfile
from distutils import log
from distutils.ccompiler import new_compiler
from distutils.errors import CompileError, LinkError
from distutils.sysconfig import customize_compiler

CCODE = """
#include <omp.h>
#include <stdio.h>
int main() {
  omp_set_num_threads(2);
  #pragma omp parallel
  printf("nthreads=%d\\n", omp_get_num_threads());
  return 0;
}
"""


@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """
    A context manager to temporarily redirect stdout or stderr

    e.g.:

    with stdchannel_redirected(sys.stderr, os.devnull):
        if compiler.has_function('clock_gettime', libraries=['rt']):
            libraries.append('rt')

    Code adapted from https://stackoverflow.com/a/17752455/1382869
    """

    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, "w")
        os.dup2(dest_file.fileno(), stdchannel.fileno())

        yield
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
        if dest_file is not None:
            dest_file.close()


def check_for_openmp():
    """Returns True if local setup supports OpenMP, False otherwise

    Code adapted from astropy_helpers, originally written by Tom
    Robitaille and Curtis McCully.
    """

    # See https://bugs.python.org/issue25150
    if sys.version_info[:3] == (3, 5, 0):
        return False

    # Create a temporary directory
    ccompiler = new_compiler()
    customize_compiler(ccompiler)

    tmp_dir = tempfile.mkdtemp()
    start_dir = os.path.abspath(".")

    if os.name == "nt":
        # TODO: make this work with mingw
        # AFAICS there's no easy way to get the compiler distutils
        # will be using until compilation actually happens
        compile_flag = "-openmp"
        link_flag = ""
    else:
        compile_flag = "-fopenmp"
        link_flag = "-fopenmp"

    try:
        os.chdir(tmp_dir)

        with open("test_openmp.c", "w") as f:
            f.write(CCODE)

        os.mkdir("objects")

        # Compile, link, and run test program
        with stdchannel_redirected(sys.stderr, os.devnull):
            ccompiler.compile(
                ["test_openmp.c"], output_dir="objects", extra_postargs=[compile_flag]
            )
            ccompiler.link_executable(
                glob.glob(os.path.join("objects", "*")),
                "test_openmp",
                extra_postargs=[link_flag],
            )
            output = (
                subprocess.check_output("./test_openmp")
                .decode(sys.stdout.encoding or "utf-8")
                .splitlines()
            )

        if "nthreads=" in output[0]:
            nthreads = int(output[0].strip().split("=")[1])
            if len(output) == nthreads:
                using_openmp = True
            else:
                log.warn(  # noqa: G010
                    "Unexpected number of lines from output of test "
                    "OpenMP program (output was %s)",
                    output,
                )
                using_openmp = False
        else:
            log.warn(  # noqa: G010
                "Unexpected output from test OpenMP " "program (output was %s)", output
            )
            using_openmp = False

    except (CompileError, LinkError):
        using_openmp = False
    finally:
        os.chdir(start_dir)

    if using_openmp:
        log.warn("Using OpenMP to compile parallel extensions")  # noqa: G010
    else:
        log.warn(  # noqa: G010
            "Unable to compile OpenMP test program so Cython\n"
            "extensions will be compiled without parallel support"
        )

    return using_openmp
