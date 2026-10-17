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
- Created private GitHub repository `harshitdeora/mosaicguard`; initial architecture committed and pushed.
- Implemented encrypted metadata/vault, Argon2 owner authentication, protected cookies/CSRF, login throttling and one-process lease.
- Implemented reviewed arbitrary CSV import, immutable versions, roles, typed mappings, scoped scenario snapshots and real parameterised FalkorDB projections.
- Implemented bounded exact/composite/interval candidate sets, independent paths, explicit knowledge bundles, within-file diagnostics, history and release-addition comparisons.
- Implemented declarative repair branches, complete eligible re-audits, utility drift/retention comparisons, content-bound reproducible ZIPs, formula transport verification and local release records.
- Added serialized durable jobs, cooperative cancellation/retry, interruption recovery, atomic metadata/result publication and deletion tombstones.
- Added guided React UI, local rules-based guidance and optional consent-controlled read-only OpenAI adapter. Live model mode is unverified (no key configured).
- Real graph correctness/security/recovery suite: 39 passed. Two Edge browser journeys pass, including unfamiliar semicolon CSVs, an added export, stale-result blocking, comparison, two repairs, independent package reopening, refresh, 390px layout, unauthorised request, invalid input, multiple-candidate analytical controls, explicit incomplete scope, failed repair and deletion.
- Five-file benchmark: 5,000 imported records; audit 2.563s, import/audit/evaluation 5.425s, peak traced Python allocations 12,855,974 bytes. Detailed envelope and fictional candidate-pair evaluation in `docs/benchmark.json`.
- Backup/restore smoke: passed after real graph SAVE/restart, fresh metadata/vault restore, login/evidence/ZIP digest checks and cleanup.
- Production TypeScript/Vite build passed. Frontend dependency audit: zero vulnerabilities after Vite/esbuild updates.
- Final Docker production image rebuilt; app and FalkorDB are healthy on localhost 8027/6397. The first-run owner flow is intentionally untouched for the operator.
- Linux CI's first run exposed a missing CI virtualenv in the browser-server command. The workflow now creates the same `.venv` layout used by local instructions. Replacement run 39024513413 passed backend tests, production build and the real Chromium browser journey.

## Exact scope notes
- The standard arbitrary single-candidate import-to-reviewed-export workflow is implemented and verified without an LLM key.
- Advanced knowledge-bundle controls are available; normal paths remain separate. Subject/time/cohort statements are operator assumptions, not automatic factual validation.
- Added rare-combination suppression and per-candidate analytical controls. Arbitrary selected-cell policies, exhaustive optimization, broad fault injection, full accessibility/security audits and public TLS deployment remain outside the verified v1. See `docs/LIMITATIONS.md`.
- Final numeric-key review replaced precision-dependent Decimal normalisation with an exact coefficient/exponent encoding, added explicit numeric range review and exact high-precision bucket arithmetic. Regression verified with distinct 40-digit values.
