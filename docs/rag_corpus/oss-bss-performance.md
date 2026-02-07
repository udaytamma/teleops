# OSS/BSS System Performance Guide

## Overview

Operations and Business Support Systems for provisioning, billing, and activation in Cable/Telecom MSO environments. Covers subscriber management, service activation, and billing platforms.

## Symptoms

- **Alert type:** `provisioning_delay`, `billing_error`, `activation_failure`, `api_timeout`
- **Typical messages:**
  - "Provisioning queue depth >1000 pending orders"
  - "Billing batch job exceeded SLA: running >4 hours"
  - "CMTS provisioning timeout for MAC 00:11:22:33:44:55"
  - "Activation API response time >30s (threshold: 5s)"
  - "Subscriber data sync failure: CRM to billing"
- **Affected hosts:** oss-db-*, bss-app-*, prov-*, billing-*, crm-*

## Root Cause Indicators

### 1. Database Contention
- Long-running queries blocking provisioning transactions
- Connection pool exhaustion (max connections reached)
- Replication lag to read replicas (>30s)
- Lock contention on subscriber tables
- Index fragmentation causing slow queries

### 2. Integration Failures
- SOAP/REST API timeouts to CMTS provisioning
- Message queue backlog (RabbitMQ, Kafka, MQ Series)
- Middleware certificate expiry (TLS handshake failures)
- ESB transformation errors
- Stale cached data in integration layer

### 3. Batch Job Failures
- Nightly billing runs exceeding maintenance window
- ETL jobs failing due to data quality issues
- Report generation blocking OLTP transactions
- Backup jobs competing for I/O
- Insufficient batch job parallelism

## Diagnostic Steps

1. **Check database health:**
   - Active sessions and wait events
   - Lock chains and blocking queries
   - Connection pool status
   - Replication lag metrics
   - Query execution plans for slow queries

2. **Monitor API/integration health:**
   - Response times to network elements (CMTS, DOCSIS)
   - Message queue depths and consumer lag
   - Error rates by integration endpoint
   - Certificate expiration dates
   - Middleware connection pools

3. **Review provisioning pipeline:**
   - Order queue depth and age
   - Activation success/failure rates
   - Average provisioning time by service type
   - Retry queue size
   - Failed order root causes

4. **Analyze batch job status:**
   - Job execution times vs historical
   - Resource utilization during batch window
   - Job dependencies and sequencing
   - Error logs and failure counts

5. **Verify data consistency:**
   - CRM to billing data sync status
   - Subscriber count reconciliation
   - Service inventory accuracy
   - Equipment assignment validation

## Remediation

### Immediate Actions
- Kill blocking queries (with business approval)
- Scale up batch job resources temporarily
- Restart hung integration adapters
- Increase database connection pool
- Enable provisioning queue prioritization

### Long-term Actions
- Database query optimization (indexes, plans)
- Async provisioning architecture
- Separate OLTP and OLAP workloads
- Implement circuit breakers for integrations
- Modernize batch processing (streaming where possible)

## Related Scenarios

- `database_latency_spike` - General database performance issues
- `router_freeze` - When provisioning cannot reach CMTS
- `activation_failure` - Service activation specific issues
