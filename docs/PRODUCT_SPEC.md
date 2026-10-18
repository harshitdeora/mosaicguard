# MosaicGuard — full product build prompt for Codex

Build MosaicGuard in the current project. This is a request to implement, run, test, and deliver a usable product with real user workflows. A design document, a static interface, or functionality restricted to bundled example files does not satisfy this request.

Make reasonable decisions, preserve existing user work, and continue through the mandatory product scope. Ask questions only when the answer is required to make progress. Record assumptions and limitations. Do not claim that incomplete or unverified capabilities are finished.

## 1. Product outcome and intended users

MosaicGuard helps an authorised data owner investigate what a planned dataset release could reveal when combined with other information available to its intended audience. It explains detected linkage paths, proposes changes, tests those changes, and exports an inspected release candidate with a reproducible report.

Primary users are a researcher, analyst, or operations lead preparing survey, programme, training, or community datasets for sharing.

Primary workflow:

Create a private workspace -> import CSVs -> define the release scenario -> review column meanings and linkage rules -> select analytical requirements -> run an audit -> inspect evidence -> compare repairs -> review and download a release package -> assess the next release against the existing release history.

Example use case: a research team wants to share training feedback while retaining useful department-level statistics. An attendance export contains overlapping attributes that could connect a response to a person in an available reference dataset. MosaicGuard identifies the candidate chain and evaluates ways to reduce that tested exposure while measuring damage to the requested statistics.

Build a private, self-hosted, single-organisation v1 with authenticated access. Support arbitrary compatible user CSVs within documented limits. Bundled synthetic examples provide onboarding and verification; they are not the only supported inputs.

The interface should feel like a guided data-review product. The main result is an understandable release decision with evidence and trade-offs. A graph is a supporting investigation view.

## 2. Scientific and product boundaries

Treat findings as scoped evidence under an explicit release and attacker-knowledge model.

NIST SP 800-188 discusses linkage, composition of releases, and balancing disclosure risk with analytical usefulness. Use it as background, not as an endorsement of this product:
https://csrc.nist.gov/pubs/sp/800/188/final

Product language must distinguish:

- A small within-file equivalence class.
- A possible match to a reference record.
- A unique candidate under a confirmed linkage model.
- An identity known only in a synthetic evaluation fixture.
- An incomplete or unsupported analysis.

A single candidate is not proof that the person has been correctly identified. A reference dataset may be incomplete. A name may not be unique. A reciprocal candidate count is not a calibrated re-identification probability.

Use labels such as "Detected linkage exposure", "One candidate under these assumptions", "Ambiguous linkage", "No match found", and "Analysis incomplete".

Never present the result as guaranteed anonymity, regulatory certification, a universal privacy score, or a differential-privacy guarantee. If no findings are detected, display the analysis coverage and say that no findings were detected within that scope.

A user-configured candidate threshold, initially 5, is a review preference. It does not establish a universally safe release.

The product audits supplied, authorised information. External identity searches, scraping, enrichment, arbitrary URL fetching, and searching for real individuals are outside the product scope.

## 3. Delivery strategy and mandatory scope

First inspect the repository, applicable instructions, runtimes, Docker, and available testing tools. Preserve existing files. Write a concise implementation plan and maintain one progress/evidence file.

Mandatory usable-v1 scope:

1. Authenticated private workspaces with persistent state.
2. Real CSV upload, import review, profiling, and versioning.
3. Explicit release scenarios and user-confirmed semantic mappings.
4. FalkorDB-based linkage investigation with evidence.
5. Within-file uniqueness diagnostics.
6. Correct, bounded multi-file candidate analysis.
7. Repair proposals, independent re-audits, and useful utility comparisons.
8. Immutable originals and reproducible release packages.
9. Background jobs, cancellation, restart recovery, and deletion.
10. A guided, polished interface, useful errors, and documentation.
11. Automated correctness, isolation, security-boundary, and browser checks.
12. A bounded tool-calling assistant when configured, while core workflows function without a model key.

Implement complete workflows before optional features. Do not silently substitute hard-coded results or a sample-only application. If work remains, identify it honestly.

Defer enterprise SSO, billing, public SaaS tenancy, spreadsheets other than CSV, natural-language SQL, probabilistic entity resolution, arbitrary fuzzy matching, web scraping, geocoding, and formal privacy guarantees.

