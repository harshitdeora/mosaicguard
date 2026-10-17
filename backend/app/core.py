import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.getenv('MOSAIC_DATA', str(ROOT / 'data')))
DATA.mkdir(parents=True, exist_ok=True)
key = os.getenv('MOSAIC_MASTER_KEY', '')
if not key:
    raise RuntimeError('MOSAIC_MASTER_KEY is required. Run scripts/configure.py once; preserve the key for existing data.')
try:
    CIPHER = Fernet(key.encode())
except Exception:
    raise RuntimeError('MOSAIC_MASTER_KEY must be a Fernet key.') from None
CHECK = DATA / 'key-check'
if CHECK.exists():
    try:
        if CIPHER.decrypt(CHECK.read_bytes()) != b'mosaicguard-key-v1': raise InvalidToken
    except InvalidToken:
        raise RuntimeError('Wrong encryption key. Restore the original key; existing data was not modified.') from None
elif (DATA / 'metadata.sqlite').exists():
    raise RuntimeError('Missing key-check for existing data. Restore the complete backup before starting.')
else:
    CHECK.write_bytes(CIPHER.encrypt(b'mosaicguard-key-v1'))

def uid(): return uuid.uuid4().hex
def digest(data): return hashlib.sha256(data).hexdigest()
def encode(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
def seal(value): return CIPHER.encrypt(encode(value))
def unseal(value): return json.loads(CIPHER.decrypt(value))
def token(wid, namespace, values):
    # JSON array is an unambiguous typed, length-delimited serialization. Keys never leave the server.
    wk = hmac.new(key.encode(), encode(['workspace-key-v1', wid]), hashlib.sha256).digest()
    return hmac.new(wk, encode(['token-v1', namespace, values]), hashlib.sha256).hexdigest()

DB_LOCK = threading.RLock()
MUTATION = threading.RLock()
@contextmanager
def db():
    with DB_LOCK:
        c = sqlite3.connect(DATA / 'metadata.sqlite', timeout=20)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally: c.close()

with db() as c:
    c.executescript('''
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS owner(id INTEGER PRIMARY KEY CHECK(id=1), username TEXT, password TEXT);
    CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, csrf TEXT, expires REAL);
    CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY, kind TEXT, wid TEXT, body BLOB, created REAL);
    CREATE INDEX IF NOT EXISTS objects_scope ON objects(wid,kind);
    CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, wid TEXT, kind TEXT, state TEXT, stage TEXT,
        payload BLOB, result BLOB, error TEXT, cancelled INTEGER DEFAULT 0, created REAL, idem TEXT);
    CREATE UNIQUE INDEX IF NOT EXISTS job_idem ON jobs(wid,idem);
    CREATE TABLE IF NOT EXISTS login_attempts(ip TEXT, ts REAL);
    ''')

def put(kind, wid, body, oid=None):
    oid = oid or uid()
    value = dict(body, id=oid)
    with db() as c:
        c.execute('INSERT INTO objects VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                  (oid, kind, wid, seal(value), time.time()))
    return value

def get(oid, kind=None, wid=None):
    with db() as c: r = c.execute('SELECT * FROM objects WHERE id=?', (oid,)).fetchone()
    if not r or (kind and r['kind'] != kind) or (wid and r['wid'] != wid): raise HTTPException(404, 'Item not found in this workspace.')
    return unseal(r['body'])

def items(kind, wid=None):
    with db() as c:
        rs = c.execute('SELECT body FROM objects WHERE kind=?'+(' AND wid=?' if wid else '')+' ORDER BY created', (kind,wid) if wid else (kind,)).fetchall()
    return [unseal(r['body']) for r in rs]

def remove(oid):
    with db() as c: c.execute('DELETE FROM objects WHERE id=?', (oid,))

def workspace(wid):
    w = get(wid, 'workspace', wid)
    if w.get('deleting'): raise HTTPException(409, 'Workspace deletion is pending. Results are unavailable.')
    return w

def active(wid):
    with db() as c: return c.execute("SELECT id FROM jobs WHERE wid=? AND state IN ('queued','running')", (wid,)).fetchone()

def editable(wid):
    workspace(wid)
    if active(wid): raise HTTPException(409, 'Wait for or cancel the active workspace job before changing its inputs.')

def bump(wid):
    w = workspace(wid); w['revision'] += 1
    put('workspace',wid,w,wid)
    return w['revision']

def vault_write(wid, data, aid=None):
    aid = aid or uid()
    folder = DATA / 'vault' / wid
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / (aid+'.tmp')
    tmp.write_bytes(CIPHER.encrypt(data)); tmp.replace(folder / (aid+'.bin'))
    return aid

def vault_read(wid, aid):
    # IDs are generated; never accept a path from a client.
    if len(aid)!=32 or any(c not in '0123456789abcdef' for c in aid): raise HTTPException(404, 'Artifact not found.')
    p = DATA / 'vault' / wid / (aid+'.bin')
    if not p.exists(): raise HTTPException(404, 'Artifact not found.')
    try: return CIPHER.decrypt(p.read_bytes())
    except InvalidToken: raise HTTPException(503,'Artifact cannot be decrypted. Check key custody and restore instructions.') from None

def vault_delete(wid, aid):
    p = DATA / 'vault' / wid / (aid+'.bin')
    p.unlink(missing_ok=True)

def enqueue(wid, kind, payload, idem):
    with db() as c:
        old=c.execute('SELECT id FROM jobs WHERE wid=? AND idem=?',(wid,idem)).fetchone()
        if old: return old['id']
        jid=uid()
        c.execute('INSERT INTO jobs(id,wid,kind,state,stage,payload,created,idem) VALUES(?,?,?,?,?,?,?,?)',
                  (jid,wid,kind,'queued','Waiting for worker',seal(payload),time.time(),idem))
    return jid

def job_public(r):
    return {k:r[k] for k in ('id','wid','kind','state','stage','error','created')} | {'result':unseal(r['result']) if r['result'] else None}

class Cancelled(Exception): pass

def checkpoint(jid, stage):
    with db() as c:
        j=c.execute('SELECT cancelled FROM jobs WHERE id=?',(jid,)).fetchone()
        if not j or j['cancelled']: raise Cancelled()
        c.execute('UPDATE jobs SET stage=? WHERE id=?',(stage,jid))
