
list(APPEND SOURCES "${CMAKE_BINARY_DIR}/config/GitRevision.cpp")
list(APPEND HEADERS "${PROJECT_SOURCE_DIR}/config/GitRevision.hpp")


list(APPEND SOURCES memory_test.cpp)
list(APPEND HEADERS memory_test.hpp)

add_executable(memory_test main.cpp ${SOURCES} ${HEADERS})

target_include_directories(memory_test
  SYSTEM PUBLIC		${Boost_INCLUDE_DIRS}
  PRIVATE 			${PROJECT_SOURCE_DIR}/config
  PUBLIC			${PROJECT_SOURCE_DIR}
)

# For lib/fles_ipc/TimesliceAutoSource.o:
target_link_libraries(memory_test
  fles_ipc
  ${Boost_LIBRARIES}
  rt  
)

# Ensure warnings are enabled and standard is set:
target_compile_options(memory_test PRIVATE -Wall -Wextra -pedantic -std=c++17)

# Ensure we have -Werror in the build:
target_compile_options(memory_test PRIVATE -Werror)

message(STATUS "CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_SOURCE_DIR}")

install(TARGETS memory_test DESTINATION bin)


