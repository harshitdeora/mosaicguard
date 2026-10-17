# MosaicGuard implementation and evidence

## Plan
1. Establish private repository, locked runtimes, owner authentication, encrypted vault, SQLite metadata and real FalkorDB connection.
2. Implement reviewed CSV imports, immutable scenario/rule snapshots and bounded graph candidate semantics.
3. Complete audit evidence, typed repairs, utility comparison, reproducible exports and release history.
4. Add durable jobs, recovery, deletion, bounded assistant and guided React interface.
5. Verify with unit/oracle tests, real graph integration, browser acceptance, benchmark and restore; document exact limits.

## Decisions
- Self-hosted Docker Compose; no hosted service or hackathon submission.
- Single owner and one serialized durable worker. All workspace endpoints require that owner session.
- Initial conservative ceiling: 1,000 records/file, 5,000/workspace, 50 columns, 2 MB/file. Larger limits will not be advertised without verification.
- Exact and composite joins use scoped HMAC keys; typed generalisation uses bounded interval compatibility, never HMAC ordering.
- All candidate counts are scoped evidence, never probabilities or anonymity guarantees.

## Evidence
- 2026-10-17: inspected empty workspace; Python 3.14, Node 22.19, Git 2.51 and Docker Engine 29.2 available. GitHub connector identifies harshitdeora.
- Implementation and verification ongoing. No completion claim yet.
