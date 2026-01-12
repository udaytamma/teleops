# Cost Estimate (Rough)

Estimates assume a demo workload with low traffic.

## Cloud Run (API)
- 1 vCPU / 512MB, minimal traffic
- Estimated monthly cost: $10 - $30

## Hosted LLM
- Gemini or similar pay-per-token model
- Estimated monthly cost: $20 - $60 for light demo usage

## Storage
- SQLite or small managed Postgres
- Estimated monthly cost: $5 - $20

## Total (Demo Scale)
- Estimated monthly cost: $35 - $110

## Notes
- Costs increase linearly with LLM usage and concurrent users.
- GPU hosting for local LLMs is excluded from this estimate.