## 4. Architecture and installation

Preferred architecture:

- Frontend: React, TypeScript, Vite, accessible UI components, and restrained styling.
- Backend: Python, FastAPI, Pydantic, a tested CSV/dataframe stack, and the official FalkorDB client.
- FalkorDB: authoritative linkage graph, approved relationships, scenario projections, findings, evidence paths, and audit provenance.
- A small metadata store, preferably SQLite for a single-instance installation: accounts, sessions, durable jobs, and artifact manifests. It must not replace FalkorDB for graph analysis.
- Private encrypted file storage: original CSVs, derived CSVs, detailed reports, and optional confidential mapping configuration.
- One application instance and a bounded worker, with explicit single-writer coordination where needed.
- Docker Compose for a reproducible local installation.

Adapt to an existing repository if there is a concrete reason. Record supported versions and lock dependencies.

Provide:

- One-command application startup after documented first-run configuration.
- A one-time owner-account setup flow or CLI.
- A documented encryption-key setup procedure; no committed keys.
- .env.example, health checks, durable volumes, and Windows PowerShell-compatible development instructions.
- Server-only secrets and no model key in the frontend bundle.
- A stable same-origin deployment path or tightly scoped development CORS configuration.
- Localhost binding by default. Internet hosting is a separate deployment configuration requiring authentication and TLS.

If FalkorDB is unavailable, show an actionable degraded state and block audits and graph mutations. Do not present a fallback implementation as successful FalkorDB integration.

## 5. Data custody, access, and deletion

Raw data must remain in the operator's deployment by default. No telemetry, third-party analytics, remote error payloads containing user content, or automatic external model calls.

Implement:

- Owner authentication with a maintained password-hashing library and protected sessions.
- Authorization on every workspace, dataset, audit, job, preview, export, and evidence endpoint.
- HttpOnly session cookies, appropriate SameSite settings, CSRF protection for cookie-authenticated mutations, and secure cookies in TLS deployments.
- Login throttling and bounded expensive operations.
- No public file paths or unauthenticated artifact downloads.
- Correct logout and session expiry.
- Masked previews and evidence by default; deliberate authenticated reveal of selected local values.
- Logs containing opaque IDs and operational diagnostics instead of row values, names, filenames containing personal data, or credentials.
- Useful errors that do not reflect uploaded cell values or stack traces.
- Uploaded cells and headers rendered as escaped text in tables and reports, including HTML-like content and instruction-like text. Never execute uploaded expressions or render them as trusted markup.

Encrypt raw artifacts at rest with a maintained cryptographic library and a documented key scheme. A master key must be supplied securely and persisted outside the application image. Do not invent cryptography or regenerate a missing key over existing data.

Graph matching should use workspace-scoped keyed tokens for canonical values, with rule/concept namespaces and unambiguous type/length encoding. Use a keyed construction such as HMAC, not an unsalted hash of low-entropy attributes.

Tokens and graph topology remain sensitive. Explain this operationally in administrator documentation. Do not describe tokenisation as anonymisation.

HMAC tokens do not support ordered numeric or date comparisons. For generalised joins, derive compatible scoped bucket keys from values in authorised processing memory, or perform a bounded typed comparison before storing supported candidate links in FalkorDB. Do not compare token strings as if their order represented dates. Any coarse blocking index must be followed by the declared compatibility check; index collisions alone are not evidence.

Keep cleartext values in encrypted artifacts and short-lived processing memory. Retrieve authorised evidence examples from the vault when needed. Do not persist raw identity values in logs, LLM traces, or graph labels.

Support deletion of:

- A draft dataset version.
- An audit and its stored examples.
- A repair branch and generated artifacts.
- An entire workspace.

Deletion must cover graph data, file artifacts, caches, job payloads, and accessible results. Remove shared token nodes only when they are orphaned within the correct workspace. Cancel related jobs and prevent downloads from a deleting workspace.

Document what deletion does about backups, retention, exported copies, and filesystem remnants. Do not promise forensic erasure.

## 6. Real CSV import and edge cases

Accept user-uploaded CSV files. Do not require a particular filename, fixed headers, or a synthetic dataset layout.

Use a guided import review:

