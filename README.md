# MosaicGuard

Private, self-hosted dataset release review. Import your own CSVs, confirm what columns mean, investigate scoped linkage exposure with **real FalkorDB**, test immutable repair branches, and download a reproducible release package.

This product reports evidence under a supplied-data and attacker-knowledge model. A single candidate is **not proof of identity**. No matches do not establish anonymity, legal compliance, or a differential-privacy guarantee.

**Live application:** <https://mosaicguard-production.up.railway.app/>

## Start locally

Requires Docker Desktop with Linux containers and Python 3.14 (Python is used only for initial configuration if using Docker).

```powershell
git clone https://github.com/harshitdeora/mosaicguard.git
cd mosaicguard
python scripts/configure.py
docker compose up --build -d
```

Open **http://127.0.0.1:8027** and create your owner account. Back up `.env` securely outside Git **before importing data**. Configuration never overwrites an existing key. The app binds to localhost; the graph uses password-protected localhost port 6397. These commands create only local services.

To stop: `docker compose stop`. To resume: `docker compose up -d`. Avoid `docker compose down -v`, which removes the durable data volumes.

## Supported workflow

1. Create a private workspace; upload CSVs or explore two small, locally generated fictional CSVs.
2. Correct delimiter, encoding, quoting and null settings; review types, meanings, dataset role and row unit. Originals remain immutable.
3. Define an audience, purpose, candidate versions, available references, confirmed exact/composite or typed-compatible rules, diagnostics and analytical requirements.
4. Profile fan-out and run a durable audit. Inspect separate paths, masked local evidence, class sizes, assumptions and missing coverage.
5. Test up to ten repair recipes: remove columns, suppress values, or generalise reviewed numeric/date fields. Each branch receives a new version, graph projection, full re-audit and utility comparison.
6. Review residual findings and analytical conflicts; create a digest-bound ZIP. Reversible spreadsheet transport escaping receives no privacy credit.
7. Record sharing separately with **Record as released**. Historical versions remain available to that audience in later scenarios.

**Conservative limits:** 2 MB/file, 1,000 logical data records/file, 50 columns, 8,192 characters/cell, 5,000 imported records/workspace, 3 joins/path, 100 paths, 20,000 endpoint results/path, 250,000 typed comparisons/rule. Bounds produce partial coverage, never artificial uniqueness. See [measured benchmark](docs/benchmark.json).

## FalkorDB graph data model

FalkorDB is the authoritative linkage graph. Every audit receives its own opaque workspace and audit namespace. Plaintext names and source values are not stored in the graph; matching values and identity anchors are represented by scoped HMAC tokens.

```text
(DatasetVersion)
       |
       | HAS_RECORD
       v
    (Record) --OUT_KEY--> (JoinKey) <--IN_KEY-- (Record)

    (Finding) --EVIDENCE_RULE--> (JoinRule)
```

| Node | Important properties | Purpose |
| --- | --- | --- |
| `DatasetVersion` | `wid`, `sid`, `did` | Identifies one immutable dataset version inside an audit. |
| `Record` | `wid`, `sid`, `did`, `idx`, `entity` | Represents one logical CSV record. `entity` is an opaque scoped token. |
| `JoinKey` | `wid`, `sid`, `rule`, `token` | Represents one complete exact or composite matching key for a confirmed rule. |
| `Finding` | `wid`, `sid`, `fid`, `summary` | Stores the bounded explanation for a completed graph finding. |
| `JoinRule` | `wid`, `sid`, `rid` | Identifies the confirmed rule supporting a finding. |

| Relationship | Meaning |
| --- | --- |
| `DatasetVersion-[:HAS_RECORD]->Record` | Dataset membership and provenance. It is not used as an attacker traversal edge. |
| `Record-[:OUT_KEY]->JoinKey` | A source record supplies the confirmed rule key. |
| `Record-[:IN_KEY]->JoinKey` | A destination record supplies the matching rule key. |
| `Finding-[:EVIDENCE_RULE]->JoinRule` | Connects an explanation to the rule chain that produced it. |

A composite rule creates one atomic `JoinKey` token from all selected components, so every component must match. Join keys are scoped by workspace, audit and rule to prevent unrelated scenarios from connecting through the same value.

## Cypher queries and graph algorithms

All Cypher is parameterised. User text never becomes executable Cypher. [`backend/app/graph.py`](backend/app/graph.py) builds only fixed, whitelisted traversal patterns containing at most three confirmed joins.

