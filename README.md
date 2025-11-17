Project structure:

- topology.json (input topology)
- routing.json (routing suggestions for simulation)
- ns3_sim.cc (ns-3 simulation; reads topology & routing; writes metrics.csv)
- run_individual_models.py (runs all routing models and generates comparisons)

Setup:

- Ensure ns-3 is built with these modules: flow-monitor, netanim, mobility,
  applications, point-to-point, internet

./ns3 configure
--enable-modules=core,network,internet,point-to-point,applications,flow-monitor,netanim,mobility
./ns3 build

- Put nlohmann/json.hpp somewhere in include path (or next to ns3_sim.cc).
- Install Python deps: pip3 install networkx pandas

To run the entire pipeline with all routing models and generate comparison
metrics: python3 run_individual_models.py
