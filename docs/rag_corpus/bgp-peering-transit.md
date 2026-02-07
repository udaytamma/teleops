# BGP Peering & Transit Operations Guide

## Overview

BGP sessions with Internet Exchange (IX) peers and transit providers in Cable/Telecom MSO environments. Covers peering management, route policy, and traffic engineering.

## Symptoms

- **Alert type:** `bgp_down`, `route_withdrawal`, `as_path_anomaly`, `prefix_hijack`
- **Typical messages:**
  - "BGP session down with AS174 (Cogent) on edge-rtr-01"
  - "Route withdrawal for customer prefix 192.0.2.0/24"
  - "AS-path prepend detected from upstream peer"
  - "Unexpected origin AS for prefix 203.0.113.0/24"
  - "BGP session flapping: 5 state changes in 10 minutes"
- **Affected hosts:** edge-rtr-*, pe-*, ix-*, border-*

## Root Cause Indicators

### 1. Session Flapping
- Hold timer expiry due to network congestion
- Authentication failure (MD5 key mismatch/expiry)
- Physical interface issues on peering link
- MTU mismatch causing packet drops
- Control plane congestion on router

### 2. Route Leak/Hijack
- Unexpected AS appearing in path
- More-specific prefix from unauthorized origin
- Customer leaking full routing table
- Peer advertising routes not covered by IRR
- Missing or incorrect RPKI ROA

### 3. Transit Congestion
- Interface utilization >85% on transit links
- Packet drops on egress queue
- Asymmetric routing causing latency increase
- Single transit provider overloaded
- IX port saturation

## Diagnostic Steps

1. **Check BGP neighbor status:**
   - `show bgp neighbors <peer-ip>`
   - Verify state (Established, Active, Idle)
   - Check uptime and last state change
   - Review hold time and keepalive settings

2. **Verify prefix advertisements:**
   - `show bgp neighbor <peer> advertised-routes`
   - `show bgp neighbor <peer> received-routes`
   - Compare against expected prefix list
   - Check community tagging

3. **Analyze AS-path:**
   - Review BGP update history
   - Check for unexpected AS in path
   - Verify AS-path prepending policy
   - Look for route leaks via looking glass

4. **Check interface health:**
   - Interface counters (errors, drops, CRC)
   - Utilization percentage (in/out)
   - Queue depth and drops
   - Optical levels if applicable

5. **External verification:**
   - Query peer's looking glass
   - Check RIPE RIS/RouteViews
   - Verify RPKI validation status
   - Review IRR objects

## Remediation

### Immediate Actions
- Failover to backup transit provider
- Apply prefix filters to block route leaks
- Engage NOC at affected peer/IX
- Adjust local-preference to shift traffic
- Enable BGP graceful restart if available

### Long-term Actions
- Implement RPKI/ROA validation
- Deploy BGP Flowspec for traffic steering
- Add redundant IX connections
- Automate IRR object maintenance
- Implement BGP session monitoring with alerts

## Related Scenarios

- `bgp_flap` - Rapid BGP session state changes
- `isp_peering_congestion` - Transit link saturation
- `network_degradation` - When routing issues cause widespread impact
