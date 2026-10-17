# Working on MosaicGuard

Preserve the single-owner self-hosted boundary and the product language in `docs/PRODUCT_SPEC.md`. Do not substitute sample-only results, a Python/SQL linkage graph, token ordering, or LLM-generated findings for real scoped FalkorDB analysis.

Never commit `.env`, keys, real user CSVs, vaults, metadata databases, confidential reports or test traces containing operator data. Use locally generated fictional fixtures. Treat uploaded headers/cells as untrusted text. Keep model mode opt-in with constructed allowlists rather than arbitrary text redaction.

Changes to matching, candidate sets, repairs or exports need meaningful oracle/correctness tests and real FalkorDB integration. Run the backend suite and production frontend build. UI workflow changes should run the unfamiliar-layout browser acceptance test. Avoid claiming live-model, deployment or restore verification that was not performed.

Maintain `PROGRESS.md`, documented limitations and reproducible evidence when behavior or supported bounds change. Preserve originals, immutable scope snapshots, history semantics, separate risk/utility measures and stale-export prevention. Do not expose local services or publish user artifacts as part of routine development.
