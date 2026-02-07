# Edge Security Incidents Guide

## Overview

Security threats targeting MSO edge infrastructure and subscriber CPE in Cable/Telecom environments. Covers DDoS mitigation, CPE security, and botnet detection.

## Symptoms

- **Alert type:** `ddos_detected`, `cpe_exploit`, `amplification_attack`, `botnet_c2`
- **Typical messages:**
  - "Volumetric DDoS detected: 400Gbps inbound on edge-rtr-01"
  - "SNMP amplification traffic from subscriber CPE segment"
  - "Botnet C2 communication detected to 198.51.100.0/24"
  - "Cable modem firmware exploit attempt: CVE-2024-XXXX"
  - "DNS amplification attack sourced from residential segment"
- **Affected hosts:** edge-rtr-*, scrubber-*, cpe-*, modem-*, firewall-*

## Root Cause Indicators

### 1. Volumetric DDoS
- Traffic asymmetry (inbound >> outbound significantly)
- Single destination IP under sustained attack
- Diverse source IPs (spoofed or botnet-originated)
- Protocol distribution anomaly (UDP flood, SYN flood)
- Bandwidth saturation on edge links

### 2. Reflection/Amplification
- Open DNS resolvers on CPE responding to queries
- SNMP, NTP, memcached amplification vectors
- Subscriber modems acting as amplifiers
- SSDP/UPnP reflection from IoT devices
- CharGEN/QOTD legacy protocol abuse

### 3. CPE Compromise
- Default credentials on cable modems exploited
- Firmware vulnerabilities allowing remote code execution
- IoT devices recruited into botnets (Mirai variants)
- TR-069/CWMP exploitation for mass configuration
- DNS hijacking via compromised modem settings

## Diagnostic Steps

1. **Analyze traffic patterns:**
   - NetFlow/sFlow analysis for attack vector
   - Top talkers by source/destination
   - Protocol distribution (UDP, TCP, ICMP)
   - Packet size distribution (amplification signatures)

2. **Check scrubbing center status:**
   - Verify BGP diversion to scrubbing
   - Monitor clean traffic return path
   - Check scrubbing capacity utilization
   - Review mitigation effectiveness

3. **Review CPE security posture:**
   - Firmware versions in affected area
   - Known vulnerabilities for deployed models
   - TR-069 configuration audit
   - Password policy compliance

4. **Correlate with threat intelligence:**
   - Match IPs against known botnet C2
   - Check for active exploit campaigns
   - Review vendor security advisories
   - Check abuse complaints/reports

5. **Identify attack target and motive:**
   - Victim IP/service identification
   - Attack timing correlation (gaming, financial)
   - Ransom/extortion communication
   - Competitor analysis if applicable

## Remediation

### Immediate Actions
- Engage upstream scrubbing or blackhole routing
- Apply ACLs to block known attack vectors
- Rate-limit vulnerable protocols at edge (UDP/53, UDP/123)
- Isolate compromised CPE segments
- Enable BGP Flowspec rules

### Long-term Actions
- Mandatory CPE firmware update program
- Deploy BCP38/BCP84 source validation
- Implement subscriber security awareness program
- Add NetFlow-based anomaly detection
- Enhance CPE default security (no default passwords)

## Related Scenarios

- `ddos_edge` - Sustained volumetric attacks on infrastructure
- `firewall_rule_misconfig` - When security rules block legitimate traffic
- `dns_outage` - When DNS infrastructure is attack target
