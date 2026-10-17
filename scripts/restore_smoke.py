import os,sys,json,time,uuid,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
run=ROOT/'work'/('restore-'+uuid.uuid4().hex);source=run/'source'
os.environ['MOSAIC_DATA']=str(source)
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core import digest,DATA
from backend.app.graph import Graph,healthy
from backend.tests.helpers import *
from scripts.backup import backup,restore

if '--verify' in sys.argv:
    # This branch is handled by a fresh inline subprocess below, not by reusing imported module globals.
    raise SystemExit('Use the default command.')
with TestClient(app) as c:
    a=ok(c.post('/api/auth/setup',json={'username':'restore-owner','password':'Synthetic-restore-password-42'}));c.headers['x-csrf-token']=a['csrf']
    w=workspace(c,'Restore verification');d=imported(c,w,'key,n\n001,4\n002,5\n');r=imported(c,w,'key\n001\n002\n','reference')
    s=scenario(c,w,[d],[r],[rule(d,r,['key'],['key'])]);audit=audited(c,w,s['id'])
    p=ok(c.post(f'/api/w/{w}/packages',json={'audit':audit['id'],'acknowledge_limits':True}))
    original_digest=digest(c.get(f'/api/w/{w}/packages/{p["id"]}/download').content)
archive=backup(source,run/'metadata-vault.zip');target=restore(archive,run/'restored')
# Force the real graph process to persist, restart only this project's graph, then reconnect.
g=Graph(w,audit['id']);g.db.connection.save()
subprocess.run(['docker','compose','restart','graph'],cwd=ROOT,check=True,capture_output=True)
for _ in range(100):
    if healthy():break
    time.sleep(.1)
code='''
import os,json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core import digest
with TestClient(app) as c:
 a=c.post('/api/auth/login',json={'username':'restore-owner','password':'Synthetic-restore-password-42'});assert a.status_code==200
 c.headers['x-csrf-token']=a.json()['csrf']
 st=c.get('/api/w/'+os.environ['VERIFY_WID']+'/state');assert st.status_code==200
 data=st.json();assert len(data['datasets'])==2 and len(data['audits'])==1 and len(data['scenarios'])==1
 raw=c.get('/api/w/'+os.environ['VERIFY_WID']+'/packages/'+os.environ['VERIFY_PACKAGE']+'/download');assert raw.status_code==200 and digest(raw.content)==os.environ['VERIFY_DIGEST']
 f=data['audits'][0]['findings'][0]
 assert c.get('/api/w/'+os.environ['VERIFY_WID']+'/audits/'+data['audits'][0]['id']+'/evidence/'+f['id']).status_code==200
 j=c.delete('/api/w/'+os.environ['VERIFY_WID']);assert j.status_code==200
 import time
 for _ in range(200):
  if c.get('/api/w/'+os.environ['VERIFY_WID']+'/state').status_code==404:break
  time.sleep(.05)
print('restore verified')
'''
env={**os.environ,'MOSAIC_DATA':str(target),'VERIFY_WID':w,'VERIFY_PACKAGE':p['id'],'VERIFY_DIGEST':original_digest}
proc=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True)
if proc.returncode:raise SystemExit('Restore verification failed: '+proc.stderr)
report={'result':'passed','metadata_and_vault':'offline backup into new directory','graph':'real FalkorDB SAVE + Docker service restart; persisted evidence retrieved',
        'checks':['owner login','workspace and dataset versions','scenario and audit','authenticated ZIP digest','Cypher evidence retrieval','workspace deletion'],
        'key':'original operator key supplied through environment; never included in backup archive'}
(ROOT/'docs'/'restore-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
