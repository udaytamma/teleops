# WiFi & Managed Services Guide

## Overview

Managed WiFi services including residential pods (xFi), public hotspots, and business WiFi in Cable MSO environments. Covers controller management, RADIUS authentication, and mesh networking.

## Symptoms

- **Alert type:** `wifi_controller_down`, `radius_timeout`, `ap_offline`, `mesh_degradation`
- **Typical messages:**
  - "WiFi controller cluster failover initiated"
  - "RADIUS authentication timeout rate >10%"
  - "xFi pod offline for 1000+ subscribers"
  - "Hotspot AP unreachable at venue MALL-CENTRAL"
  - "Mesh backhaul degradation in node NG-456"
- **Affected hosts:** wifi-ctrl-*, ap-*, xfi-*, radius-*, hotspot-*

## Root Cause Indicators

### 1. Controller Infrastructure
- Controller cluster split-brain
- Database replication lag
- License exhaustion for APs
- API/management plane overload
- Certificate expiry for CAPWAP

### 2. RADIUS/Authentication
- RADIUS server overload
- AAA database connectivity
- EAP-TLS certificate issues
- Shared secret mismatch
- Accounting record backlog

### 3. Access Point Issues
- Firmware corruption after update
- PoE power budget exceeded
- Channel congestion/interference
- Mesh backhaul signal degradation
- CAPWAP tunnel failures

### 4. Subscriber CPE (xFi Pods)
- Cloud connectivity loss
- Mesh pairing failures
- Firmware update stuck
- Backhaul interference
- App provisioning errors

## Diagnostic Steps

1. **Check controller health:**
   - Cluster status and sync state
   - Database replication status
   - Active AP count vs licensed
   - CPU/memory utilization
   - API response times

2. **Verify RADIUS infrastructure:**
   - Server availability and latency
   - Authentication success/failure rates
   - EAP method distribution
   - Certificate validity dates
   - Accounting queue depth

3. **Analyze AP population:**
   - Online/offline AP counts by region
   - Channel utilization heatmaps
   - Client connection counts
   - Mesh link quality metrics
   - Firmware version distribution

4. **Review subscriber pods:**
   - Cloud registration status
   - Mesh topology health
   - Speed test results
   - App error logs
   - Provisioning state

5. **Check network connectivity:**
   - CAPWAP tunnel status
   - VLAN/subnet configuration
   - DHCP scope exhaustion
   - DNS resolution for cloud services

## Remediation

### Immediate Actions
- Failover to standby controller
- Add RADIUS server capacity
- Force AP firmware rollback
- Reset affected xFi pods remotely
- Enable local authentication fallback

### Long-term Actions
- Implement controller geo-redundancy
- Deploy RADIUS load balancing
- Automate AP health monitoring
- Add mesh topology optimization
- Improve xFi pod provisioning flow

## Related Scenarios

- `dns_outage` - Cloud service connectivity
- `database_latency_spike` - RADIUS database issues
- `network_degradation` - Backhaul capacity problems
