import json
import os
import subprocess
import sys
import time
from pathlib import Path
import pytest
from cryptography.fernet import Fernet
from backend.app.core import *
from backend.app import jobs
from backend.app.main import app
from backend.app.graph import Graph
from backend.app.ingestion import ParseConfig,parse_csv,MAX_BYTES
from backend.app.matching import bindings
from backend.app.lease import InstanceLease
from .helpers import *

def test_upload_boundaries_and_binary(client):
    w=workspace(client)
    assert client.post(f'/api/w/{w}/uploads',files={'file':('too.csv',b'x'*(MAX_BYTES+1))}).status_code==413
    assert client.post(f'/api/w/{w}/uploads',files={'file':('../../payload.csv',b'PK\x03\x04zip')}).status_code==422
    assert client.post(f'/api/w/{w}/uploads',files={'file':('empty.csv',b'')}).status_code==422
    raw=(',' .join('c'+str(i) for i in range(50))+'\n'+('\n'.join(','.join(['x'*40]*50) for _ in range(1000)))+'\n').encode()
    assert len(raw)<MAX_BYTES
    d=parse_csv(raw,ParseConfig());assert len(d['rows'])==1000 and len(d['columns'])==50

def test_failed_cancelled_import_and_restart_recovery(client):
    c=client;w=workspace(c);jobs.stop()
    try:
        u=ok(c.post(f'/api/w/{w}/uploads',files={'file':('draft.csv',b'id\n001\n')}))
        p={'encoding':'utf-8-sig','delimiter':',','quotechar':'"','header':True,'null_tokens':[],'skip_bad_rows':False}
        preview=ok(c.post(f'/api/w/{w}/uploads/{u["id"]}/preview',json=p))
        columns=[{k:v for k,v in col.items() if k in ('id','name','type','date_format','meaning','identifier','sensitive')} for col in preview['columns']]
        body={'parse':p,'columns':columns,'role':'candidate','row_unit':'person'}
        j=ok(c.post(f'/api/w/{w}/uploads/{u["id"]}/confirm',json=body))
        ok(c.post(f'/api/w/{w}/jobs/{j["job"]}/cancel',json={}))
        jobs.start();result=wait(c,w,j['job']);assert result['state']=='cancelled'
        assert not ok(c.get(f'/api/w/{w}/state'))['datasets']
        # Retry preserves the draft's encrypted source and uses the same durable job ID.
        ok(c.post(f'/api/w/{w}/jobs/{j["job"]}/retry',json={}));assert wait(c,w,j['job'])['state']=='complete'
        # A retry of the original import request still returns its original idempotent job after draft cleanup.
        assert ok(c.post(f'/api/w/{w}/uploads/{u["id"]}/confirm',json=body))['job']==j['job']
        jobs.stop()
        fake=enqueue(w,'import',{'draft':'missing','config':{}},'failure-test')
        jobs.start();assert wait(c,w,fake)['state']=='failed'
        assert len(ok(c.get(f'/api/w/{w}/state'))['datasets'])==1
        jobs.stop()
        interrupted=enqueue(w,'audit',{'scenario':'missing'},'restart-test')
        with db() as conn:conn.execute("UPDATE jobs SET state='running' WHERE id=?",(interrupted,))
        jobs.start();assert ok(c.get(f'/api/w/{w}/jobs/{interrupted}'))['state']=='interrupted'
    finally:
        if jobs.THREAD is None or not jobs.THREAD.is_alive():jobs.start()

def test_wrong_missing_key_and_single_writer(tmp_path):
    root=Path(__file__).resolve().parents[2]
    code='from backend.app.core import DATA; print("opened")'
    for key in ('',Fernet.generate_key().decode()):
        env={**os.environ,'MOSAIC_MASTER_KEY':key}
        # core imports directly; no dotenv may replace the deliberately missing key.
        p=subprocess.run([sys.executable,'-c',code],cwd=root,env=env,capture_output=True,text=True)
        assert p.returncode!=0 and 'opened' not in p.stdout
        assert ('required' if not key else 'Wrong encryption key') in p.stderr
    with InstanceLease(tmp_path):
        with pytest.raises(RuntimeError):
            with InstanceLease(tmp_path):pass

def test_outage_blocks_analysis(client,monkeypatch):
    from backend.app import graph
    c=client;w=workspace(c);a=imported(c,w,'x\nA\n');s=scenario(c,w,[a],[],[])
    monkeypatch.setattr(graph,'healthy',lambda:False)
    r=c.post(f'/api/w/{w}/audits',json={'scenario':s['id']});assert r.status_code==503
    assert not ok(c.get(f'/api/w/{w}/state'))['audits']

def test_historical_exposure_and_release_addition(client):
    c=client;w=workspace(c)
    a=imported(c,w,'code,day\nA,2026-01-01\nB,2026-01-02\n',types={'day':'date'})
    b=imported(c,w,'code,day\nA,2026-01-01\nB,2026-01-02\n','reference',types={'day':'date'})
    extra=imported(c,w,'day,code\n2026-01-01,A\n2026-01-02,B\n','available',types={'day':'date'})
    r=rule(a,b,['code'],['code']);s=scenario(c,w,[a],[b],[r]);before=audited(c,w,s['id'])
    r2=rule(a,extra,['day'],['day']);r3=rule(extra,b,['code'],['code'])
    s2=scenario(c,w,[a],[b,extra],[r,r2,r3]);after=audited(c,w,s2['id'])
    impact=ok(c.post(f'/api/w/{w}/comparisons',json={'before':before['id'],'after':after['id']}));assert sum(x['new_path'] for x in impact['changes'])==2
    p=ok(c.post(f'/api/w/{w}/packages',json={'audit':after['id'],'acknowledge_limits':True}))
    ok(c.post(f'/api/w/{w}/releases',json={'package':p['id'],'audience':s2['audience'],'date':'2026-10-17'}))
    s3=scenario(c,w,[a],[b,extra],[r,r2,r3]);assert a['id'] in s3['historical']
    branch,repaired_a=repaired(c,w,s3['id'],[{'dataset':a['id'],'column':col(a,'code'),'kind':'drop'},{'dataset':a['id'],'column':col(a,'day'),'kind':'drop'}])
    assert repaired_a['summary']['single_candidate_path_records']==0
    assert repaired_a['summary']['historical_single_candidate_path_records']>=2

def test_exact_blanks_do_not_join_in_typed_composites():
    a={'columns':[{'id':'x','type':'text'},{'id':'n','type':'number','generalization':'numeric_bucket'}],'rows':[['  ','0..10']]}
    b={'columns':[{'id':'x','type':'text'},{'id':'n','type':'number'}],'rows':[[' ','1']]}
    left,right,stats=bindings('w',{'id':'r','source_columns':['x','n'],'target_columns':['x','n'],'predicate':'compatible','trim':True},a,b)
    assert not left and not right and stats['missing']==1