1. File validation and bounded preview.
2. Encoding, delimiter, quote, header, and null-token choices.
3. Column-type suggestions and user overrides.
4. Dataset role and row-unit selection.
5. Stable column IDs and import confirmation.
6. Background ingestion and a completion summary.

Start with practical configurable limits, for example 10 MB and 10,000 rows per file, 50 columns, and 25,000 rows per workspace. Enforce byte limits while streaming. Validate actual performance and publish the measured envelope; reduce stated limits if necessary.

Handle or explicitly reject with a useful error:

- UTF-8, BOM, and a user-selected supported alternate encoding.
- Commas, semicolons, tabs, quoted delimiters, embedded newlines, escaped quotes, and CRLF.
- Empty files, headers-only files, duplicate or blank headers, ragged rows, and malformed quoting.
- Duplicate filenames and identical file contents.
- Leading-zero IDs, long identifiers, large integers, mixed numeric/string columns, and negative numeric values.
- Ambiguous dates, invalid dates, timezone-bearing timestamps, and date-only fields.
- Missing values, empty strings, configured null markers, and a literal string such as "NA" that may be meaningful.
- Unicode normalization, accented characters, and case distinctions.
- Very long cells, binary content, unsupported archives, path traversal filenames, and resource exhaustion.

Preserve imported source values. Do not silently coerce identifiers into numbers, infer an ambiguous date format, remove accents, or apply lossy normalization.

Show parsing warnings with row numbers and counts. Redact cell contents in error logs. Skipping malformed rows requires an explicit import choice, and the exclusion count must carry through audit coverage and exports.

Store immutable source bytes with content digests and a parse configuration. Reference records by dataset-version ID and logical record index; physical line number is insufficient for multiline CSVs.

Store uploads outside the webroot under generated paths. Do not trust MIME type or extension alone. Follow the applicable parts of:
https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

Preview samples may help review an import, but an audit must scan all in-limit records or clearly report partial coverage.

## 7. Release scenarios and attacker knowledge

Every audit must use an immutable scenario manifest containing:

- Candidate dataset version or versions intended for sharing.
- Intended audience and purpose.
- Reference and previously released versions assumed available to that audience.
- Internal-only data, explicitly excluded from linkage analysis.
- Confirmed identity-anchor definition, if any.
- The row unit for each dataset: person, household, organisation, event, or unknown.
- Applicable time/cohort conditions.
- Approved linkage rules and normalization configurations.
- Search bounds and thresholds.
- Utility requirements and protected columns.

A dataset role is explicit. Do not assume every imported dataset is publicly available or automatically eligible as a reference.

Versions that are alternative drafts are mutually exclusive unless the user includes both. Previously released versions remain available in the release model when a new candidate replaces them.

Downloading a file creates an artifact; it does not prove that the user published it. Provide an explicit "Record as released" action with audience and date metadata. This records history and does not publish externally.

Removing an already released file from the local workspace cannot establish that an audience no longer has it. Retain a minimal release-history record and mark analyses with missing historical context as incomplete. Report historical exposure separately from what a future repair can change.

Allow "before adding this export" and "after adding this export" comparisons using versioned scenario manifests.

## 8. Semantic mappings and join rules

Offer mapping suggestions from types, declared meanings, and local profiling. Require user confirmation before a suggested mapping influences findings.

Each rule records:

- Source and destination dataset-version/column IDs.
- Intended meaning and subject unit.
- Exact, composite-exact, or supported typed-generalisation predicate.
- Normalization configuration.
- Direction and applicable time/cohort constraints.
- Human confirmation and revision.
- Any cardinality assumptions.

Identical column names or equal strings do not establish semantic equivalence. Event IDs, household IDs, and person IDs must not be treated as interchangeable identities.

Support exact joins and composite exact joins with conjunctive semantics. A match on one field must not satisfy a rule requiring all three fields.

Normalization choices are visible and versioned. Start conservatively with reviewed trimming, Unicode normalization, type-aware parsing, and optional case folding.

Null, blank, suppressed, and unknown values do not match each other as identifiers. Missing one component of a required composite key makes that rule unassessed for that row.

Detect and explain low-selectivity joins and many-to-many fan-out before running an expensive audit. Let users profile candidate counts and inspect masked examples.

