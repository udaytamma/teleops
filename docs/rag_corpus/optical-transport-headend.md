# Optical Transport & Headend Connectivity Guide

## Overview

Fiber ring infrastructure connecting headends, hubs, and optical nodes in Cable MSO environments. Covers DWDM/ROADM systems, fiber plant, and headend connectivity.

## Symptoms

- **Alert type:** `fiber_alarm`, `dwdm_channel_down`, `ring_protection`, `optical_power_low`
- **Typical messages:**
  - "LOS detected on DWDM channel 34 to hub-west"
  - "Ring protection switch activated on metro-ring-2"
  - "Optical power below threshold on span 5-6"
  - "EDFA output power degraded on amp-node-12"
  - "Headend-to-hub fiber cut detected via OTDR"
- **Affected hosts:** dwdm-*, roadm-*, olt-*, headend-*, hub-*, edfa-*

## Root Cause Indicators

### 1. Fiber Cut
- Loss of Signal (LOS) on multiple wavelengths simultaneously
- OTDR trace showing reflectance spike at specific distance
- Correlated with dig activity or construction permits
- Weather event (ice storm, high winds, flooding)
- Vehicle accident near aerial plant

### 2. DWDM Equipment Failure
- EDFA (amplifier) output power degradation
- Transponder laser failure or wavelength drift
- ROADM express path blocked or misconfigured
- OSC (Optical Supervisory Channel) failure
- DCM (Dispersion Compensation Module) issues

### 3. Headend Power/Cooling
- Generator failover at headend facility
- HVAC failure causing thermal shutdown
- UPS battery exhaustion during extended outage
- PDU overload or circuit breaker trip
- Cooling fan failure in optical equipment

## Diagnostic Steps

1. **Check DWDM NMS for alarm correlation:**
   - Review active alarms across ring
   - Identify affected wavelengths/channels
   - Check protection switching status
   - Verify OSC communication

2. **Run OTDR test:**
   - Locate fiber fault distance
   - Identify type (break, bend, connector)
   - Compare with baseline trace
   - Dispatch based on distance calculation

3. **Verify ring protection state:**
   - Check working/protect path status
   - Verify switchover completed successfully
   - Confirm traffic rerouted properly
   - Monitor for protection flapping

4. **Check headend environmental:**
   - Temperature and humidity sensors
   - Power feed status (A/B feeds)
   - Generator fuel level and status
   - UPS battery capacity

5. **Review maintenance/construction:**
   - Check dig ticket database
   - Review planned maintenance windows
   - Correlate with construction permits
   - Check utility locate records

## Remediation

### Immediate Actions
- Confirm ring protection activated successfully
- Dispatch fiber team with OTDR and splice equipment
- Reroute critical traffic via alternate path
- Enable traffic prioritization on protected path
- Notify affected downstream systems

### Long-term Actions
- Implement fiber route diversity initiatives
- Maintain spare transponder inventory at hubs
- Enhanced physical security on critical fiber paths
- Deploy fiber monitoring with real-time OTDR
- Add redundant headend interconnects

## Related Scenarios

- `fiber_cut` - Direct fiber damage affecting services
- `router_freeze` - When optical issues cascade to routing
- `network_degradation` - Widespread impact from ring failure
