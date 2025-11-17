# NS-3 Development Guidelines

## Build Commands
- Build: `./build.py` (from ns-allinone-3.42 directory)
- Build with examples/tests: `./build.py --enable-examples --enable-tests`
- Configure ns-3: `python ns3 configure --enable-modules=core,network,internet,point-to-point,applications,flow-monitor,netanim,mobility`
- Build ns-3: `python ns3 build`
- Test: `python scripts/run_cycle.py` (from project directory)
- Run single test: `python scripts/run_cycle.py 1`
- Run example: `python scripts/run_cycle.py 3`
- Run simulation: `./ns3 run scratch/ns3_sim --topo=topology.json --routes=routing.json --anim=sim-anim.xml --metrics=metrics.csv`
- Run pipeline: `python3 scripts/run_cycle.py 3`

## Code Style Guidelines
- Language: C++ (primary), Python (ML components)
- Build system: CMake (minimum version 3.13)
- License: GPL v2 header required in all source files
- Naming: CamelCase for classes, lowerCamelCase for methods
- Includes: Use `#include "ns3/module-name.h"` format
- Error handling: Use NS_ASSERT, NS_ABORT_* macros
- Documentation: Doxygen comments required for public APIs
- Testing: Use ns-3 test framework with TEST_* macros
- Python: Use type hints, follow PEP 8, import pandas/networkx as needed
- Logging: Use NS_LOG_* macros for debug output
- File organization: src/module/{model,helper,test,examples} structure