A matching reference row is an identity anchor only when the user supplies a defensible entity-key definition. If identity deduplication is unresolved, report "reference records", not a count of distinct people. Names alone are insufficient.

V1 should not silently perform fuzzy matches. Unsupported mappings must remain visible as unsupported.

## 9. Graph model and bounded linkage engine

Use FalkorDB for the relationships that make the findings possible.

Suggested logical entities:

- Workspace, Dataset, DatasetVersion, Column, and Record.
- ConfirmedConcept, JoinRule, and scoped JoinKey/ValueToken.
- IdentityAnchor when explicitly defined.
- ScenarioSnapshot, AuditRun, Finding, and EvidencePath.
- RepairBranch, Transformation, UtilityMetric, ExportArtifact, and ReleaseRecord.

Relationships should represent dataset membership, approved join bindings, possible record matches, identity-anchor references, finding evidence, transformation lineage, and release inclusion.

Use graph representations that enforce full composite predicates. A shared-value hub must not accidentally turn a conjunctive join into an OR join or allow arbitrary same-dataset hops.

Use real parameterised Cypher for candidate expansion, bounded path investigation, affected-release detection, and evidence retrieval. Keep query templates readable in the repository.

Requirements:

- Every query is workspace and scenario scoped.
- Whitelist traversal relationships used for attacker linkage.
- Never traverse privileged internal row IDs, source lineage, repair ancestry, or synthetic truth mappings as linkage evidence.
- Candidate edges mean possible matches, not proven identity.
- Avoid materialising an unbounded row-to-row Cartesian product. Use indexed scoped join keys and controlled expansion.
- Do not maintain another authoritative linkage graph in Python, SQL, or browser memory.
- Temporary dataframe profiling, bounded query results, and independent test oracles are appropriate.

Default to at most 3 approved dataset-to-dataset joins per path, with a configurable hard ceiling. Bound rule combinations, candidate expansions, graph query time, result size, and total job time.

When a bound is reached, record the affected rows/rules/paths and mark coverage partial. Never convert a timeout or truncated candidate set into a finding of uniqueness.

Path semantics:

- For a source row and one permitted path, collect distinct endpoint candidates reachable through any valid intermediate-row combination.
- Union alternative intermediate matches within that path.
- Count distinct anchors, not the number of paths or duplicate rows.
- Evaluate separate paths separately.
- Intersect candidate sets across multiple evidence paths only in an explicit knowledge bundle whose predicates are confirmed to refer to the same subject, cohort, and time.
- Do not automatically intersect alternative explanations or conflicting contexts to manufacture a smaller candidate set.
- Surface contradictory path results and inconsistent mappings.

Define and unit-test the candidate-set semantics before building UI counts around them. Use an independent small relational/set-based implementation as the correctness oracle for synthetic test fixtures.

## 10. Findings, diagnostics, and honest metrics

Implement at least:

A. Direct-identifier screening:
Surface user-marked identifier columns still included in a candidate, and reviewable suggestions for likely identifiers. Do not automatically classify a free-text field as clean.

B. Within-file uniqueness:
Compute equivalence-class sizes for approved quasi-identifier combinations. Distinguish record counts from person counts.

C. Multi-file linkage:
Report possible, ambiguous, and single-candidate paths to approved reference anchors.

D. Release-addition impact:
Show which findings appeared or changed when a new export or release version became available.

E. Missing-coverage diagnostics:
Show unsupported types, unresolved mappings, excluded rows, missing historical releases, query limits, and incomplete reference coverage.

Where practical, show sensitive-value homogeneity within assessed classes as a diagnostic when the user marks a sensitive column. Do not present class size alone as covering attribute disclosure.

For each finding show:

- The source dataset version and affected record count.
- The exact approved rule chain.
- Candidate cardinality with entity-unit wording.
- Supporting field roles and masked local examples.
- Scenario assumptions and coverage.
- Related release versions.
- The specific transformations that may address it.

Zero candidates means no match was found under that test. It does not mean zero privacy risk. Missing data or unsupported predicates mean unassessed, not protected.

Use deterministic, documented severity rules and raw counts. Avoid an unexplained 0–100 privacy score.

Expose denominators: imported rows, excluded rows, assessed rows, unassessed rows, retained rows, and suppressed rows. A repair must not look better merely because fewer rows were assessed.

