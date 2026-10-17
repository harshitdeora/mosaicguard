# Verification evidence

Performed on 2026-10-17 on Windows, Python 3.14.0, Node 22.19.0, Docker Desktop Linux engine 29.2.1, and the digest-pinned real FalkorDB image in `compose.yaml`. No external model key was configured. No personal datasets were used.

## Automated correctness and boundary tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q --junitxml=docs/junit.xml
```

**39 passed** in the final recorded run. [JUnit evidence](junit.xml).

Coverage includes logical multiline records, BOM and alternate encodings, semicolon/tab imports, leading-zero IDs, ambiguous dates, literal `NA`, explicit nulls and ragged-row exclusions, duplicate/blank headers, malformed quoting, empty/header-only/binary/oversized input, dense 50-column/1,000-record parsing, reviewed Unicode/case rules, exact composite conjunction and missing components.

A regression test verifies that numbers longer than Decimal's default 28-digit context never round into the same exact key, and that their numeric bucket boundaries remain exact within the documented range.

Real graph tests compare candidate sets to an independent relational/set oracle, union one-to-many intermediate possibilities, deduplicate confirmed entity anchors, keep independent paths separate, explicitly intersect knowledge bundles and report contradictions. They test partial fan-out refusal to claim uniqueness, typed date/numeric interval boundaries, negative buckets, no ordering of HMAC tokens, and whitespace-only composite components.

Workflow tests cover residual alternative paths after repair, quarter-compatible candidates remaining plausible, protected-column refusal, unavailable analytical metrics, stale export refusal, release-addition impact, retained historical exposure, semantic ZIP verification, formula transport escaping, masked/default versus deliberate reveal, canary absence from graph/model payloads/encrypted files, foreign workspace/job IDs, unauthenticated access, CSRF/origin rejection, workspace deletion, failed/cancelled imports, retry/idempotency, interrupted-worker recovery, wrong/missing keys, single-writer lease and database-outage blocking.

The external-model adapter is tested with a controlled provider mock, including actual typed tool dispatch. That is **not a live model call**.

## Actual browser journey

```powershell
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run test:browser
```

**Two journeys passed** in headless Microsoft Edge on Windows: the expanded end-to-end review and a separate invalid-input/multiple-candidate/incomplete-scope/failed-repair journey. [Machine-readable browser results](browser-results.json).

The browser signs in to an isolated synthetic test installation, creates a workspace, uploads an unfamiliar semicolon layout, corrects parsing, reviews date/numeric types, assigns roles/units, confirms mappings, profiles fan-out, defines a protected column and a numeric mean requirement, runs and expands actual graph findings. It then imports an additional available export, observes the stale prior scope, revises the scenario while preserving confirmed rules, runs again and compares release-addition findings. It tests an unsuitable repair and a useful typed repair, creates a package, downloads and independently reopens it with `scripts/verify_package.py`, refreshes, checks a 390px layout for document overflow, verifies unauthorised access refusal, and deletes the workspace. No browser page errors were recorded.

Synthetic screenshots were visually inspected: [desktop evidence](screenshots/audit-desktop.png), [repair comparison](screenshots/repairs-desktop.png), [narrow overview](screenshots/overview-mobile.png). Keyboard-operable controls, explicit labels, focus outlines, local table overflow handling and reduced-motion CSS are implemented. This is not a comprehensive accessibility certification.

The second browser journey confirms that quasi-identifier selections, protected columns and mean-by-group goals remain tied to each of two candidate versions. It checks rejected duplicate headers, an explicitly partial audit with no eligible linkage rules, and a failed incompatible repair without a fabricated result. Rare-combination suppression also has an independent focused correctness test.

## Measured envelope

```powershell
.\.venv\Scripts\python.exe scripts/benchmark.py
```

The final [benchmark JSON](benchmark.json) reports **five real imported files of 1,000 records each**, six confirmed rules and a maximum depth of three. The audit took **2.563 seconds**, and import plus audit/evaluation took **5.425 seconds**. Peak traced Python allocations were **12,855,974 bytes**; this is not total process RSS and excludes native allocations/FalkorDB. A separate graph-container snapshot was about 77 MiB, not a measured peak.

The benchmark reports complete coverage within its configured bounds. Fictional generator truth gives candidate-pair recall 1.0 for the three evaluated routes; precision differs by ambiguity (attendance 0.2, badge 1.0, repeated calendar dates about 0.294). These are synthetic fixture measurements, not evidence of real-world re-identification accuracy.

Limits above this envelope, such as 10,000 records per file, are not advertised. Near-bound fan-out and unsupported conversions remain partial rather than protected.

## Restore and installation

`scripts/restore_smoke.py` performed an offline SQLite/vault backup, restored into a new directory, executed a real graph SAVE, restarted this project's graph container and retrieved persisted evidence. It verified owner login, workspace/datasets, scenario/audit, authenticated package digest, Cypher evidence and deletion. [Restore evidence](restore-results.json).

The production React build passes TypeScript compilation. The Docker multi-stage build was executed successfully with locked dependencies. The final image and Compose health/startup checks are recorded in `PROGRESS.md` after the last build. `npm audit` reports zero vulnerabilities after updating Vite and resolving its esbuild transitive dependency. This dependency result is not a penetration test.

## Remaining unverified or deferred work

Live model execution, public TLS/reverse-proxy deployment, cross-machine disaster recovery, a full fault-injection campaign, exhaustive browser/accessibility coverage and independent security/scientific review remain unverified. Arbitrary selected-cell policies and richer anchor/bundle sets remain outside the standard form; see [exact limitations](LIMITATIONS.md). These are not represented as completed capabilities.
