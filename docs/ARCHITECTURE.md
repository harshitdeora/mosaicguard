# Architecture and analytical semantics

React + TypeScript + Vite renders the guided review UI. FastAPI handles authenticated, same-origin endpoints. One worker consumes durable SQLite jobs. An OS-backed lease prevents multiple application processes sharing a metadata/vault directory.

SQLite stores the owner password hash, hashed session tokens, CSRF tokens, rate-limit attempts, durable job state and an encrypted object catalog. Object bodies and job payloads use Fernet. Source bytes, parsed versions, branch versions and ZIP packages are separately encrypted in a private vault. The master key is externally supplied; a key-check stops startup with a missing/wrong key.

FalkorDB is the authoritative record-linkage graph. Each audit has its own opaque workspace/audit namespace. A dataset has Record members; each Record carries only scoped opaque IDs, a logical index and a keyed entity token. Exact/composite matches use atomic JoinKey hubs scoped to one confirmed rule, connected by OUT_KEY and IN_KEY. Findings have EVIDENCE_RULE relationships to JoinRule nodes. Membership and provenance relationships are never attacker traversal relationships.

`queries/` contains parameterised Cypher templates. `graph.py` generates only fixed whitelisted patterns of at most three approved OUT_KEY/IN_KEY steps. Dataset IDs, rule IDs, workspace IDs and audit IDs enter as parameters. No user-supplied Cypher executes. Python may enumerate **schema-level rule chains**, build temporary key bindings and aggregate bounded query results; it does not store or traverse an alternative authoritative record graph.

## Candidate sets

For a source record and one permitted ordered rule chain, the graph query returns every distinct endpoint entity reachable through **any** valid intermediate-record combination. Intermediate alternatives are unioned. Duplicate reference records with a confirmed stable entity key count once; without that defensible key (or if a key is missing), wording is **reference records**. Names alone are rejected as anchors.

Separate chains remain separate findings. They are never intersected automatically. The advanced scenario controls support explicitly confirmed same-subject/context knowledge bundles with paths ending at the same reference version; the engine reports contradictory disjoint paths. Independent paths remain the default.

Every composite component must match. Null, empty and reviewed whitespace-only values cannot be keys. Missing any required component leaves the source record unassessed for that rule. Leading-zero text IDs retain their exact spelling. Optional trim, NFC and case folding are visible rule settings. Numeric exact matching uses Decimal canonicalisation; dates require a reviewed explicit format.

## Typed generalisation

Numeric buckets are half-open `[lower, upper)` intervals, including correct floor division for negative values. Months, quarters and years have explicit Gregorian start/end boundaries. Exact points match an interval when contained; two intervals match when they overlap. A quarter-valued candidate therefore remains compatible with all reference dates inside that quarter.

Exact composite components first provide a blocking key. Every resulting typed candidate pair then passes all declared compatibility checks in authorised processing memory. Supported pairs receive scoped HMAC keys in FalkorDB; ordered comparisons are never performed on HMAC strings. A comparison/pair budget exhaustion makes the rule partial. An exact rule used with a generalised field is labelled unsupported/partial rather than compared as unequal literal text. Column removal deliberately blocks its predicate and reduces assessed coverage; it is not reported as zero risk.

## Findings and measurements

- Direct identifiers: columns explicitly marked by the owner, plus review-only import suggestions.
- Within-file classes: record frequencies for selected quasi-identifier combinations; missing components are unassessed. Marked sensitive columns get single-distinct-value class diagnostics.
- Linkage: path-specific endpoint counts, single candidates, small candidate sets, no matches and partial coverage.
- Release addition: new/changed chains are compared only when candidate, audience, utility, bounds and original rules match and availability is a superset.
- Historical exposure: recorded releases and their previously reviewed references/rules remain in the audience model. Historical-source single-candidate path records are counted separately from the current candidate.

Severity is deterministic: partial traversal → incomplete; one candidate → high review priority; positive count below the configured threshold → review; other outcomes → scope. This is an investigation triage rule, not calibrated risk.

The top single-candidate count sums **source record/path pairs**. A record can appear on multiple chains. Its denominator is separately reported. It is neither a distinct-person total nor a probability.

## Repairs and consistency

Each reviewed recipe creates derived versions with private lineage, a new scenario and a separate graph projection. Originals and reference datasets are unchanged. The full eligible search runs again, including alternative and historical paths. Failed work cannot replace a completed result. Staging versions are hidden until publication; interrupted jobs require review/retry. Workspace mutations are serialized against active work; one worker limits concurrency. There is no distributed transaction: stage/checkpoint/publish plus restart reconciliation implements the application boundary.

Utility is independent of exposure: category counts, exact numeric means/medians and supported time counts use the same structured definitions before and after repair. Missing groups/columns or generalised exact numeric outputs are unavailable/violated. Relative error at a zero baseline is undefined; equality is treated explicitly. Row suppression is excluded in v1, so retained and original cohorts coincide. Retention, missingness and generalised-column counts remain visible.

ZIP exports are bound to the scenario revision and SHA-256 digests of the exact audited version artifacts. Files are reopened and reversible spreadsheet escaping is removed according to a position manifest before checking semantic equality. Stale revisions or changed content digests block a new export. Historical packages retain their historical scope.

## Background and references

[NIST SP 800-188](https://csrc.nist.gov/pubs/sp/800/188/final) informs the linkage/composition and utility framing; no endorsement is implied. Implemented APIs were checked against the [official Python client](https://github.com/FalkorDB/falkordb-py), [FalkorDB persistence guidance](https://docs.falkordb.com/operations/durability/persistence), [Fernet documentation](https://cryptography.io/en/stable/fernet/), [OWASP upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [CSV injection guidance](https://community.owasp.org/attacks/CSV_Injection), and [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
