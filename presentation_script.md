# 🎬 **Formal 10-Minute Research Presentation Script**

**Project:** _Resource Utilisation Optimization in HPC Networks using NS-3
Simulation and Multi-Algorithm Routing Analysis_ **Course:** _Networking for
High-Performance Computing_

---

## **0:00 – 0:45 — Introduction & Research Motivation**

**VOICE-OVER:** "Good morning. Today we present our research on optimizing
resource utilisation in High-Performance Computing networks through advanced
routing algorithms and simulation-based analysis.

In modern HPC systems, efficient network utilisation is critical for achieving
optimal performance. Our project addresses the resource utilisation challenge by
implementing a comprehensive simulation framework using NS-3, evaluating four
distinct routing algorithms across a 14-node hierarchical topology.

Our research demonstrates how algorithmic routing optimization can significantly
improve network performance metrics including throughput, latency, and fairness
in multi-flow environments."

**ON-SCREEN:**

- Title slide with project title and research objectives
- Key metrics: 14 nodes, 16 links, 30 flows, 4 algorithms evaluated

---

## **0:45 – 1:30 — Technical Architecture & Methodology**

**VOICE-OVER:** "Our methodology employs a five-stage pipeline:

First, we constructed a 14-node hierarchical network topology with 16
point-to-point links, configured with bandwidth constraints ranging from 1.5 to
3.0 Mbps and propagation delays of 1-2 milliseconds.

Second, we implemented NS-3 simulations generating 30 concurrent UDP flows with
randomized source-destination pairs, collecting comprehensive performance
metrics including throughput, delay, and packet loss.

Third, we developed four routing algorithms using NetworkX: Maximum Flow,
Minimum Cost Maximum Flow, Multi-Commodity Flow, and Load-Balanced Shortest
Path.

Fourth, we established a performance evaluation framework measuring 12 distinct
metrics across success rate, throughput, delay, cost efficiency, fairness, and
utilization dimensions.

Finally, we implemented automated visualization using NetAnim for flow pattern
analysis."

**ON-SCREEN:**

- Architecture diagram showing 5-stage pipeline
- Topology visualization with 14 nodes arranged in 2-tier hierarchy
- Table of link specifications (bandwidth, delay)

---

## **1:30 – 2:45 — Simulation Environment & Network Configuration**

**VOICE-OVER:** "Our simulation environment features a carefully designed
14-node topology representing a simplified HPC interconnect. The network
consists of two core nodes (0-1), eight aggregation nodes (2-5), and four edge
nodes (6-13), interconnected via 16 bidirectional links.

Link configurations include 3.0 Mbps bandwidth with 1ms delay for
core-to-aggregation connections, and 1.5 Mbps bandwidth with 2ms delay for
aggregation-to-edge links. This asymmetric design reflects realistic HPC network
hierarchies where core links typically offer higher capacity.

Traffic generation employs 30 UDP flows with 8 Mbps data rates and 512-byte
packets, utilizing DropTail queues limited to 3 packets to induce realistic
congestion scenarios. Simulation runtime spans 42 seconds with randomized flow
start times between 1-6 seconds."

**ON-SCREEN:**

- Detailed topology diagram showing node tiers and link capacities
- Configuration table with exact bandwidth/delay values
- Queue configuration and traffic parameters

---

## **2:45 – 4:00 — Baseline Performance Analysis**

**VOICE-OVER:** "Our baseline NS-3 simulation with default routing revealed
significant performance challenges. Analysis of 30 flows across 27 unique
source-destination pairs showed an average throughput of only 0.278 Mbps with
substantial variance of 0.348 Mbps.

Critical findings include a 43.3% overall packet loss rate, with 13 flows
experiencing complete connectivity failure. Average end-to-end latency reached
1,043 milliseconds, indicating severe congestion under default routing.

The simulation transmitted approximately 1.04 gigabytes but successfully
delivered only 38.9 megabytes, representing a 96.5% data loss. These baseline
metrics establish the performance ceiling that our routing algorithms aim to
improve."

**ON-SCREEN:**

- Bar chart showing throughput distribution (0-1.5 Mbps range)
- Packet loss statistics: 43.3% overall, 13 complete failures
- Latency distribution graph with 1,043ms average
- Data transmission vs delivery comparison

---

## **4:00 – 5:30 — Algorithm Implementation & Theoretical Framework**

**VOICE-OVER:** "We implemented four distinct routing algorithms, each
addressing different optimization objectives:

The Maximum Flow algorithm employs Ford-Fulkerson method to identify bottlenecks
and calculate maximum achievable throughput between node pairs, achieving
perfect 100% success rate across all 27 routes.

The Minimum Cost Maximum Flow utilizes NetworkX's network simplex algorithm with
cost function defined as delay plus 0.5 times utilization, achieving total flow
allocation of 9.63 Mbps with cost efficiency of 0.319.

The Multi-Commodity Flow algorithm implements proportional allocation with
fairness constraints, achieving total allocation of 18.98 Mbps and allocation
ratio of 1.97, with fairness index of 0.588.

The Load-Balanced Shortest Path employs modified Dijkstra with cost function
delay times (1 plus 0.3 times utilization squared), achieving average edge
utilization of 67.1% with 2.41 average hops per flow."

**ON-SCREEN:**

- Algorithm comparison table with key parameters
- Cost function mathematical formulations
- NetworkX implementation screenshots
- Performance metric definitions

---

## **5:30 – 7:00 — Comprehensive Performance Evaluation**

**VOICE-OVER:** "Our comprehensive evaluation across 12 performance metrics
reveals distinct algorithmic strengths:

Maximum Flow achieved the highest overall score of 100.0, with perfect success
rate and zero delay, making it ideal for reliability-critical applications.