If showing a single-candidate rate, name the population and define the calculation. Keep any reciprocal-cardinality statistic separate from probability claims.

## 11. Utility requirements that reflect real use

Before repair, let the user select useful analytical goals with structured, supported controls:

- Counts by selected categories.
- Means or medians of supported numeric fields by group.
- Totals by a selected time granularity.
- Preservation of required columns.
- Minimum retained-row proportion.
- Maximum acceptable drift for selected statistics.

Do not execute arbitrary user-generated SQL or Python.

Compute original and repaired query outputs using the same definitions. Show absolute changes, relative changes where defined, missing groups, row retention, missingness, and generalisation coverage.

Handle zero denominators, empty groups, removed columns, and undefined comparisons explicitly. A metric that cannot be computed after repair must appear unavailable or violated, not zero drift.

Compare both the retained cohort and the original source cohort where suppression changes the population. Explain when an apparent improvement comes from dropping records.

Keep risk and utility as separate dimensions. Show competing valid repair options rather than hiding trade-offs inside one arbitrary score.

## 12. Repair design and correct re-auditing

Originals remain immutable. Each repair creates a versioned branch with a declarative transformation recipe, source digest, rule versions, and audit context.

Mandatory repair families:

1. Typed generalisation:
   Dates to explicit month/quarter/year intervals and numeric values to user-reviewable buckets.

2. Suppression:
   Selected values or rare combinations to explicit missing values, with coverage consequences recorded.

3. Column removal:
   Available only when permitted by the user's utility constraints.

Optional row suppression requires an explicit policy and a clear population-impact report. Do not use arbitrary noise or pretend it offers formal privacy guarantees.

Critical matching rule:

Generalisation must widen the set of plausible matches when appropriate. A quarter-valued candidate must remain compatible with reference dates inside that quarter. Do not compare "2026-Q2" literally against "2026-05-12" and report the disappearance of matches as protection.

Implement compatible typed interval/bucket predicates or a shared explicit generalisation mapping. Both sides' precision and boundary conventions must be defined. Unsupported conversions must block that evaluation or be labelled incomplete.

Suppressed markers must not form a common join key matching every suppressed row.

For every repair:

- Rebuild the relevant graph projection and rerun the full eligible linkage search against the same audience/reference/history model.
- Search for alternative paths that remain after breaking the first path.
- Do not modify an attacker reference dataset to make the candidate appear safer.
- Respect already released source versions that are still assumed available.
- Distinguish a deliberately blocked attack predicate from an unsupported or skipped test.
- Preserve source-row lineage privately for comparison; exclude it from attacker traversal.

Search a bounded, configurable set of transformation recipes. Return a Pareto-style comparison of tested risk, assessment coverage, and utility. Show search limits and protected constraints. If no tested repair satisfies the user's requirements, say so and show the conflict.

The assistant may propose a branch; the user chooses which changes to apply/export. No original-data overwrite or automatic publishing.

## 13. Release package and reproducibility

After the user reviews a chosen branch, build a downloadable package containing:

- Transformed CSV or CSVs.
- Human-readable review report.
- Machine-readable audit summary.
- Transformation recipe.
- Column schema, parse settings, and normalization version.
- Scenario, rule, and audit identifiers.
- File digests and software/version metadata.
- Coverage limits, residual findings, and utility results.

Default reports must exclude original identity values, raw identifying chains, HMAC keys, hidden synthetic truth, and confidential row examples. A private detailed evidence report requires a separate deliberate selection and clear labelling.

Keep application IDs and private lineage maps out of release CSVs unless explicitly intended as output columns and re-audited.

Address spreadsheet formula injection using a documented export policy:
https://community.owasp.org/attacks/CSV_Injection

Preserve the distinction between semantic data and spreadsheet transport escaping. Escaping a formula-like identifier must not count as a privacy repair, because an audience can remove transport escapes. Quote escaping alone is not the full mitigation.

Audit the semantic contents represented by the final exported artifact, including every privacy transformation. Verify digests and compare reopened output with the audited branch. Test that formula protection cannot manufacture an apparent reduction in linkage risk.

Bind each package to the exact scenario/branch revision. A stale audit cannot authorise export of a changed candidate. Downloading a historical package should show its historical scope and any superseding findings.

