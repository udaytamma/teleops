# MPLS VPN & Enterprise Services Guide

## Overview

MPLS L3VPN and Metro Ethernet services for business customers in Cable MSO environments. Covers VRF configuration, route leaks, and enterprise SLA management.

## Symptoms

- **Alert type:** `vrf_route_leak`, `mpls_label_error`, `pe_router_cpu`, `ce_unreachable`
- **Typical messages:**
  - "VRF route leak detected: customer prefix in global table"
  - "MPLS label exhaustion on pe-router-01"
  - "CE router unreachable for enterprise customer ACME-Corp"
  - "BGP session down between PE and CE for VRF:CUST-1234"
  - "Metro-E circuit utilization >95% on eline-biz-045"
- **Affected hosts:** pe-*, ce-*, mpls-*, metro-e-*, vpn-*

## Root Cause Indicators

### 1. VRF Route Leak
- Customer routes appearing in wrong VRF or global table
- Route target (RT) import/export misconfiguration
- Route distinguisher (RD) collision between customers
- MP-BGP extended community propagation errors
- VRF table corruption after software upgrade

### 2. MPLS Label Issues
- Label switching path (LSP) failure
- LDP session flapping between P/PE routers
- RSVP-TE tunnel down
- Label space exhaustion on PE router
- PHP (Penultimate Hop Popping) misconfiguration

### 3. Enterprise CE Connectivity
- PE-CE BGP/OSPF/EIGRP session down
- Access circuit failure (Ethernet handoff)
- CPE device failure or misconfiguration
- QoS policy mismatch causing drops
- MTU issues on MPLS path (jumbo frames)

## Diagnostic Steps

1. **Check VRF routing table:**
   - `show ip vrf detail <vrf-name>`
   - Verify RT import/export policies
   - Check for unexpected routes in VRF
   - Validate RD uniqueness across customers

2. **Verify MPLS label path:**
   - `show mpls forwarding-table`
   - `traceroute mpls ipv4 <destination>`
   - Check LDP neighbor status
   - Verify label range availability

3. **Analyze PE-CE relationship:**
   - BGP/IGP neighbor status
   - Route advertisement from CE
   - Access circuit status and counters
   - MTU configuration end-to-end

4. **Check enterprise SLA metrics:**
   - Latency, jitter, packet loss per VRF
   - Circuit utilization trends
   - QoS queue statistics
   - SLA violation history

5. **Review recent changes:**
   - VRF configuration changes
   - Route policy modifications
   - Software upgrades on PE/P routers
   - New customer provisioning

## Remediation

### Immediate Actions
- Isolate affected VRF to prevent leak propagation
- Clear BGP session to force route refresh
- Apply route-map to filter leaked prefixes
- Failover to backup PE if available
- Engage enterprise customer NOC

### Long-term Actions
- Implement VRF route leak detection automation
- Add RT/RD validation in provisioning workflow
- Deploy MPLS OAM for proactive monitoring
- Review and standardize VPN provisioning templates
- Implement customer-specific SLA dashboards

## Related Scenarios

- `router_freeze` - When PE router becomes unresponsive
- `bgp_flap` - PE-CE or PE-PE BGP instability
- `network_degradation` - When MPLS core is congested
