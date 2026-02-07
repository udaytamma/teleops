# Video & CDN Delivery Guide

## Overview

Video-on-Demand (VOD), linear channel delivery, and CDN infrastructure in Cable MSO environments. Covers origin servers, edge caches, transcoding, and adaptive bitrate streaming.

## Symptoms

- **Alert type:** `vod_origin_error`, `cache_miss_spike`, `abr_quality_drop`, `manifest_stale`
- **Typical messages:**
  - "VOD origin 5xx error rate >5% on origin-east-01"
  - "Cache miss ratio >40% on edge-cache-03 (threshold: 15%)"
  - "ABR bitrate downshift alerts for linear channel ESPN"
  - "Manifest generation latency >500ms (threshold: 100ms)"
  - "Transcoder queue depth >50 jobs (normal: <10)"
- **Affected hosts:** origin-*, edge-cache-*, transcoder-*, packager-*, encoder-*

## Root Cause Indicators

### 1. Origin Server Failure
- Storage system latency or I/O errors
- Transcoder/packager queue backup
- Origin server out of memory (OOM) or crash
- Content not found (404) for requested assets
- Origin CPU saturation during peak

### 2. Cache Stampede
- Popular content TTL expiry causing origin flood
- Cold cache after restart or deployment
- Manifest request storm during live events
- Cache key misconfiguration
- Cache purge without warming

### 3. ABR/Streaming Issues
- Segment generation delays (packager backlog)
- Manifest stale data (outdated playlist)
- Player-side buffering correlations
- Bitrate ladder mismatch
- DRM license server latency

## Diagnostic Steps

1. **Check origin server health:**
   - Storage I/O latency and queue depth
   - Origin CPU and memory utilization
   - HTTP error rates by response code
   - Active connection count
   - Origin request rate vs capacity

2. **Analyze cache metrics:**
   - Cache hit ratio trend (target >85%)
   - Popular content in cache (top-N)
   - Cache eviction rate
   - Time-to-first-byte (TTFB)
   - Cache storage utilization

3. **Review transcoding/packaging:**
   - Transcoder job queue depth
   - Packaging latency per profile
   - Segment generation timing
   - Encoder input health (SDI, IP)

4. **Examine CDN request patterns:**
   - Request distribution by edge location
   - Error rates by POP (point of presence)
   - Geographic distribution anomalies
   - Peak vs normal traffic comparison

5. **Correlate with content events:**
   - New content releases/premieres
   - Live event schedules (sports, news)
   - Promotional campaigns
   - Content catalog changes

## Remediation

### Immediate Actions
- Increase origin capacity or failover
- Prepopulate cache with trending content
- Extend TTL on frequently-requested manifests
- Scale transcoder fleet for queue reduction
- Enable origin shielding to reduce load

### Long-term Actions
- Implement origin shielding architecture
- Predictive cache warming before events
- Multi-CDN failover strategy
- Edge computing for personalization
- Improve monitoring with per-title metrics

## Related Scenarios

- `cdn_cache_stampede` - Mass cache invalidation events
- `database_latency_spike` - When VOD catalog database is slow
- `network_degradation` - When network issues affect video delivery
