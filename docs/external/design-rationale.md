# Design Rationale

## Contents
1. Correlation Parameters
2. Scenario Design Decisions
3. Alert Generation Rationale
4. LLM and RAG Parameters
5. Baseline RCA Design
6. Confidence Scoring
7. Data Model Choices
8. Evaluation Metrics

---

## 1. Correlation Parameters

The incident correlator groups alerts into incidents using time windows, count thresholds, and percentile-based noise filtering. These values are chosen to reflect telecom operations realities while keeping the MVP deterministic.

| Parameter | Value | Rationale |
| --- | --- | --- |
| `window_minutes` | 15 | Network incidents cascade within 5-15 minutes. A 15-minute window captures the full cascade without merging unrelated incidents. |
| `min_alerts` | 10 | Real incidents generate alert storms. A 10-alert minimum filters transient noise while keeping smaller outages visible. |
| `noise_rate_per_min` | 5 | Produces a 4:1 signal-to-noise ratio with the default incident rate, testing noise handling without overwhelming correlation. |
| `alert_rate_per_min` | 20 | Major incidents generate 10-50 alerts/minute. 20/minute for 10 minutes yields realistic load without breaking the demo. |
| `duration_min` | 10 | Represents the detection + diagnosis phase rather than full MTTR, focusing evaluation on RCA quality. |

### Noise Filtering (Percentile-Based)
Noise filtering is data-driven rather than tag-driven. For each correlation batch, the correlator computes alert counts per tag and drops tags at or below the 25th percentile after the `min_alerts` guardrail. If all tags have identical counts, the percentile filter is skipped to avoid dropping all incidents.

### Why Tag-Based Correlation (Not Time-Window Only)?

| Approach | Problem |
| --- | --- |
| Time-window only | Concurrent incidents merge into one, creating false correlations. |
| Host-based grouping | A single network event affects many hosts, producing fragmented incidents. |
| Tag-based (chosen) | Synthetic generator tags alerts deterministically, enabling reproducible evaluation. In production, this would be replaced by topology-aware correlation. |

---

## 2. Scenario Design Decisions

TeleOps supports 11 scenario types to represent distinct failure modes that require different RCA reasoning.

| Scenario | Why Included | RCA Challenge |
| --- | --- | --- |
| `network_degradation` | Most common incident type. Tests basic correlation. | Distinguish congestion from hardware failure. |
| `dns_outage` | High business impact with cascading failures. | Identify authoritative vs resolver failure. |
| `bgp_flap` | Routing instability affects the entire AS. | Distinguish internal vs external peer issue. |
| `fiber_cut` | Physical layer incident with different remediation. | Identify affected segment and reroute options. |
| `router_freeze` | Control plane vs data plane distinction. | Separate software hang from hardware failure. |
| `isp_peering_congestion` | External dependency, limited remediation. | Identify peer and traffic engineering options. |
| `ddos_edge` | Security incident with a different workflow. | Distinguish DDoS from legitimate traffic spikes. |
| `mpls_vpn_leak` | Common enterprise configuration failure. | Identify VRF and route target misconfiguration. |
| `cdn_cache_stampede` | Application-layer, MSP-relevant. | Distinguish TTL issues from origin failure. |
| `firewall_rule_misconfig` | Change-related incidents are common. | Identify rule and rollback path. |
| `database_latency_spike` | Application-layer for MSP customers. | Distinguish contention from resource exhaustion. |

### Why These Specific Hosts?
- `core-router-1/2`: Backbone traffic, redundant core pair.
- `edge-router-3`: Edge connectivity to customers/peers.
- `agg-switch-2`: Aggregation between core and edge.
- `pe-core-1/2`: Provider Edge routers for MPLS VPN.
- `dns-auth-1`, `dns-rec-1`: Authoritative vs recursive DNS split.

Trade-off: generic host names would be simpler but fail to demonstrate telecom domain realism.

---

## 3. Alert Generation Rationale

Each scenario generates alerts with specific types and severity based on common monitoring signals for that failure mode.

| Alert Type | Scenarios | Why This Alert? |
| --- | --- | --- |
| `packet_loss` | `network_degradation`, `isp_peering_congestion` | Universal congestion/failure symptom (SNMP, synthetic monitoring). |
| `high_latency` | `network_degradation`, `isp_peering_congestion` | Often precedes packet loss; common early warning signal. |
| `dns_timeout` | `dns_outage` | Resolver timeouts are a primary DNS failure symptom. |
| `servfail_spike` | `dns_outage` | SERVFAIL bursts indicate upstream DNS failures. |
| `nx_domain_spike` | `dns_outage` | Unexpected NXDOMAIN spikes often accompany DNS failures. |
| `bgp_session_flap` | `bgp_flap` | Core routing instability signal. |
| `route_withdrawal` | `bgp_flap` | Downstream symptom of peering instability. |
| `link_down` | `fiber_cut` | Physical link loss on transport layer. |
| `loss_of_signal` | `fiber_cut` | Optical NMS signal for fiber cuts. |
| `cpu_spike` | `router_freeze` | Control plane overload symptom. |
| `control_plane_hang` | `router_freeze` | Direct signal of control-plane failure. |
| `traffic_spike` | `ddos_edge` | DDoS volumetric indicator. |
| `syn_flood` | `ddos_edge` | Common attack pattern for edge devices. |
| `route_leak_detected` | `mpls_vpn_leak` | VPN route propagation errors. |
| `vrf_mismatch` | `mpls_vpn_leak` | VRF policy misconfiguration signal. |
| `cache_miss_spike` | `cdn_cache_stampede` | Stampede indicator at CDN edge. |
| `origin_latency` | `cdn_cache_stampede` | Origin saturation due to cache misses. |
| `blocked_port` | `firewall_rule_misconfig` | Blocked traffic due to policy change. |
| `policy_violation` | `firewall_rule_misconfig` | Firewall policy misconfiguration indicator. |
| `query_latency` | `database_latency_spike` | Symptom of DB contention. |
| `lock_waits` | `database_latency_spike` | Common DB latency root cause. |

