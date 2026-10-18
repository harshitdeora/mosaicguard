# Railway deployment

Railway fits MosaicGuard's current architecture because it supports a Dockerfile-built web service, private service networking and persistent volumes. Vercel's request-driven containers have ephemeral local filesystems and do not fit the current SQLite, encrypted vault, durable worker and self-hosted FalkorDB design without replacing those components.

This remains a **single-organisation, single-owner** deployment. The public URL may be reachable by many browsers, but only one owner account exists. Do not share that owner password among unrelated users. A multi-tenant service needs separate account, tenancy, quota, deletion, audit and abuse-control work.

Railway does not execute `compose.yaml` directly. Create two services in one project.

## 1. Application service

Create a service from the private GitHub repository `harshitdeora/mosaicguard`. Railway uses the root `Dockerfile` and `railway.toml`.

Attach a persistent volume at `/data`. Configure these private variables:

```text
MOSAIC_MASTER_KEY=<new Fernet key; retain an independent secure backup>
MOSAIC_GRAPH_PASSWORD=<new random graph password>
MOSAIC_GRAPH_HOST=graph.railway.internal
MOSAIC_GRAPH_PORT=6379
MOSAIC_DATA=/data
MOSAIC_SECURE_COOKIE=true
MOSAIC_HOSTS=*.up.railway.app
MOSAIC_SETUP_TOKEN=<new random one-time owner-setup token>
FORWARDED_ALLOW_IPS=*
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Keep external-model mode blank unless its exact payload policy is acceptable. Generate a Railway domain only for this application service. TLS is supplied at the Railway edge.

## 2. Graph service

Create a service named exactly `graph` from this image:

```text
falkordb/falkordb@sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a
```

Do not generate a public domain for the graph. Attach a persistent volume at `/var/lib/falkordb/data` and configure:

```text
MOSAIC_GRAPH_PASSWORD=<same graph password as the app service>
REDIS_ARGS=--requirepass <same graph password> --appendonly yes --save 60 1
```

Both services communicate over Railway's private network. The app's `/api/ready` check remains unavailable until FalkorDB responds.

## 3. First owner and verification

Open the generated application URL, choose an owner username and a unique password of at least 12 characters, and enter the deployment setup token. The token prevents an unknown visitor from claiming a newly published instance before the owner does.

After setup:

1. Sign out and sign in again over HTTPS.
2. Import only the fictional beginner example first.
3. Run its audit and confirm 6 assessed path records and 2 single-candidate path records.
4. Restart each service once and confirm the workspace still exists.
5. Back up both volumes and the master key before importing authorised private data.

Railway's current Hobby plan has a $5 monthly minimum that counts toward usage; compute beyond that and volume storage are usage-billed. Review the current Railway pricing page and set a spending limit before sustained use.