## 14. Assistant and external-model privacy

Core import, analysis, repair comparison, and export must work without an external model.

Provide a bounded assistant for explaining the workflow, proposing mappings, choosing audits, investigating findings, and comparing repair branches through tools. Include a live tool-calling adapter when credentials are configured.

Suggested tools:

- get_schema_summary
- propose_mapping
- profile_join_rule
- run_audit
- get_sanitised_finding
- propose_repair_recipes
- evaluate_repair_branch
- get_utility_comparison
- explain_release_limitations

Use typed tool schemas, validated IDs, server-side authorization, output limits, retries, timeouts, and a total tool-call budget.

External-model mode is opt-in and off by default. Show the provider, configurable model, and exact outbound payload preview before enabling it for a workspace. Use opaque aliases and tightly scoped aggregates; do not send raw rows, original names, confidential filenames, or arbitrary cell text.

Provide a reviewable payload policy and an initial exact request preview at enablement. Subsequent dynamic tool responses must pass the same deterministic redaction/allowlist checks and be inspectable in a sanitised request history. An optional per-request preview may be offered. Do not imply that an initial preview covered future unrestricted payloads.

Do not assume aggregates are inherently anonymous. Document what is sent and permit users to keep this mode disabled. No hidden data egress in error reporting or embeddings.

The LLM can propose and explain; deterministic code and graph queries establish findings. The LLM cannot execute raw Cypher, change originals, select confidential identity examples, or publish a dataset.

Use current official function-calling documentation if implementing OpenAI:
https://developers.openai.com/api/docs/guides/function-calling

If no credential is configured, label the built-in rules-based assistant accurately. Test the model adapter separately, and record a live tool-call smoke test only when actually performed. Never describe canned text or a stub as a live LLM agent.

## 15. User experience and interface

Build a calm, professional data-review workspace with clear language, helpful defaults, and consistent spacing. Avoid decorative dashboards and forcing users to understand graph terminology.

Primary navigation:

- Workspaces.
- Datasets.
- Release scenarios.
- Audits and findings.
- Repair comparison.
- Release history.
- Settings and data management.

The first-run experience should offer "Use my CSVs" and "Explore a synthetic example". Both use the same backend and analysis engine.

Guide users with a visible progress checklist:

Import -> Describe -> Map -> Audit -> Repair -> Review and export.

Required UI behavior:

- Drag/drop upload plus a keyboard-operable file picker.
- Import preview and correction without losing the upload.
- Plain-language explanations of identifiers, quasi-identifiers, reference data, and candidate matches.
- Reviewable mapping suggestions with reasons.
- Data table filters and pagination.
- Clear distinction between source data, candidate data, and a repaired branch.
- Findings that open a readable explanation before the technical graph.
- A small evidence graph focused on the selected path.
- Side-by-side repair cards showing actual measurements and constraints.
- A release-addition comparison view.
- Job progress stages, cancellation, retry, and interruption recovery.
- State preserved across refresh and restart.
- Empty, invalid-input, database-down, no-findings, incomplete-analysis, and no-feasible-repair states.
- Keyboard accessibility, visible focus, readable contrast, responsive layouts, and reduced motion.

Use statuses that mean something: review required, draft, running, complete within scope, partial, stale, failed, cancelled, or exported. Never show a green "anonymous" or "compliant" badge.

All findings, counts, graphs, and comparisons must come from actual backend results. No fake loading, fabricated progress percentages, or controls that do nothing.

## 16. Jobs, consistency, and failure recovery

Treat imports, audits, and repair evaluations as durable jobs with stable IDs and idempotency keys.

- Queue, run, cancel, retry, and record failure without leaving usable half-ingested versions.
- Use staging graph namespaces/versions, validate completeness, then publish the version atomically at the application boundary.
- Record content/configuration digests and graph revisions.
- Use optimistic concurrency checks and serialize conflicting workspace mutations.
- An audit reads one immutable scenario snapshot.
- A changed mapping, source version, utility constraint, or release assumption creates a new revision and marks affected results stale.
- A failed branch cannot overwrite the last successful result.
- A cancelled job must release resources and remove scoped temporary artifacts.
- Reconcile metadata-store and graph state after restart. Do not assume a cross-database transaction.
- Prefer a small, documented single-worker design to an unnecessary distributed queue.
- Make health status and actionable failures visible.
- Clean up temporary graph projections and expired artifacts within the correct scope.

