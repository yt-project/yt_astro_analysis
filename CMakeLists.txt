cmake_minimum_required(VERSION 3.18)
project(yt_astro_analysis LANGUAGES C)

include(GNUInstallDirs)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module NumPy)

set(YT_AA_NUMPY_DEFINITIONS
    NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
    NPY_TARGET_VERSION=NPY_1_19_API_VERSION
)

# Cython is a build dependency from pyproject.toml. Generate C sources in the
# build tree rather than modifying the source tree during a wheel build.
function(cythonize_to_c output_variable pyx_file)
    get_filename_component(module_name "${pyx_file}" NAME_WE)
    set(generated_c "${CMAKE_CURRENT_BINARY_DIR}/cython/${module_name}.c")
    get_filename_component(generated_dir "${generated_c}" DIRECTORY)
    file(MAKE_DIRECTORY "${generated_dir}")

    add_custom_command(
        OUTPUT "${generated_c}"
        COMMAND "${Python3_EXECUTABLE}" -m cython -3
                -o "${generated_c}"
                "${CMAKE_CURRENT_SOURCE_DIR}/${pyx_file}"
        DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${pyx_file}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        COMMENT "Cythonizing ${pyx_file}"
        VERBATIM
    )
    set(${output_variable} "${generated_c}" PARENT_SCOPE)
endfunction()

function(configure_python_extension target)
    target_include_directories(${target} PRIVATE ${Python3_NumPy_INCLUDE_DIRS})
    target_compile_definitions(${target} PRIVATE ${YT_AA_NUMPY_DEFINITIONS})
endfunction()

# PPV cube: Cython extension.
cythonize_to_c(PPV_UTILS_C
    yt_astro_analysis/ppv_cube/ppv_utils.pyx
)
Python3_add_library(ppv_utils MODULE WITH_SOABI "${PPV_UTILS_C}")
configure_python_extension(ppv_utils)
if(UNIX AND NOT APPLE)
    target_link_libraries(ppv_utils PRIVATE m)
endif()
install(TARGETS ppv_utils
    LIBRARY DESTINATION yt_astro_analysis/ppv_cube
    RUNTIME DESTINATION yt_astro_analysis/ppv_cube
)

# Enzo friends-of-friends halo finder.
Python3_add_library(EnzoFOF MODULE WITH_SOABI
    yt_astro_analysis/halo_analysis/halo_finding/fof/EnzoFOF.c
    yt_astro_analysis/halo_analysis/halo_finding/fof/kd.c
)
configure_python_extension(EnzoFOF)
if(UNIX AND NOT APPLE)
    target_link_libraries(EnzoFOF PRIVATE m)
endif()
install(TARGETS EnzoFOF
    LIBRARY DESTINATION yt_astro_analysis/halo_analysis/halo_finding/fof
    RUNTIME DESTINATION yt_astro_analysis/halo_analysis/halo_finding/fof
)

# Enzo HOP halo finder.
Python3_add_library(EnzoHop MODULE WITH_SOABI
    yt_astro_analysis/halo_analysis/halo_finding/hop/EnzoHop.c
    yt_astro_analysis/halo_analysis/halo_finding/hop/hop_hop.c
    yt_astro_analysis/halo_analysis/halo_finding/hop/hop_kd.c
    yt_astro_analysis/halo_analysis/halo_finding/hop/hop_regroup.c
    yt_astro_analysis/halo_analysis/halo_finding/hop/hop_slice.c
    yt_astro_analysis/halo_analysis/halo_finding/hop/hop_smooth.c
)
configure_python_extension(EnzoHop)
install(TARGETS EnzoHop
    LIBRARY DESTINATION yt_astro_analysis/halo_analysis/halo_finding/hop
    RUNTIME DESTINATION yt_astro_analysis/halo_analysis/halo_finding/hop
)

# Optional Rockstar support. The lookup order mirrors the former setup.py:
# rockstar.cfg first, then the Conda include directory. ROCKSTAR_ROOT can be
# passed explicitly to CMake and takes precedence over both.
option(YT_AA_BUILD_ROCKSTAR
    "Build the optional Rockstar extensions when Rockstar is available" ON)
set(ROCKSTAR_ROOT "" CACHE PATH
    "Path to the rockstar-galaxies installation/build directory")

if(YT_AA_BUILD_ROCKSTAR)
    if(NOT ROCKSTAR_ROOT AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/rockstar.cfg")
        file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/rockstar.cfg"
            ROCKSTAR_ROOT LIMIT_COUNT 1)
        string(STRIP "${ROCKSTAR_ROOT}" ROCKSTAR_ROOT)
    endif()

    if(NOT ROCKSTAR_ROOT AND DEFINED ENV{CONDA_PREFIX})
        set(_conda_rockstar "$ENV{CONDA_PREFIX}/include/rockstar-galaxies")
        if(EXISTS "${_conda_rockstar}")
            set(ROCKSTAR_ROOT "${_conda_rockstar}")
        endif()
    endif()

    if(ROCKSTAR_ROOT)
        find_library(ROCKSTAR_LIBRARY
            NAMES rockstar-galaxies
            PATHS "${ROCKSTAR_ROOT}" "${ROCKSTAR_ROOT}/lib"
            NO_DEFAULT_PATH
        )
        if(NOT ROCKSTAR_LIBRARY)
            message(FATAL_ERROR
                "ROCKSTAR_ROOT is '${ROCKSTAR_ROOT}', but "
                "librockstar-galaxies was not found in that directory "
                "or its lib/ subdirectory.")
        endif()

        foreach(module IN ITEMS rockstar_interface rockstar_groupies)
            cythonize_to_c(ROCKSTAR_${module}_C
                "yt_astro_analysis/halo_analysis/halo_finding/rockstar/${module}.pyx"
            )
            Python3_add_library(${module} MODULE WITH_SOABI
                "${ROCKSTAR_${module}_C}")
            configure_python_extension(${module})
            target_include_directories(${module} PRIVATE
                "${ROCKSTAR_ROOT}"
                "${ROCKSTAR_ROOT}/io"
                "${ROCKSTAR_ROOT}/util"
            )
            target_compile_definitions(${module} PRIVATE THREADSAFE)
            target_link_libraries(${module} PRIVATE "${ROCKSTAR_LIBRARY}")
            install(TARGETS ${module}
                LIBRARY DESTINATION yt_astro_analysis/halo_analysis/halo_finding/rockstar
                RUNTIME DESTINATION yt_astro_analysis/halo_analysis/halo_finding/rockstar
            )
        endforeach()
        message(STATUS "Building Rockstar extensions from ${ROCKSTAR_ROOT}")
    else()
        message(STATUS
            "Rockstar not found; skipping optional Rockstar extensions. "
            "Set ROCKSTAR_ROOT or add rockstar.cfg to enable them.")
    endif()
endif()
