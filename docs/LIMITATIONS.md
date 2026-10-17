# Supported boundaries and remaining hardening

The authenticated CSV → scenario → real-FalkorDB audit → repair → inspected ZIP workflow is implemented and tested with arbitrary compatible layouts. This repository is an early single-owner v1, not a security certification or a complete production assurance exercise.

## Deliberate v1 boundaries

- CSV only; conservative fixed limits are enforced. No fuzzy/probabilistic entity resolution, external identity searches, arbitrary URL fetching, spreadsheet formulas, natural-language executable SQL/Python, geocoding or formal privacy guarantees.
- Exact/composite and reviewed number/date interval predicates only. Ambiguous dates need an explicit supported format. Timestamps can join as exact text; timezone/date interval conversion is unsupported.
- A file version is the cohort boundary. Time/cohort descriptions are reviewed assumptions; there are no automatic row-level date-window/cohort filters or factual validation that an operator's subject/context assertion is true.
- Unknown/missing identity keys produce reference-record counts. Names alone cannot establish a person anchor. Supplied reference completeness is not independently known.
- Advanced scenario controls support explicit confirmed knowledge bundles and contradiction detection. The operator must substantiate the same-subject/context assumption; the product cannot establish it from equal field values.
- For multiple candidate versions, choose the candidate in the analytical controls to define per-dataset quasi-identifiers, statistics and protected columns. A single optional identity-anchor definition and one explicit knowledge bundle are exposed in the standard form; richer sets can be supplied through the typed API.
- Suppression covers chosen columns and selected fields of rare composite combinations. Arbitrary selected-cell policies and row suppression are not exposed. No random noise mechanism exists.
- Repairs are explicitly selected declarative recipes, capped at ten branches. There is no exhaustive automatic optimizer. Compare exposure, coverage, utility and retention separately; no arbitrary combined privacy score is used.
- The compact investigation view shows actual dataset/rule chains and masked endpoint indices. It is intentionally not an unrestricted graph explorer.
- Referenced immutable source versions and recorded release branches cannot be individually removed through draft deletion. Full workspace deletion removes local review/history together.
- One process/owner/worker; no SSO, organisation role hierarchy, account recovery email, key rotation UI, multi-instance deployment or distributed transactions.

## Verification limits

- A real five-file, 1,000-row-per-file benchmark and dense 50-column parser bound test were run. Workloads near the fan-out/time limits can be partial. No 10,000-row claim is made.
- The automated browser journey uses unfamiliar semicolon CSVs and covers parsing, meanings, analytical goals, actual audits, adding an available export, stale-result blocking, release-addition comparison, competing repairs, independent ZIP reopening, refresh, narrower layout, unauthorised access and deletion. Additional API tests cover historical exposure, explicit bundles, outage, cancellation/retry and restart handling.
- Restore verification backs up metadata/vault, restarts the real graph container and restores into a new application directory with the same key. It validates login, records, scope, audit, graph evidence and ZIP digest. It is not a disaster-recovery drill on another physical machine.
- The OpenAI adapter is tested with a controlled mock provider. **Live external-model execution was not tested; no server credential was present.** Core workflows were tested without it.
- This is not a penetration test. TLS/reverse-proxy operation, hostile shared-host operators, malware, forensic erasure, recipient copies and operator backup access are outside the tested trust boundary.

## Recommended next hardening

1. Add reviewed database migrations, explicit key rotation/recovery administration and fault-injection tests at every publication checkpoint.
2. Extend the guided UI for richer anchor/bundle sets and arbitrary selected-cell policies.
3. Add more independent generated-property fixtures, long-running quota/soak tests, accessibility tooling and broader browser coverage.
4. Independently review graph candidate-set semantics, threat model, session/storage boundaries and deployment configuration before real sensitive-data use.
5. With authorised credentials, run and record a live model tool-call smoke test, verify dynamic request history and confirm provider-specific retention settings.

No public service, real personal dataset upload, paid infrastructure or hackathon submission was performed.
