cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(PulmoSlicerAI)

set(EXTENSION_HOMEPAGE "https://github.com/pulmoslicer/PulmoSlicerAI")
set(EXTENSION_CATEGORY "Chest by bsquochoainew")
set(EXTENSION_CONTRIBUTORS "PulmoSlicer AI research team")
set(EXTENSION_DESCRIPTION "Research pulmonary CT reconstruction using TotalSegmentator outputs.")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "TotalSegmentator")

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(PulmoSlicerAI)

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})

