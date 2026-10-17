# Operations, custody and recovery

## First-run secrets

`python scripts/configure.py` creates `.env` once with a random 32-byte Fernet key and a separate graph password. It refuses to overwrite existing configuration or regenerate a key over existing local data. Do not commit `.env`; keep an independently secured backup outside this repository and outside the application image. Docker supplies it at runtime. Lost keys make encrypted artifacts unreadable. A wrong/missing key fails startup rather than creating a new store. The app never silently rotates it.

Fernet uses the maintained cryptography library. Metadata object bodies, durable job payloads and vault artifacts are encrypted. Owner passwords use Argon2; sessions use cryptographically random cookies whose identifiers are hashed in SQLite. Browser cookies are HttpOnly, SameSite=Strict and expire after eight hours. Cookie-authenticated mutations require a session-bound CSRF header. Logins are limited to ten attempts per hashed client IP in 15 minutes. Preview/reveal endpoints require the same authenticated owner. Authentication and opaque workspace/object scoping are checked on every data endpoint. This is a single-organisation, single-owner installation, not a public multi-tenant service.

Graph values use workspace-scoped HMAC-SHA256 with separate rule/anchor namespaces and canonical typed JSON arrays. Clear identity values never enter graph labels/properties. HMAC does not make low-cardinality datasets anonymous; graph topology and tokens are sensitive. Restrict the graph volume, host access and backups. The password-protected graph port binds only to localhost. The image's optional graph browser port is not exposed.

No telemetry, third-party analytics, arbitrary URL ingestion, enrichment or automatic model requests are configured. Uvicorn access logs are disabled; dependency exception bodies are not emitted by jobs. Public health exposes service state and conservative bounds, not rows or object IDs. Validation errors omit rejected input values. Store and audit operator host logs with the same care as any private deployment.

## Deployment and update

`docker compose up --build -d` starts one application instance and one FalkorDB service, both with health checks and durable volumes. The app serves the built UI and API from one origin. For local development Vite proxies only `/api` to localhost 8027; no permissive CORS middleware exists.

Internet hosting requires a separately reviewed TLS reverse proxy, configured `MOSAIC_HOSTS`, `MOSAIC_SECURE_COOKIE=true`, a trusted proxy-header configuration, network restrictions and backup policy. Do not expose the Vite development server or graph port publicly. No hosting deployment is part of this build.

For updates: stop new work, back up, pull the reviewed repository revision, run `docker compose up --build -d`, check `/api/health`, and sign in to inspect existing work. Keep `.env` and durable volumes. There is no automated schema migration framework in v1; review changes before upgrading an existing store. Restore a matched application revision with its data/key/graph backup when rolling back.

## Jobs and restart recovery

Imports, audits, repairs and deletion are durable SQLite jobs. One worker serializes them. Cancellation is cooperative between bounded stages; a running Cypher operation can take up to its eight-second timeout before a checkpoint observes cancellation. Failed/cancelled jobs remove staging versions/artifacts and projections where reachable. A graph outage can delay projection cleanup; retry or workspace deletion removes that namespace when the service returns.

On restart, a previously running job becomes **interrupted**, never complete. Retry rebuilds its scoped graph namespace. Queued jobs continue. Successful snapshots remain available. Staging dataset versions are hidden. A workspace is locked against conflicting edits while a job is queued/running. Client-supplied idempotency keys prevent duplicate submissions; import has a stable default key. Cancellation arriving after the final publication checkpoint may lose a race to successful completion; the final durable job status is authoritative.

## Deletion and retention

Pending uploads, unreferenced dataset drafts, audit evidence, unrecorded repair branches and complete workspaces can be deleted. Referenced source versions and recorded release branches are retained to avoid silently invalidating immutable review/history context; use full workspace deletion to remove them locally. Minimal local release records survive individual audit/artifact removal. Deletion cannot establish that recipients no longer possess an already shared file.

Workspace deletion marks a tombstone immediately, blocks downloads/results, cancels related jobs, then removes audit/job graph namespaces, encrypted vault files, object payloads and related jobs. A graph outage leaves the tombstone and a retryable failed deletion rather than claiming success. One minimal deletion job record remains with opaque IDs/state only. It contains no rows or accessible artifacts. Object payload deletion removes logical access; SQLite free pages, filesystem remnants and backups are not forensic erasure. Exported copies are outside the application's custody.

There is no automatic retention policy. Owners should review old uploads, audits, repair branches and packages; bounded per-workspace quotas prevent unlimited expensive operations in one workspace. Backups inherit the operator's retention policy. Keep encryption keys for every retained encrypted backup.

## Back up a Docker installation

Stop the app to create a consistent metadata/artifact boundary. Then stop the graph cleanly so RDB/AOF files are flushed. Back up the **whole pair** of volumes plus the exact Git revision; keep `.env` separately. For PowerShell, from the repository root:

```powershell
docker compose stop app
docker compose stop graph
New-Item -ItemType Directory -Force work/backup
docker cp mosaicguard-app-1:/data work/backup/app-data
docker cp mosaicguard-graph-1:/var/lib/falkordb/data work/backup/graph-data
git rev-parse HEAD | Set-Content work/backup/revision.txt
docker compose up -d
```

`docker cp` can copy from stopped containers. Verify actual container names with `docker compose ps -a` if a Compose project name was overridden. Secure the copied folder; **graph files are not application-encrypted**. Encrypt the backup using an established operator-managed backup system, restrict access, and do not commit it.

Restore into new volumes/containers using the same application revision and original `.env`. Stop both services, copy the complete matching app and graph directories back to their original locations, preserve owner UID 10001 on app-data, then start graph and app. Do not mix a newer metadata snapshot with an older graph snapshot. First restore to an isolated local deployment and validate login, dataset versions, an evidence path, an export digest and history before replacing a running installation.

## Back up a local Python installation

Stop the Python application, preserve the real graph volume separately, then:

```powershell
.\.venv\Scripts\python.exe scripts/backup.py backup data work/private-backup.zip
.\.venv\Scripts\python.exe scripts/backup.py restore work/private-backup.zip work/restored-data
```

The script acquires the application's OS lease, backs up SQLite consistently and packages key-check plus encrypted vault files. It never includes `.env`, refuses to overwrite a backup/restore directory and rejects archive path traversal. Supply the original key and set `MOSAIC_DATA` to the new restored directory when verifying. Keep graph persistence files with the same checkpoint. See `docs/restore-results.json` for the performed synthetic restore and real graph restart verification.

## Optional model mode

Set `OPENAI_API_KEY` only in the server environment and choose `OPENAI_MODEL`. In workspace Settings inspect the exact initial outbound request and fixed payload policy before enabling. Outbound fields are deliberately constructed counts, opaque aliases and bounded audit/utility aggregates; original filenames, schema names, cell text, identity examples and arbitrary user chat are excluded. Counts can still disclose sensitive information. Keep the mode off when these aggregates are not permitted to leave the deployment.

The adapter uses strict empty-argument read-only tools, four total tool calls, bounded outputs, timeouts, one retry and one concurrent request. It never runs model-written Cypher, SQL or Python and cannot publish or overwrite originals. Dynamic tool responses use the same allowlist and exact sanitized requests are inspectable in encrypted history. Changing provider model requires renewed consent. The built-in assistant is accurately labelled rules-based. No live call was verified in this build because no model key was configured.
