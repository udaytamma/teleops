# Residential DNS Resolver Operations Guide

## Overview

DNS resolver infrastructure serving residential and business subscribers in Cable/Telecom MSO environments. Includes caching resolvers, RDNS, and CDN steering services.

## Symptoms

- **Alert type:** `dns_timeout`, `resolver_overload`, `nxdomain_spike`, `cache_miss_high`
- **Typical messages:**
  - "DNS resolver response time >500ms on resolver-east-01"
  - "NXDOMAIN rate spike: 50K/min on resolver cluster"
  - "Query rate exceeds 500K QPS on resolver-west-02"
  - "Cache hit ratio dropped to 45% (threshold: 70%)"
  - "Upstream authoritative timeout: ns1.example.com"
- **Affected hosts:** resolver-*, rdns-*, cache-*, dns-*

## Root Cause Indicators

### 1. Resolver Overload
- CPU utilization >80% on resolver nodes
- Cache hit ratio dropping below 70%
- Upstream authoritative server timeout/errors
- Connection queue depth increasing
- Response latency P99 >1000ms

### 2. NXDOMAIN Storm
- Botnet/malware generating random subdomain queries
- Typosquatting campaign targeting popular domains
- Misconfigured CPE/IoT devices with hardcoded DNS
- DNS tunneling/exfiltration attempts
- Compromised modems in subscriber network

### 3. CDN Steering Issues
- EDNS Client Subnet (ECS) not propagating correctly
- Anycast routing problems affecting resolver selection
- Origin DNS misconfiguration for CDN records
- GeoIP database stale or incorrect
- CDN provider DNS changes not reflected

## Diagnostic Steps

1. **Check resolver health metrics:**
   - Query rate (QPS) per resolver node
   - Cache hit ratio trend (should be >70%)
   - Response latency percentiles (P50, P95, P99)
   - Error rate by response code (NXDOMAIN, SERVFAIL)

2. **Analyze query patterns:**
   - Top queried domains (identify anomalies)
   - Random subdomain detection (DGA patterns)
   - Source IP distribution (botnet indicators)
   - Query type distribution (A, AAAA, TXT, ANY)

3. **Verify upstream authoritative health:**
   - Response time to root/TLD servers
   - Authoritative server availability
   - DNSSEC validation failures
   - TCP fallback rate

4. **Check EDNS Client Subnet:**
   - Verify ECS configuration on resolvers
   - Test CDN steering for major providers
   - Check client subnet propagation logs

5. **Review rate limiting:**
   - Per-client query limits
   - Response rate limiting (RRL) effectiveness
   - Blocked/limited client count

## Remediation

### Immediate Actions
- Enable aggressive rate limiting on anomalous patterns
- Scale resolver cluster horizontally (add nodes)
- Blackhole known-bad domains via RPZ
- Increase cache TTL for popular content
- Failover to backup resolver cluster

### Long-term Actions
- Implement DNS-over-HTTPS (DoH) for subscribers
- Deploy Response Policy Zones (RPZ) for threat blocking
- Enhance monitoring with passive DNS analytics
- Implement machine learning for anomaly detection
- Add redundant upstream resolver paths

## Related Scenarios

- `dns_outage` - Complete resolver unavailability
- `ddos_edge` - When DNS infrastructure is DDoS target
- `security_incident` - Malware/botnet using DNS for C2