### Why Critical Severity for Incident Alerts?
- Simplifies evaluation: no severity weighting in the MVP.
- Matches real incident patterns: critical alerts dominate during outages.
- Provides an extension point for severity-weighted correlation later.

Noise alerts use `warning` or `info` to simulate background chatter.

---

## 4. LLM and RAG Parameters

| Parameter | Value | Rationale |
| --- | --- | --- |
| `alerts_sample` | 20 alerts | Incidents can have 200+ alerts. Sampling first 20 keeps prompt size bounded without losing signal. |
| `output_format` | JSON only | Enables programmatic parsing, UI rendering, and evaluation. |
| `rag_context_chunks` | Top 4 | Balanced context depth vs latency and noise. |
| `constraints` | No commands | Safety guardrail to avoid hallucinated remediation commands. |

### Why Gemini 2.0 Flash (Default)?
Gemini 2.0 Flash is the default model in `teleops.config` for the MVP. The adapter pattern allows swapping to other providers without code changes. Measured local benchmark (2026-02-09) shows LLM p50 latency ~3150ms and p90 ~3912ms (see `storage/benchmarks/rca_latency.json`).

---

## 5. Baseline RCA Design

The baseline RCA is deterministic, rule-based, and exists for several reasons:

| Purpose | Explanation |
| --- | --- |
| Fallback | If the LLM fails (timeout, invalid JSON), baseline ensures an RCA is always available. |
| Comparison | Baseline is the benchmark; LLM must beat it to justify complexity. |
| Determinism | Reproducible output simplifies evaluation and debugging. |
| Speed | Baseline is millisecond-class vs LLM seconds; useful in time-critical incidents. |

### Why 0.55 Confidence for the Network Degradation Baseline?
- Above 0.5: indicates "probably right" rather than a guess.
- Below 0.7: leaves room for LLM to show improvement.
- Not 0.5 exactly: avoids implying a pure coin flip.

Note: baseline confidence values vary by rule (0.52-0.70 in current rules).

---

## 6. Confidence Scoring

Confidence scores guide operator trust and triage behavior.

| Score Range | Interpretation | Operator Action |
| --- | --- | --- |
| 0.8 - 1.0 | High confidence | Proceed with remediation; minimal additional validation. |
| 0.6 - 0.8 | Medium confidence | Verify with additional diagnostics. |
| 0.4 - 0.6 | Low confidence | Investigate further; consider alternatives. |
| 0.0 - 0.4 | Very low confidence | Do not act on this alone. |

### Why Multiple Hypotheses?
- Real incidents are ambiguous; symptoms can match multiple root causes.
- Operators need alternatives if the top hypothesis is wrong.
- The confidence distribution conveys uncertainty, not just a winner.

---

## 7. Data Model Choices

TeleOps uses three core entities: `Alert`, `Incident`, and `RCAArtifact`.

### Alert
- **Typed fields**: `source_system`, `host`, `service`, `severity`, `alert_type`, `timestamp`.
- **Flexible fields**: `tags` and `raw_payload` are JSON for schema agility.
- **Indexes**: `tenant_id`, `timestamp` for query performance.

### Incident
- **Correlation output**: `related_alert_ids`, `summary`, `severity`, `status`.
- **Metadata**: `impact_scope`, `owner`, `created_by`, `tenant_id`.
- **Index**: `tenant_id` for isolation.

### RCAArtifact
- **Outputs**: `hypotheses`, `evidence`, `confidence_scores` as JSON.
- **Metadata**: `llm_model`, `timestamp`, `duration_ms`, `status`, `reviewed_by`, `reviewed_at`.
- **Index**: `incident_id` for fast lookup.

### Why JSON Fields?
JSON fields allow scenario-specific evidence and hypotheses without schema migrations. Core fields remain typed for performance and stability.

### Why SQLite (Not Postgres)?
- Local-first: no external dependency for demos.
- Sufficient for MVP: thousands of alerts fit easily.
- ORM compatibility: migrating to Postgres is straightforward later.

---

## 8. Evaluation Metrics

TeleOps evaluates RCA quality using semantic similarity between hypothesis and ground truth.

| Metric | What It Measures | Target | Notes |
| --- | --- | --- | --- |
| RCA accuracy | % of hypotheses meeting similarity threshold | >= 0.75 | Correct threshold is 0.75 similarity. |
| LLM vs baseline delta | Improvement over baseline | >= 0.10 | Target; currently not met. |
| P50 latency | Median RCA time | < 3s | Measured p50 LLM ~3150ms on 2026-02-09. |
| P90 latency | Tail RCA time | < 10s | Measured p90 LLM ~3912ms on 2026-02-09. |
| JSON validity | % of LLM responses parsed | > 95% | Enforced by parser; not separately measured. |
| Unsafe suggestion rate | % of RCAs with risky commands | 0% | Enforced by prompt constraints. |

### Why Semantic Similarity (Not String Matching)?
The evaluation uses cosine similarity over sentence-transformer embeddings. This captures paraphrases and reduces false negatives compared to string similarity. Thresholds and metrics are recorded in `storage/evaluation_results.json`.

---

*Every parameter in TeleOps is derived from telecom operations reality: 15-minute correlation windows match incident cascade timelines, 10-alert minimums filter transient noise, and percentile-based filtering adapts to each batch.*