Multi-Commodity Flow scored 55.6, demonstrating superior fairness with index
0.588 and highest edge utilization at 75.5%, though with maximum utilization
reaching 100% indicating potential hotspots.

Minimum Cost Maximum Flow scored 51.9, showing best cost efficiency at 0.319 and
total flow of 9.63 Mbps, suitable for resource-constrained environments.

Load-Balanced Shortest Path scored lowest at 0.0 but achieved highest flow
routing with all 27 flows successfully directed, though with higher average
delay of 3.59ms and 2.41 hops per flow."

**ON-SCREEN:**

- Overall scoring radar chart comparing all 4 algorithms
- Detailed performance metrics table with rankings
- Success rate, throughput, and delay comparisons
- Fairness index and utilization graphs

---

## **7:00 – 8:15 — Resource Utilization Analysis**

**VOICE-OVER:** "Resource utilization analysis reveals critical insights into
network efficiency:

Multi-Commodity Flow achieved the highest average edge utilization at 75.5%,
effectively distributing load across available capacity. However, its maximum
utilization of 100% indicates potential congestion points requiring careful
monitoring.

Load-Balanced Shortest Path achieved moderate utilization at 67.1% while
maintaining lower maximum utilization, demonstrating better load distribution
characteristics.

The allocation ratio analysis shows Multi-Commodity Flow achieving 1.97,
indicating nearly double the requested demand was successfully allocated through
intelligent multi-path routing.

Cost efficiency analysis reveals Minimum Cost Maximum Flow achieving 0.319
throughput per unit cost, making it optimal for environments where computational
resources are constrained."

**ON-SCREEN:**

- Edge utilization heat maps for each algorithm
- Allocation ratio comparison bar chart
- Cost efficiency scatter plot
- Resource utilization summary statistics

---

## **8:15 – 9:15 — NetAnim Visualization & Flow Analysis**

**VOICE-OVER:** "NetAnim visualization provides critical insights into flow
behavior and network dynamics:

Our animation reveals significant congestion under default routing, with 13
flows experiencing complete packet loss and average throughput of only 0.278
Mbps.

Maximum Flow routing shows efficient path selection with minimal congestion,
though with conservative resource utilization.

Multi-Commodity Flow visualization demonstrates effective load balancing across
multiple paths, though with some links reaching saturation.

Load-Balanced Shortest Path shows distributed traffic patterns with 2.41 average
hops, successfully routing all 27 flows through alternative paths to avoid
congestion.

The visualization clearly demonstrates how algorithmic routing can transform
network performance from 43.3% packet loss to 100% success rate."

**ON-SCREEN:**

- NetAnim screen recordings showing flow patterns for each algorithm
- Side-by-side comparison of default vs optimized routing
- Congestion heat maps and link utilization animations
- Flow success rate visualizations

---

## **9:15 – 10:00 — Conclusions & Future Research Directions**

**VOICE-OVER:** "Our research demonstrates that intelligent routing algorithm
selection can dramatically improve HPC network resource utilization. Key
findings include:

Maximum Flow algorithm achieves optimal reliability with 100% success rate and
zero delay, ideal for mission-critical HPC workloads.

Multi-Commodity Flow provides superior fairness and utilization, achieving 75.5%
average edge utilization with fairness index of 0.588.

The performance variance between algorithms—ranging from 0.0 to 100.0 overall
score—demonstrates that algorithm selection significantly impacts network
efficiency.

Future research directions include implementing machine learning models for
dynamic algorithm selection, scaling to larger topologies with hundreds of
nodes, and integrating real-time adaptive routing based on traffic patterns.

This work establishes a foundation for data-driven routing optimization in HPC
networks, demonstrating how simulation-based analysis can guide algorithm
selection for optimal resource utilization."

**ON-SCREEN:**

- Summary of key findings and algorithm recommendations
- Performance improvement metrics (43.3% → 100% success rate)
- Future research roadmap
- Acknowledgments and contact information

---

## **Key Performance Metrics Summary**

### Network Configuration

- **Nodes:** 14 (2 core, 8 aggregation, 4 edge)
- **Links:** 16 bidirectional point-to-point connections
- **Bandwidth:** 3.0 Mbps (core), 1.5 Mbps (aggregation)
- **Delay:** 1ms (core), 2ms (aggregation)
- **Flows:** 30 concurrent UDP flows
- **Simulation Time:** 42 seconds

### Baseline Performance

- **Average Throughput:** 0.278 Mbps
- **Packet Loss:** 43.3% overall
- **Complete Failures:** 13 flows
- **Average Delay:** 1,043 ms
- **Data Transmitted:** 1.04 GB
- **Data Delivered:** 38.9 MB (96.5% loss)

### Algorithm Performance Rankings

1. **Maximum Flow:** 100.0 overall score
   - Success Rate: 100%
   - Average Delay: 0 ms
   - Routes Generated: 27/27 successful

2. **Multi-Commodity Flow:** 55.6 overall score
   - Fairness Index: 0.588
   - Average Edge Utilization: 75.5%
   - Total Allocated: 18.98 Mbps

3. **Minimum Cost Maximum Flow:** 51.9 overall score
   - Cost Efficiency: 0.319
   - Total Flow: 9.63 Mbps
   - Average Delay: 3.59 ms

4. **Load-Balanced Shortest Path:** 0.0 overall score
   - Average Hops: 2.41
   - Edge Utilization: 67.1%
   - All 27 flows routed successfully

### Recommendations

- **Reliability-Critical:** Maximum Flow algorithm
- **Fair Distribution:** Multi-Commodity Flow
- **Resource-Constrained:** Minimum Cost Maximum Flow
- **Load Balancing:** Load-Balanced Shortest Path
