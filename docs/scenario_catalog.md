# Scenario Catalog

Each scenario defines a synthetic alert pattern, a ground-truth root cause, and expected alert types.

| Scenario | Ground Truth | Expected Alerts |
| --- | --- | --- |
| `network_degradation` | Link congestion on core-router-1 | `packet_loss`, `high_latency` |
| `dns_outage` | Authoritative DNS cluster outage | `dns_timeout`, `servfail_spike`, `nx_domain_spike` |
| `bgp_flap` | Unstable BGP session with upstream AS | `bgp_session_flap`, `route_withdrawal` |
| `fiber_cut` | Fiber cut on metro ring segment | `link_down`, `loss_of_signal` |
| `router_freeze` | Control plane freeze on core-router-1 | `cpu_spike`, `control_plane_hang` |
| `isp_peering_congestion` | Congested ISP peering link | `high_latency`, `packet_loss` |
| `ddos_edge` | Volumetric DDoS at the edge | `traffic_spike`, `syn_flood` |
| `mpls_vpn_leak` | VRF misconfiguration leaking routes | `route_leak_detected`, `vrf_mismatch` |
| `cdn_cache_stampede` | Misconfigured TTLs causing cache stampede | `cache_miss_spike`, `origin_latency` |
| `firewall_rule_misconfig` | Firewall rule blocking critical port | `blocked_port`, `policy_violation` |
| `database_latency_spike` | Database contention in MSP apps | `query_latency`, `lock_waits` |

Notes:
- All scenarios inject tunable noise alerts for realism.
- Use the Scenario Builder to control alert rate, duration, and noise rate.
