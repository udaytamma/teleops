# HFC Network & CMTS Troubleshooting Guide

## Overview

Hybrid Fiber-Coax (HFC) network issues affecting DOCSIS cable modems and CMTS infrastructure in Cable MSO environments.

## Symptoms

- **Alert type:** `cmts_offline`, `docsis_error`, `rf_degradation`, `modem_offline`
- **Typical messages:**
  - "CMTS linecard offline on cmts-hub01"
  - "High uncorrectable errors on downstream channel"
  - "RF ingress detected on node N-1234"
  - "Upstream SNR below threshold on US-CH3"
  - "Mass modem offline event: 500+ modems in node group NG-456"
- **Affected hosts:** cmts-*, node-*, amp-*, modem-*, hub-*

## Root Cause Indicators

### 1. CMTS Hardware Failure
- Linecard CPU utilization >90%
- Memory exhaustion on supervisor module
- Upstream/downstream channel flapping
- Multiple modems going offline simultaneously on same linecard
- DOCSIS timing errors increasing

### 2. RF Plant Issues
- SNR degradation (<25dB downstream, <20dB upstream)
- High pre-RS/post-RS uncorrectable errors (FEC failures)
- Ingress noise spikes (common 5-42MHz range for upstream)
- MER (Modulation Error Ratio) below threshold
- Power level variations outside -15 to +15 dBmV range

### 3. Node/Amplifier Failure
- Power supply issues in field equipment
- Temperature alarms on optical nodes
- Fiber cut between headend and node
- Amplifier cascade failure
- Optical receiver sensitivity degradation

## Diagnostic Steps

1. **Check CMTS linecard status:**
   - `show linecard status`
   - `show cable modem summary`
   - Verify upstream/downstream channel utilization

2. **Review RF levels and quality:**
   - `show cable interface spectrum`
   - Check downstream power levels (-15 to +15 dBmV)
   - Verify upstream SNR (target >25dB)
   - Review FEC error counters

3. **Analyze modem population:**
   - Count offline modems by node/service group
   - Check registration failure reasons
   - Review partial service modems

4. **Check node power status:**
   - Query SCADA/HFC monitoring system
   - Verify node transponder readings
   - Check optical power levels at node

5. **Correlate with external factors:**
   - Review field tech dispatch history
   - Check weather conditions (temperature, moisture)
   - Verify recent plant maintenance activities

## Remediation

### Immediate Actions
- Failover to standby linecard if available
- Isolate affected node segment via RF switching
- Dispatch field tech for plant inspection
- Adjust downstream power levels if within range
- Enable ingress cancellation if available

### Long-term Actions
- Proactive sweep testing schedule (monthly)
- Node splitting for capacity relief
- Upgrade aging amplifiers to GaN technology
- Implement proactive network monitoring (PNM)
- Deploy DOCSIS 3.1 for improved noise immunity

## Related Scenarios

- `fiber_cut` - When fiber ring to node is affected
- `network_degradation` - Widespread service impact across multiple nodes
- `router_freeze` - When CMTS becomes unresponsive
