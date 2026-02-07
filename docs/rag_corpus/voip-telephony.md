# VoIP & Telephony Services Guide

## Overview

Voice over IP services including residential phone (MTA), business SIP trunks, and E911 in Cable MSO environments. Covers call quality, provisioning, and regulatory compliance.

## Symptoms

- **Alert type:** `mta_offline`, `sip_registration_fail`, `e911_routing_error`, `mos_degradation`
- **Typical messages:**
  - "MTA registration failure rate >5% in node group NG-789"
  - "SIP trunk down for business customer BIZ-5678"
  - "E911 ALI database sync failure"
  - "MOS score <3.5 on calls through softswitch-02"
  - "RTP packet loss >2% on voice gateway vgw-east-01"
- **Affected hosts:** mta-*, sip-*, softswitch-*, vgw-*, e911-*

## Root Cause Indicators

### 1. MTA Registration Issues
- DHCP/TFTP failures for MTA provisioning
- PacketCable/DOCSIS configuration file errors
- MTA firmware incompatibility
- HFC plant issues affecting voice modems
- Softswitch capacity limits reached

### 2. Call Quality Degradation
- Jitter >30ms on voice path
- Packet loss >1% causing audio artifacts
- One-way audio (NAT/firewall issues)
- Echo or audio delay complaints
- Codec negotiation failures

### 3. E911 Compliance Issues
- ALI (Automatic Location Identification) database stale
- PSAP routing errors
- Callback number incorrect
- Location validation failures
- Selective router connectivity

### 4. SIP Trunk Failures
- SIP registration timeout
- Authentication failures (401/407)
- Onesession border controller overload
- TLS certificate expiry
- Onesystem trunk group exhaustion

## Diagnostic Steps

1. **Check MTA status:**
   - Registration state on softswitch
   - DOCSIS modem status (online, partial)
   - Configuration file download logs
   - Voice line provisioning in OSS

2. **Analyze call quality metrics:**
   - MOS scores by region/node
   - Jitter and packet loss statistics
   - RTP stream analysis
   - Codec usage distribution

3. **Verify E911 compliance:**
   - ALI database last sync time
   - Test call to PSAP (non-emergency)
   - Location validation audit
   - Selective router connectivity

4. **Review SIP infrastructure:**
   - SBC session counts and capacity
   - SIP registration success rate
   - Onesession border controller logs for errors
   - DNS SRV record resolution

5. **Check network path:**
   - QoS marking (DSCP EF for voice)
   - Voice VLAN configuration
   - Firewall rules for SIP/RTP
   - NAT traversal settings

## Remediation

### Immediate Actions
- Restart affected MTA via SNMP reset
- Failover to backup softswitch
- Force E911 ALI database resync
- Bypass problematic SBC path
- Apply emergency QoS policy

### Long-term Actions
- Upgrade MTA firmware fleet-wide
- Implement voice quality monitoring (VQM)
- Automate E911 compliance testing
- Add SBC redundancy
- Deploy HD voice codecs (G.722, Opus)

## Related Scenarios

- `hfc_network_degradation` - When HFC issues affect MTAs
- `dns_outage` - SIP resolution failures
- `database_latency_spike` - Provisioning system delays
