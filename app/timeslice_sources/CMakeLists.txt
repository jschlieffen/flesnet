
list(APPEND SOURCES "${CMAKE_BINARY_DIR}/config/GitRevision.cpp")
list(APPEND HEADERS "${PROJECT_SOURCE_DIR}/config/GitRevision.hpp")


list(APPEND SOURCES timeslice_sources.cpp)
list(APPEND HEADERS timeslice_sources.hpp)

add_executable(timeslice_sources main.cpp ${SOURCES} ${HEADERS})

target_include_directories(timeslice_sources
  SYSTEM PUBLIC		${Boost_INCLUDE_DIRS}
  PRIVATE 			${PROJECT_SOURCE_DIR}/config
  PUBLIC			${PROJECT_SOURCE_DIR}
)

# For lib/fles_ipc/TimesliceAutoSource.o:
target_link_libraries(timeslice_sources
  fles_ipc
  ${Boost_LIBRARIES}
  rt  
)

# Ensure warnings are enabled and standard is set:
target_compile_options(timeslice_sources PRIVATE -Wall -Wextra -pedantic -std=c++17)

# Ensure we have -Werror in the build:
target_compile_options(timeslice_sources PRIVATE -Werror)

message(STATUS "CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_SOURCE_DIR}")

install(TARGETS timeslice_sources DESTINATION bin)


