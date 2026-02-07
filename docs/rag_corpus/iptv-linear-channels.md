# IPTV & Linear Channel Delivery Guide

## Overview

Linear television and IPTV services in Cable MSO environments. Covers QAM delivery, multicast distribution, set-top box management, and channel blackouts.

## Symptoms

- **Alert type:** `channel_blackout`, `multicast_failure`, `stb_mass_reboot`, `qam_error`
- **Typical messages:**
  - "Linear channel ESPN blackout affecting 50K subscribers"
  - "Multicast tree failure for group 239.1.1.100"
  - "Mass STB reboot event in headend region EAST"
  - "QAM modulator error rate >1E-6 on qam-shelf-12"
  - "IGMP join failures exceeding threshold"
- **Affected hosts:** qam-*, stb-*, encoder-*, multicast-*, headend-*

## Root Cause Indicators

### 1. QAM/RF Delivery Issues
- QAM modulator hardware failure
- RF combining network problems
- Edge QAM configuration errors
- Frequency collision/interference
- Signal level issues in HFC plant

### 2. Multicast Distribution Failure
- PIM neighbor adjacency down
- IGMP snooping misconfiguration
- Multicast routing table corruption
- RP (Rendezvous Point) unreachable
- Multicast storm from STB

### 3. Set-Top Box Issues
- Mass firmware update failure
- Guide data (EPG) corruption
- Conditional access (CA) errors
- HDCP handshake failures
- DVR recording conflicts

### 4. Source/Encoder Problems
- Satellite receiver loss of signal
- Encoder hardware failure
- SDI input signal loss
- Transcoding quality issues
- Audio/video sync problems

## Diagnostic Steps

1. **Check channel source:**
   - Satellite receiver lock status
   - Encoder input and output health
   - SDI/ASI signal integrity
   - Source switching status

2. **Verify QAM delivery:**
   - QAM modulator status and alarms
   - RF output levels and MER
   - Transport stream PID analysis
   - Edge QAM configuration audit

3. **Analyze multicast path:**
   - PIM neighbor table
   - Multicast routing table (mroute)
   - IGMP group membership
   - RP reachability

4. **Review STB population:**
   - STB online/offline counts by region
   - Firmware version distribution
   - CA entitlement status
   - Error code analysis from STB logs

5. **Check headend systems:**
   - Video server health
   - Guide data ingest status
   - Conditional access system
   - Ad insertion platform

## Remediation

### Immediate Actions
- Switch to backup source/encoder
- Restart affected QAM modulators
- Force multicast tree rebuild
- Push emergency STB reboot command
- Bypass ad insertion if causing issues

### Long-term Actions
- Implement multicast monitoring
- Add encoder/source redundancy
- Deploy proactive STB health checks
- Upgrade to IP-based video delivery
- Automate channel failover

## Related Scenarios

- `fiber_cut` - When headend connectivity is lost
- `cdn_cache_stampede` - VOD component failures
- `network_degradation` - Multicast affected by congestion