Support metadata backup and encrypted artifact/graph persistence. Document backup scope, key custody, restore, and retention. Perform one restore verification using synthetic data.

## 17. Performance and coverage controls

Prevent accidental combinatorial explosions.

Use indexes, composite-key blocking, paginated graph inspection, configurable depth/candidate limits, and aggregate counts where possible. Do not build every pairwise edge between rows sharing a common attribute.

Distinguish:

- Complete coverage within stated bounds.
- A sampled preview.
- A partially assessed file or search.
- A failed or cancelled job.

Incomplete candidate enumeration cannot establish a single-candidate result. Missing fields cannot make an assessed record automatically protected.

Benchmark at least a five-file synthetic workspace with around 1,000 rows per file on the available machine. Report data sizes, parameters, peak resource use where measurable, and actual timings.

Test the largest supported size before advertising it. If the environment cannot verify the proposed 10,000-row-per-file limit, state the tested envelope and leave the larger limit experimental or reduce it.

Provide a dry-run fan-out estimate and a useful "narrow this rule" suggestion for low-selectivity joins.

## 18. Synthetic examples and evaluation fixtures

Provide a documented five-file onboarding scenario with roughly 200 fictional people and three linkage patterns. Generate the data locally; do not base it on actual individuals.

Include:

- An ambiguous initial candidate.
- A newly available export that introduces an additional linkage path.
- A repair that broadens plausible matches while preserving selected statistics.
- A repair that fails because another path remains.
- A historical release that preserves exposure despite changing the newest candidate.

Use hidden fixture entity IDs only to evaluate the engine. Keep them out of approved joins, LLM context, exported examples, and product findings.

All example uploads must pass through the same upload/import/mapping/audit interfaces as arbitrary user data. No special-case filenames or precomputed findings.

For any public hosted preview, use only synthetic or otherwise clearly permitted non-personal data. Keep the public environment synthetic; an authorised operator's private deployment is a separate use context.

## 19. Correctness and edge-case tests

Implement meaningful tests and an independent small reference oracle. Include at least:

1. Leading-zero IDs survive parsing and export.
2. Quoted multiline CSVs preserve logical records.
3. Ambiguous dates require a format choice.
4. Nulls and suppressed values do not create identifier matches.
5. Same column names with unconfirmed meanings do not join.
6. Composite predicates require all components.
7. One-to-many paths return all distinct endpoint candidates.
8. Duplicate paths/rows do not inflate person counts.
9. Unknown entity identity produces reference-record wording.
10. Independent path alternatives are not incorrectly intersected.
11. A confirmed same-subject knowledge bundle can apply the intended conjunction.
12. Contradictory evidence is surfaced.
13. An empty candidate set is not labelled safe.
14. A partial traversal cannot produce a uniqueness claim.
15. Typed date/numeric generalisation preserves compatible possible matches.
16. A dropped field's effect is distinguished from an unsupported test.
17. Repair assessment catches an alternative path left intact.
18. Previously released data remains in the release model.
19. A protected column or utility requirement can make all tested repairs unsuitable.
20. Dropping records cannot hide denominator and coverage changes.
21. Undefined utility metrics are not reported as zero error.
22. Final export contents and manifest match the audited branch.
23. Formula escaping is effective and gives no artificial privacy credit.
24. Internal lineage and synthetic truth are excluded from attacker traversal.
25. Workspace, job, and artifact IDs cannot bypass authorization.
26. Plaintext test canaries do not enter graph properties, logs, or external-model payloads.
27. Deletion covers graph, vault, caches, and pending jobs.
28. Failed/cancelled imports cannot appear complete.
29. Restart preserves files, mappings, results, keys, and history.
30. Missing/wrong encryption keys fail clearly without regenerating or corrupting data.
31. Database outage blocks analysis without fake results.
32. Scenario revisions prevent stale export or misleading comparisons.
33. HTML-like cells remain text in previews and reports; instruction-like cells cannot change assistant policy or tool privileges.
34. Generalised matching remains correct when graph values are tokenised, and no ordered comparison is performed on HMAC strings.

Use a real FalkorDB instance for graph integration tests. Test-only oracles and mocks are useful, but do not replace that integration verification.

