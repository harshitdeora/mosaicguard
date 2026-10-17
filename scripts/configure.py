"""First-run key creation. Never replace an existing configuration or key."""
import base64
import os
import secrets
from pathlib import Path

root=Path(__file__).resolve().parents[1]
env=root/'.env'
if env.exists():
    print('Existing .env preserved. See docs/OPERATIONS.md for key custody.'); raise SystemExit()
if (root/'data'/'metadata.sqlite').exists(): raise SystemExit('Existing data found. Restore the original .env; do not create a new key.')
key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
env.write_text('MOSAIC_MASTER_KEY='+key+'\nMOSAIC_GRAPH_PASSWORD='+secrets.token_urlsafe(32)+'\nMOSAIC_SECURE_COOKIE=false\n',encoding='utf-8')
print('Created .env. Back it up securely outside the repository. Create the owner through localhost first-run setup.')
