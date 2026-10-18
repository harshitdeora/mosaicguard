# First use and CSV preparation

Create the owner account on the local first-run screen. Create a named workspace. Pick **Use my CSVs** for your authorised files or **Explore a simple example** for two locally generated fictional datasets. Start with the [five-minute beginner walkthrough](BEGINNER_TUTORIAL.md). The example imports through the same upload, parse-review and durable ingestion endpoints used for other files; no precomputed audit results exist.

## Prepare and review CSVs

Use one logical row per declared person, household, organisation or event, and one unique nonblank header per column. Supported delimiters are comma, semicolon, tab and pipe. UTF-8/BOM, Windows-1252 and Latin-1 are supported. Quoted separators, quoted newlines, escaped quotes and CRLF are supported. The row number displayed is a **logical data record index**, which differs from a physical file line when fields contain newlines.

Choose a parsing preview, correct its settings, and update it before confirming. Parsing corrections preserve the encrypted upload. Previews are masked; the deliberate local reveal action shows at most ten sample records. Ragged records fail by default; explicit exclusion is available and its count carries through coverage. Malformed quoting, binary data, archives, oversized cells, duplicate/blank headers and header-only files are rejected with useful errors. Correct duplicate/blank headers in the source or use the no-header import option.

Blank fields become missing. `NA` remains a literal value unless you explicitly configure it as a null marker. Source bytes remain intact even when the reviewed parse represents blanks/null markers as missing. Nothing automatically strips accents or changes case. Text is the conservative identifier type, preserving `001` and very long integers. Reviewed numeric matching preserves exact decimal coefficients up to 100 significant digits with adjusted exponents from -100 to 100; select text outside this supported numeric range. Numeric means/medians use ordinary finite floating-point statistics and are approximate. Numeric/date suggestions are not automatic semantic mappings. Ambiguous dates require YYYY-MM-DD, DD/MM/YYYY or MM/DD/YYYY selection; timezone timestamps remain exact text in v1.

Choose roles deliberately: candidate to share; supplied reference; another audience-available export; internal only. Internal data cannot enter a linkage scenario. A row unit of unknown does not establish distinct people.

## Build a release scenario

Select candidate and audience-available versions, purpose and audience. Choose each relationship's corresponding source/destination components in matching order. Confirm the meaning, subject unit and time/cohort context. Profile fan-out first; add a selective component when the projected match count is too large.

Use typed-compatible predicates for reviewed date/number fields that may be generalised. Mapping confirmation never follows merely from equal header spelling. Optional normalisation is explicit. Independent mappings remain alternative paths. If identity keys are unresolved, leave the anchor unset and read candidate cardinalities as reference-record counts.

Select quasi-identifier diagnostics, marked sensitive fields, useful counts or numeric statistics, protected columns, minimum retention and acceptable drift. For multiple candidates, use **Candidate for analytical controls** to configure each version; definitions remain scoped to their selected dataset. Save the immutable snapshot. **Revise this scope** copies an existing review into a new editable draft; saving it creates a new revision and makes older results stale for new export.

## Read an audit

Expand a finding for its explanation before the compact evidence chain. Inspect record counts, candidate counts, required rules, missing values and coverage. A single candidate is not proof that a person has been correctly identified. Zero candidates means no match found under that test. Query exhaustion never creates a uniqueness claim. Local record previews offer filtering, pagination and deliberate value reveal.

## Compare repairs

Test two or more recipes. Column removal can block one path while another remains. Suppression loses linkage assessment coverage; that is shown in the denominators. Rare-combination suppression counts complete combinations of selected columns and suppresses only the chosen target column for combinations below the threshold; missing combinations remain unassessed. Typed generalisation can widen possible matches, so assess candidate counts and utility independently. Protected columns cannot change. A dropped analytical field makes its metric unavailable/violated. Rejected branches can be deleted; they are never applied to the original.

The comparison cards show actual re-audit counts, assessed/unassessed records, retention, missingness and each requested statistic's before/after values and drift. They do not combine these into one privacy score. A branch failing analytical requirements needs explicit conflict acceptance to export.

## Export and history

Review residual exposure and coverage, acknowledge them, then build the ZIP. The package contains CSVs, reports, schema/parse settings, audit/scenario/recipe identifiers, utility, digests and a reversible transport-escaping manifest. Original row examples, original identity chains, HMAC keys and private lineage maps are excluded. Formula-like text receives an apostrophe prefix, which consumers can remove according to the manifest; this transport operation is never credited as a privacy change. Spreadsheet behavior varies; inspect data using a CSV parser when verifying semantics.

Downloading creates an artifact. **Record as released** separately records the actual audience/date without transmitting anything. Prior releases remain in that audience's model. Future local repairs cannot undo past sharing. Historical packages indicate when a newer workspace revision exists.

## Advanced five-file demonstration

The benchmark generator in `fixtures/generate.py` can also produce about 200 fictional participants in `feedback`, `attendance`, `directory`, `badges` and `calendar` CSVs. Run `python fixtures/generate.py` to create them next to the generator. No rows are based on real people and there are no hidden entity-ID columns in the product.

1. Begin with feedback as the candidate, attendance and directory as available information. Confirm feedback.session → attendance.session and attendance.participant_key → directory.participant_key. Five fictional participants attend each session, producing an ambiguous route. Directory participant_key can be a defensible synthetic entity key.
2. Add the badge export and calendar to a new scenario. Confirm feedback.badge → badges.badge → directory.participant_key, and feedback.survey_day → calendar.survey_day → directory.participant_key. Their paths add more selective candidate sets. Compare the before/after audits with matching scopes.
3. Request department counts and mean rating by department; protect department and rating.
4. Remove only badge in one recipe. The calendar path remains; the full re-audit detects it.
5. Remove badge and generalise survey_day to quarters with a typed-compatible rule. Plausible calendar matches broaden, while department/rating measurements remain available. The attendance path still exists.
6. Record an original package as released and re-run a new scenario. Historical exposure persists despite changing the newest candidate. Inspect it separately.

For a three-minute review: show import correction, the confirmed composite/rule controls, an expanded audit, contrasting branch cards, then the package acknowledgment and explicit release-history action. Use only synthetic data for public demonstrations.
