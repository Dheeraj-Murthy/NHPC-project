#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/netanim-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>
#include <vector>

using json = nlohmann::json;
using namespace ns3;

NS_LOG_COMPONENT_DEFINE("Ns3SimJson");

struct LinkSpec
{
    uint32_t src;
    uint32_t dst;
    std::string bw;
    std::string delay;
};

int
main(int argc, char* argv[])
{
    CommandLine cmd;
    std::string topoFile = "topology.json";
    std::string routeFile = "routing.json";
    std::string animFile = "sim-anim.xml";
    std::string metricsFile = "metrics.csv";
    uint32_t nFlows = 50;
    bool fastMode = false;

    cmd.AddValue("topo", "Topology JSON file", topoFile);
    cmd.AddValue("routes", "Routing JSON file (optional)", routeFile);
    cmd.AddValue("anim", "NetAnim XML output", animFile);
    cmd.AddValue("metrics", "CSV metrics output", metricsFile);
    cmd.AddValue("flows", "Number of random flows", nFlows);
    cmd.AddValue("fast", "Enable fast debug mode", fastMode);
    cmd.Parse(argc, argv);

    // Load topology JSON
    json topo;
    {
        std::ifstream in(topoFile);
        if (!in.is_open())
        {
            std::cerr << "Failed to open topology file: " << topoFile << "\n";
            return 1;
        }
        in >> topo;
    }

    uint32_t nNodes = topo.value("nodes", 0u);
    std::vector<LinkSpec> links;
    for (auto& l : topo["links"])
    {
        LinkSpec s;
        s.src = l["src"].get<uint32_t>();
        s.dst = l["dst"].get<uint32_t>();
        s.bw = l.value("bandwidth", "10Mbps");
        s.delay = l.value("delay", "10ms");
        links.push_back(s);
    }

    if (fastMode)
    {
        nFlows = std::min<uint32_t>(nFlows, 5);
        NS_LOG_UNCOND("[FAST MODE] Running with reduced complexity: " << nFlows << " flows");
    }

    // Create nodes
    NodeContainer nodes;
    nodes.Create(nNodes);

    InternetStackHelper internet;
    internet.Install(nodes);

    // Mobility
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(nodes);

    auto ipToStr = [](Ipv4Address addr) {
        std::ostringstream oss;
        addr.Print(oss);
        return oss.str();
    };

    // Links and IPs
    PointToPointHelper p2p;
    p2p.SetQueue("ns3::DropTailQueue",
                 "MaxSize",
                 StringValue("3p")); // Very small queue to force drops
    std::vector<NetDeviceContainer> devs;
    Ipv4AddressHelper ipv4;
    uint32_t subnetIndex = 1;

    std::vector<std::vector<std::string>> nodeIpv4Strings(nNodes);
    for (auto& lk : links)
    {
        p2p.SetDeviceAttribute("DataRate", StringValue(lk.bw));
        p2p.SetChannelAttribute("Delay", StringValue(lk.delay));
        NetDeviceContainer d = p2p.Install(NodeContainer(nodes.Get(lk.src), nodes.Get(lk.dst)));
        devs.push_back(d);

        std::ostringstream base;
        base << "10." << (subnetIndex / 256) << "." << (subnetIndex % 256) << ".0";
        ipv4.SetBase(base.str().c_str(), "255.255.255.0");
        Ipv4InterfaceContainer ifc = ipv4.Assign(d);

        nodeIpv4Strings[lk.src].push_back(ipToStr(ifc.GetAddress(0)));
        nodeIpv4Strings[lk.dst].push_back(ipToStr(ifc.GetAddress(1)));
        subnetIndex++;
    }

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // Flows - use routing.json flow pairs if available, otherwise random
    Ptr<UniformRandomVariable> rv = CreateObject<UniformRandomVariable>();
    uint16_t basePort = 9000;
    std::vector<std::pair<uint32_t, uint32_t>> flowPairs;

    // Optional routing.json - extract both static routes and flow pairs
    {
        std::ifstream rfs(routeFile);
        if (rfs.is_open())
        {
            json rj;
            try
            {
                rfs >> rj;

                // Extract flow pairs from routing.json if available
                if (rj.contains("routes"))
                {
                    for (auto& route : rj["routes"])
                    {
                        uint32_t src = route["src"];
                        uint32_t dst = route["dst"];
                        if (src < nNodes && dst < nNodes && src != dst)
                        {
                            flowPairs.emplace_back(src, dst);
                        }
                    }
                    NS_LOG_UNCOND("Using " << flowPairs.size() << " flow pairs from routing.json");
                }

                // Set up static routing
                if (rj.contains("routes"))
                {
                    Ipv4StaticRoutingHelper staticRoutingHelper;
                    for (auto& entry : rj["routes"])
                    {
                        uint32_t src = entry["src"];
                        uint32_t dst = entry["dst"];
                        uint32_t next = entry["next_hop"];
                        if (next >= nodeIpv4Strings.size() || dst >= nodeIpv4Strings.size())
                            continue;
                        if (nodeIpv4Strings[next].empty() || nodeIpv4Strings[dst].empty())
                            continue;

                        Ipv4Address dstAddr(nodeIpv4Strings[dst].front().c_str());
                        Ipv4Address nextHop(nodeIpv4Strings[next].front().c_str());

                        Ptr<Ipv4> ipv4ptr = nodes.Get(src)->GetObject<Ipv4>();
                        Ptr<Ipv4StaticRouting> staticRouting =
                            staticRoutingHelper.GetStaticRouting(ipv4ptr);
                        staticRouting->AddHostRouteTo(dstAddr, nextHop, 1);
                    }
                }
            }
            catch (...)
            {
                NS_LOG_WARN("Failed to parse routing.json");
            }
        }
    }

    // If no routes in json or not enough flows, generate random ones
    while (flowPairs.size() < (size_t)nFlows)
    {
        uint32_t a = rand() % nNodes;
        uint32_t b = rand() % nNodes;
        while (b == a)
            b = (b + 1) % nNodes;
        flowPairs.emplace_back(a, b);
    }

    // Limit to requested number of flows
    if (flowPairs.size() > (size_t)nFlows)
    {
        flowPairs.resize(nFlows);
    }

    // Create flows using the flow pairs
    for (size_t f = 0; f < flowPairs.size(); ++f)
    {
        uint32_t a = flowPairs[f].first;
        uint32_t b = flowPairs[f].second;

        if (nodeIpv4Strings[b].empty())
            continue;
        Ipv4Address dstIp(nodeIpv4Strings[b].front().c_str());

        uint16_t port = basePort + f;
        PacketSinkHelper sink("ns3::UdpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), port));
        ApplicationContainer sapps = sink.Install(nodes.Get(b));
        sapps.Start(Seconds(0.5));
        sapps.Stop(Seconds(fastMode ? 10.0 : 40.0));

        OnOffHelper onoff("ns3::UdpSocketFactory", Address(InetSocketAddress(dstIp, port)));
        onoff.SetConstantRate(
            DataRate(fastMode ? "2Mbps" : "8Mbps")); // Higher data rate for congestion
        onoff.SetAttribute("PacketSize", UintegerValue(512));

        ApplicationContainer apps = onoff.Install(nodes.Get(a));
        double start = 1.0 + rv->GetValue(0, 5); // Random start times for burst patterns
        apps.Start(Seconds(start));
        apps.Stop(Seconds(fastMode ? 9.0 : 38.0));
    }

    // Optional animation
    AnimationInterface* anim = nullptr;
    if (!fastMode)
    {
        anim = new AnimationInterface(animFile);
        anim->SetMaxPktsPerTraceFile(500000); // Increase trace buffer
        double spacing = 30.0;
        for (uint32_t i = 0; i < nNodes; ++i)
        {
            double x = (i % 6) * spacing + 10;
            double y = (i / 6) * spacing + 10;
            anim->SetConstantPosition(nodes.Get(i), x, y, 0.0);
        }
        anim->EnableIpv4RouteTracking("routes.xml", Seconds(0), Seconds(20), Seconds(5.0));
    }

    // Flow monitor
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    Simulator::Stop(Seconds(fastMode ? 12.0 : 42.0));
    Simulator::Run();

    // Collect metrics
    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
    auto stats = monitor->GetFlowStats();

    std::ofstream csv(metricsFile);
    csv << "flow_id,src_idx,dst_idx,src_ip,dst_ip,txPkts,rxPkts,txBytes,rxBytes,throughput_mbps,"
           "avg_delay_ms,loss_pct\n";
    for (auto& kv : stats)
    {
        FlowId id = kv.first;
        FlowMonitor::FlowStats fs = kv.second;
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(id);

        std::ostringstream srcOss, dstOss;
        t.sourceAddress.Print(srcOss);
        t.destinationAddress.Print(dstOss);

        std::string srcIp = srcOss.str(), dstIp = dstOss.str();
        int srcIdx = -1, dstIdx = -1;

        for (uint32_t n = 0; n < nodeIpv4Strings.size(); ++n)
        {
            for (auto& s : nodeIpv4Strings[n])
            {
                if (s == srcIp)
                    srcIdx = n;
                if (s == dstIp)
                    dstIdx = n;
            }
        }

        double duration = fs.timeLastRxPacket.GetSeconds() - fs.timeFirstTxPacket.GetSeconds();
        double throughput = (duration > 0.0) ? (fs.rxBytes * 8.0) / (duration * 1e6) : 0.0;
        double avgDelay =
            (fs.rxPackets > 0) ? (fs.delaySum.GetSeconds() / fs.rxPackets) * 1000.0 : 0.0;
        double lossPct =
            (fs.txPackets > 0) ? (fs.txPackets - fs.rxPackets) / fs.txPackets * 100.0 : 0.0;

        csv << id << "," << srcIdx << "," << dstIdx << "," << srcIp << "," << dstIp << ","
            << fs.txPackets << "," << fs.rxPackets << "," << fs.txBytes << "," << fs.rxBytes << ","
            << throughput << "," << avgDelay << "," << lossPct << "\n";
    }

    csv.close();
    monitor->SerializeToXmlFile("flowmon-results.xml", true, true);

    if (anim)
        delete anim;
    Simulator::Destroy();

    NS_LOG_UNCOND("Simulation complete → Metrics written to " << metricsFile);
    return 0;
}