For fixtures with known fictional truth, measure supported-path precision/recall and document assumptions. Do not turn fixture accuracy into a claim of real-world re-identification accuracy.

## 20. Browser acceptance and usability

Run an actual browser-based journey using an additional unfamiliar CSV layout:

- Sign in.
- Create a workspace.
- Upload and correct parsing.
- Assign roles and confirm mappings.
- Define analytical requirements.
- Run and inspect an audit.
- Add an available export and observe the changed result.
- Evaluate at least two repairs.
- Reject an unsuitable repair.
- Select a suitable candidate and export it.
- Reopen the exported files and verify the package.
- Refresh/restart and resume.
- Delete the workspace and confirm artifacts are inaccessible.

Also test an invalid CSV, no feasible repair, an incomplete audit, a failed job, a stale result, and an unauthorised request.

Inspect desktop and narrower layouts. Fix clipping, table overflow, unreadable graphs, keyboard traps, console errors, and misleading disabled controls. Save synthetic-data screenshots for review.

The product must be usable without developer tools, hand-edited JSON, or writing Cypher. Advanced configuration may exist separately.

## 21. Documentation and delivery

Deliver:

- A complete runnable application and dependency lockfiles.
- Clear install/start/update instructions.
- A first-use guide and CSV preparation guide.
- Architecture and graph-model documentation.
- Actual parameterised Cypher query files.
- Candidate-set and matching semantics.
- Threat/release-model assumptions and unsupported cases.
- Repair and utility definitions.
- Key management, retention, deletion, backup, and restore instructions.
- Actual test commands/results and benchmark outputs.
- A known-limitations document written plainly.
- A short synthetic-data demonstration script.
- AI-assistance disclosure.

Suggested layout:

~~~
frontend/
backend/
  app/
    api/
    auth/
    ingestion/
    vault/
    graph/
    linkage/
    audit/
    repairs/
    utility/
    exports/
    assistant/
    jobs/
  tests/
queries/
fixtures/
docs/
scripts/
compose.yaml
.env.example
README.md
~~~

Do not upload user data or create paid infrastructure as part of routine development. Prepare deployment configuration for later review. Existing authorised local build/test actions should continue without unnecessary confirmation.

## 22. Implementation sequence and completion gate

Work in small, verified increments:

1. Inspect and plan; establish authentication, storage, key setup, and real graph connectivity.
2. Complete real CSV import, semantic review, and scenario manifests.
3. Implement and independently verify exact/composite linkage and candidate-set semantics.
4. Build evidence-based audit results and within-file diagnostics.
5. Implement typed repairs, full scenario re-audit, utility measurement, and immutable exports.
6. Complete job recovery, history, deletion, and administration.
7. Add the bounded assistant with external-model privacy controls.
8. Complete product UI, unfamiliar-file browser checks, performance tests, and documentation.

At each phase, verify the consequential behavior before expanding scope. Keep the application runnable. Prefer a correct, documented supported feature set to a broader misleading claim.

The core v1 is complete only when an authenticated user can take their own compatible CSVs through the entire import-to-reviewed-export workflow, with persistent results, inspectable graph evidence, independently tested repair behavior, and no required LLM credential.

Separate live-LLM verification from core-product verification. Mark it unverified if credentials or access prevent the smoke test.

Finish by reporting:

- How to install and launch.
- The exact supported product scope and measured limits.
- Which real user journeys were verified.
- Test and benchmark evidence.
- Whether live model execution was tested.
- Remaining blockers and material limitations.
- The recommended next hardening work, without calling unfinished work complete.

Start with repository inspection, state the short plan, and implement the product.

## Official references

Consult current documentation and verify installed APIs:

- [NIST SP 800-188](https://csrc.nist.gov/pubs/sp/800/188/final)
- [FalkorDB documentation](https://docs.falkordb.com/)
- [FalkorDB Python client](https://github.com/FalkorDB/falkordb-py)
- [FalkorDB persistence](https://docs.falkordb.com/operations/durability/persistence)
- [OWASP file upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP CSV injection](https://community.owasp.org/attacks/CSV_Injection)
- [Cryptography library documentation](https://cryptography.io/en/stable/)
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Codex outcomes and verification guidance](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)