| Query | Role |
| --- | --- |
| [`records.cypher`](queries/records.cypher) | Creates the `DatasetVersion`, `Record` nodes and `HAS_RECORD` provenance edges. |
| [`bind_out.cypher`](queries/bind_out.cypher) | Connects source records to scoped `JoinKey` nodes with `OUT_KEY`. |
| [`bind_in.cypher`](queries/bind_in.cypher) | Connects matching destination records to the same keys with `IN_KEY`. |
| [`candidates.cypher`](queries/candidates.cypher) | Traverses an approved rule chain and returns distinct endpoint candidates for every source record. |
| [`finding.cypher`](queries/finding.cypher) | Stores a finding and its supporting `EVIDENCE_RULE` relationships. |
| [`evidence.cypher`](queries/evidence.cypher) | Retrieves the stored summary for one exact audit finding. |

The core candidate traversal has this shape:

```cypher
MATCH (s:Record {wid:$wid, sid:$sid, did:$source})
      -[:OUT_KEY]->(k0:JoinKey {wid:$wid, sid:$sid, rule:$r0})
      <-[:IN_KEY]-(t0:Record {wid:$wid, sid:$sid, did:$d0})
RETURN DISTINCT s.idx, t0.entity, t0.idx
LIMIT 20001
```

For longer approved paths, the same fixed `OUT_KEY → JoinKey ← IN_KEY` pattern is repeated. Dataset, workspace, audit and rule identifiers remain query parameters.

The product depends on these deterministic graph algorithms:

1. **Rule-chain enumeration:** confirmed directed mappings are searched without cycles, to a maximum depth of three joins and 100 paths.
2. **Exact and composite matching:** complete keys are HMAC-tokenised into atomic `JoinKey` nodes. Composite components are conjunctive, not separate optional matches.
3. **Typed-compatible matching:** exact components first block possible pairs; reviewed numeric or date intervals are then compared in bounded application memory. Accepted pairs receive scoped graph keys. Exhausting the comparison budget produces partial coverage.
4. **Candidate-set aggregation:** the candidate query returns distinct endpoint entity tokens. Duplicate intermediate routes are unioned within one path before candidate counts are calculated.
5. **Path-specific evidence:** independent paths remain separate findings. They are intersected only when the operator explicitly confirms a same-subject knowledge bundle.
6. **Coverage-safe limits:** missing components, blocked rules, query timeouts and result limits create unassessed or partial results. They never create an artificial uniqueness claim.
7. **Repair re-audit:** every repair creates a new immutable candidate version, rebuilds its graph projection and reruns every eligible path before risk and analytical utility are compared.

See [Architecture](docs/ARCHITECTURE.md) for candidate-set semantics, typed intervals, historical exposure and evidence boundaries.

## Development and checks

Python 3.14 and Node 22.19+; Docker provides the real graph. Commands below work in Windows PowerShell from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock
python scripts/configure.py
docker compose up -d graph
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8027 --no-access-log --log-level critical
```

The Python server serves the production UI. For frontend hot reload, use `npm.cmd --prefix frontend run dev` in another terminal (port 5178, same-origin API proxy).

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend run test:browser
.\.venv\Scripts\python.exe scripts/benchmark.py
.\.venv\Scripts\python.exe scripts/restore_smoke.py
```

Browser tests use Edge on Windows. On Linux, run `npx playwright install --with-deps chromium` inside `frontend` first. Tests use isolated directories under ignored `work/`, generated synthetic accounts and their own app port 8028. The restore smoke test restarts **this project's graph service**; run it when no other MosaicGuard jobs are active. No live model call is made by these tests.

## Documentation

- [Five-minute beginner walkthrough and sample data](docs/BEGINNER_TUTORIAL.md)
- [Detailed first-use, CSV preparation and advanced synthetic demo](docs/USER_GUIDE.md)
- [Architecture, graph and candidate-set semantics](docs/ARCHITECTURE.md)
- [Keys, deployment, deletion, backup and restore](docs/OPERATIONS.md)
- [Verification and measured limits](docs/VERIFICATION.md)
- [Exact limitations and remaining hardening](docs/LIMITATIONS.md)
- [Build progress and evidence](PROGRESS.md)

No external model credential is required. The local assistant is labelled rules-based. An optional OpenAI tool-calling adapter requires a server key, a reviewed payload policy and explicit workspace enablement. Its live execution remains unverified unless separately recorded in verification evidence.

## Internet deployment

The supported public-hosting path is a single-owner Railway deployment with separate app and FalkorDB services and a persistent volume for each. See the [Railway deployment guide](docs/RAILWAY_DEPLOYMENT.md). The setup token prevents another visitor from claiming a fresh public instance. The current product is not a multi-tenant service.
