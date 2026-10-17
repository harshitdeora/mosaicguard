# Demonstration and submission notes

MosaicGuard is a private, single-organisation tool for reviewing the linkage exposure of planned dataset releases. Its contribution is the full review workflow: user-owned CSV import, confirmed semantics, explicit audience model, graph-derived candidate sets, independent repairs, measured analytical utility and reproducible export.

Use the locally generated five-file fictional kit for any public demonstration. It contains no actual people and no hidden identity-truth columns in the product. Show both a failed repair (an alternative path remains) and a broadened typed match. Explain that a single candidate is not verified re-identification and NIST provides background rather than endorsement.

The authoritative linkage graph is FalkorDB, using the official Python client and parameterised Cypher. Exact composite hubs enforce conjunction; typed comparisons establish compatible candidate keys before graph expansion. Missing/partial analysis is explicit. SQLite handles encrypted metadata and durable jobs, not a competing record-linkage graph.

AI assistance disclosure: the application code, fixtures, documentation and tests were developed with OpenAI Codex assistance. The application makes deterministic findings; its optional external assistant explains bounded aggregates and never establishes identity or runs unrestricted queries. The built-in guidance is rules-based. Live external-model execution has not been verified.

Review the current [event rules](https://www.wemakedevs.org/hackathons/falkordb/rules) before any submission. This build does not submit to an event, publish a service, create paid infrastructure or upload personal/private/restricted source data.
