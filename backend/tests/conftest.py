import os
import sys
from pathlib import Path
import uuid
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from cryptography.fernet import Fernet
os.environ.setdefault('MOSAIC_MASTER_KEY',Fernet.generate_key().decode())
os.environ['MOSAIC_DATA']=str(ROOT/'work'/('test-'+uuid.uuid4().hex))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core import db, items
from backend.app.graph import Graph, healthy

@pytest.fixture(scope='session')
def client():
    assert healthy(),'Real FalkorDB required. Start docker compose up -d graph.'
    with TestClient(app,raise_server_exceptions=False) as c:
        r=c.post('/api/auth/setup',json={'username':'test-owner','password':'fictional-test-password-42'})
        assert r.status_code==200,r.text
        c.headers['x-csrf-token']=r.json()['csrf']
        yield c
    with db() as conn: jobs=conn.execute('SELECT id,wid FROM jobs').fetchall()
    for j in jobs:
        try:Graph(j['wid'],j['id']).delete()
        except Exception:pass
