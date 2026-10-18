import copy
import io
import json
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2]/'.env')
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import FastAPI, Request, Response, Depends, HTTPException, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.formparsers import MultiPartParser
from pydantic import Field
from .core import *
from .ingestion import *
from .models import Scenario, Repair, Rule
from .graph import healthy, require_graph, Graph
from .analysis import load_dataset
from .matching import bindings
from .exports import package
from . import jobs
from .lease import InstanceLease

MultiPartParser.spool_max_size=3*1024*1024
PH=PasswordHasher()
SECURE=os.getenv('MOSAIC_SECURE_COOKIE','false').lower()=='true'
SETUP_TOKEN=os.getenv('MOSAIC_SETUP_TOKEN','')

@asynccontextmanager
async def lifespan(app):
    with InstanceLease(DATA):
        jobs.start()
        yield
        jobs.stop()

app=FastAPI(title='MosaicGuard',version='0.1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=os.getenv('MOSAIC_HOSTS','localhost,127.0.0.1,testserver').split(','))

@app.middleware('http')
async def boundaries(request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        expected=str(request.base_url).rstrip('/')
        if origin and origin!=expected: return JSONResponse({'detail':'Cross-origin mutations are blocked.'},403)
        if request.headers.get('sec-fetch-site')=='cross-site': return JSONResponse({'detail':'Cross-site requests are blocked.'},403)
    length=request.headers.get('content-length')
    if length and (not length.isdigit() or int(length)>MAX_BYTES+65536): return JSONResponse({'detail':'Request exceeds the upload limit.'},413)
    if request.url.path.endswith('/uploads') and request.method=='POST' and not length:
        return JSONResponse({'detail':'Upload requires a declared content length.'},411)
    response=await call_next(request)
    response.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
                             'Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
    if SECURE: response.headers['Strict-Transport-Security']='max-age=31536000'
    return response

@app.exception_handler(RequestValidationError)
async def invalid(request,exc):
    return JSONResponse({'detail':'Invalid request. Check the selected fields, types and supported bounds.','fields':['.'.join(map(str,e['loc'])) for e in exc.errors()][:10]},422)

@app.exception_handler(Exception)
async def internal(request,exc): return JSONResponse({'detail':'Operation could not be completed. Check service health and administrator documentation.'},500)

def session(request:Request):
    raw=request.cookies.get('mosaic_session','')
    with db() as c:
        c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
        r=c.execute('SELECT * FROM sessions WHERE id=?',(digest(raw.encode()),)).fetchone()
    if not r: raise HTTPException(401,'Sign in to continue.')
    if request.method not in ('GET','HEAD','OPTIONS') and not secrets.compare_digest(request.headers.get('x-csrf-token',''),r['csrf']):
        raise HTTPException(403,'Invalid CSRF token. Refresh and retry.')
    wid=request.path_params.get('wid')
    if wid:
        w=get(wid,'workspace',wid)
        if w.get('deleting') and '/jobs' not in request.url.path: raise HTTPException(409,'Workspace deletion is pending. Downloads and results are blocked.')
    return dict(r)

def logged_in(response):
    sid=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
    with db() as c: c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(sid.encode()),csrf,time.time()+8*3600))
    response.set_cookie('mosaic_session',sid,httponly=True,secure=SECURE,samesite='strict',max_age=8*3600,path='/')
    return {'authenticated':True,'csrf':csrf}

class Credentials(Strict):
    username: str=Field(min_length=3,max_length=64)
    password: str=Field(min_length=12,max_length=256)
    setup_token: str | None=Field(default=None,max_length=256)

def verify_setup_token(value):
    if SETUP_TOKEN and not secrets.compare_digest(value or '',SETUP_TOKEN):
        raise HTTPException(403,'The deployment setup token is incorrect.')

@app.get('/api/health')
def health(): return {'application':'ready','graph':'ready' if healthy() else 'unavailable','limits':{'file_bytes':MAX_BYTES,'file_rows':MAX_ROWS,'workspace_rows':MAX_WORKSPACE_ROWS,'columns':50},'model_configured':bool(os.getenv('OPENAI_API_KEY'))}

@app.get('/api/ready')
def ready():
    value=health()
    return value if value['graph']=='ready' else JSONResponse(value,status_code=503)

@app.get('/api/auth/status')
def auth_status():
    with db() as c: exists=c.execute('SELECT 1 FROM owner').fetchone()
    return {'setup_required':not bool(exists),'setup_token_required':bool(SETUP_TOKEN and not exists)}

@app.post('/api/auth/setup')
def setup(body:Credentials,response:Response):
    verify_setup_token(body.setup_token)
    with MUTATION,db() as c:
        if c.execute('SELECT 1 FROM owner').fetchone(): raise HTTPException(409,'An owner already exists. Sign in.')
        c.execute('INSERT INTO owner VALUES(1,?,?)',(body.username,PH.hash(body.password)))
    return logged_in(response)

@app.post('/api/auth/login')
def login(body:Credentials,request:Request,response:Response):
    ip=token('auth','ip',[request.client.host if request.client else 'local'])
    with db() as c:
        c.execute('DELETE FROM login_attempts WHERE ts<?',(time.time()-900,))
        n=c.execute('SELECT count(*) FROM login_attempts WHERE ip=?',(ip,)).fetchone()[0]
        if n>=10: raise HTTPException(429,'Too many attempts. Try again after 15 minutes.')
        c.execute('INSERT INTO login_attempts VALUES(?,?)',(ip,time.time()))
        owner=c.execute('SELECT * FROM owner').fetchone()
    valid=False
    if owner:
        try: valid=PH.verify(owner['password'],body.password) and secrets.compare_digest(owner['username'],body.username)
        except VerificationError: pass
    if not valid: raise HTTPException(401,'Incorrect username or password.')
    with db() as c: c.execute('DELETE FROM login_attempts WHERE ip=?',(ip,))
    return logged_in(response)

@app.get('/api/auth/me')
def me(s=Depends(session)): return {'authenticated':True,'csrf':s['csrf']}

@app.post('/api/auth/logout')
def logout(response:Response,s=Depends(session)):
    with db() as c: c.execute('DELETE FROM sessions WHERE id=?',(s['id'],))
    response.delete_cookie('mosaic_session',path='/');return {'logged_out':True}

class WorkspaceName(Strict): name:str=Field(min_length=1,max_length=120)
@app.get('/api/workspaces')
def workspaces(s=Depends(session)): return items('workspace')

@app.get('/api/examples')
def examples(s=Depends(session)):
    from fixtures.generate import beginner_kit
    return beginner_kit()

@app.post('/api/workspaces')
def create_workspace(body:WorkspaceName,s=Depends(session)):
    wid=uid();return put('workspace',wid,{'name':body.name,'revision':1,'deleting':False,'created':time.time()},wid)

@app.get('/api/w/{wid}/state')
def state(wid,s=Depends(session)):
    w=workspace(wid)
    datasets=[{k:v for k,v in d.items() if k not in ('data_artifact','source_artifact')} for d in items('dataset',wid) if d['status']=='ready']
    with db() as c: js=c.execute('SELECT * FROM jobs WHERE wid=? ORDER BY created DESC LIMIT 50',(wid,)).fetchall()
    return {'workspace':w,'datasets':datasets,'uploads':[{k:v for k,v in u.items() if k not in ('source_artifact','preview')} for u in items('upload',wid)],
            'scenarios':items('scenario',wid),'audits':items('audit',wid),'branches':items('branch',wid),'packages':items('package',wid),
            'releases':items('release',wid),'jobs':[job_public(j) for j in js]}

@app.post('/api/w/{wid}/uploads')
async def upload(wid,file:UploadFile=File(...),s=Depends(session)):
    with MUTATION: editable(wid)
    raw=bytearray()
    while chunk:=await file.read(65536):
        raw.extend(chunk)
        if len(raw)>MAX_BYTES: raise HTTPException(413,'File exceeds 2 MB.')
    if not raw: fail('The upload is empty.')
    if b'\x00' in raw or bytes(raw[:4]) in (b'PK\x03\x04',b'%PDF'): fail('Binary files and archives are not supported. Choose a CSV.')
    # All filenames are display-only. Generated paths are used for storage.
    name=(file.filename or 'Uploaded CSV').replace('\\','/').split('/')[-1][:160]
    with MUTATION:
        editable(wid)
        if len(items('upload',wid))>=10: fail('Review or delete an existing pending upload first (maximum 10).')
        aid=vault_write(wid,bytes(raw));oid=uid()
        draft=put('upload',wid,{'name':name,'source_artifact':aid,'digest':digest(raw),'bytes':len(raw),'preview':None},oid)
    return {'id':oid,'name':name,'bytes':len(raw),'digest':draft['digest']}

@app.post('/api/w/{wid}/uploads/{oid}/preview')
def import_preview(wid,oid,cfg:ParseConfig,s=Depends(session)):
    with MUTATION:
        editable(wid);u=get(oid,'upload',wid)
        data=parse_csv(vault_read(wid,u['source_artifact']),cfg,(u.get('preview') or {}).get('columns'))
        u['preview']={'columns':data['columns'],'parse':cfg.model_dump()};put('upload',wid,u,oid)
    return {'columns':profile(data),'rows':[['•••' if v is not None else None for v in row] for row in data['rows'][:10]],
            'imported_rows':len(data['rows']),'excluded':data['excluded'],'warnings':data['warnings'],'masked':True}

@app.post('/api/w/{wid}/uploads/{oid}/reveal')
def reveal_upload(wid,oid,cfg:ParseConfig,s=Depends(session)):
    u=get(oid,'upload',wid);d=parse_csv(vault_read(wid,u['source_artifact']),cfg,(u.get('preview') or {}).get('columns'))
    return {'rows':d['rows'][:10],'columns':d['columns'],'deliberate_local_reveal':True}

@app.post('/api/w/{wid}/uploads/{oid}/confirm')
def confirm_import(wid,oid,body:ConfirmImport,request:Request,s=Depends(session)):
    with MUTATION:
        # Honor retries with the same key before conflict checks.
        idem=request.headers.get('idempotency-key') or 'import:'+oid
        with db() as c: old=c.execute('SELECT id FROM jobs WHERE wid=? AND idem=?',(wid,idem)).fetchone()
        if old:return {'job':old['id']}
        u=get(oid,'upload',wid)
        editable(wid)
        if body.role not in ('candidate','reference','available','internal') or body.row_unit not in ('person','household','organisation','event','unknown'): fail('Choose a supported dataset role and row unit.')
        d=parse_csv(vault_read(wid,u['source_artifact']),body.parse,(u.get('preview') or {}).get('columns'))
        validate_columns(d,body.columns)
        if sum(ds['rows'] for ds in items('dataset',wid))+len(d['rows'])>MAX_WORKSPACE_ROWS: fail('Workspace ceiling is 5,000 records.')
        return {'job':enqueue(wid,'import',{'draft':oid,'config':body.model_dump()},idem)}

@app.delete('/api/w/{wid}/uploads/{oid}')
def delete_upload(wid,oid,s=Depends(session)):
    with MUTATION:
        editable(wid);u=get(oid,'upload',wid);vault_delete(wid,u['source_artifact']);remove(oid)
    return {'deleted':True}

class Preview(Strict):
    offset:int=Field(default=0,ge=0)
    limit:int=Field(default=20,ge=1,le=50)
    reveal_columns:list[str]=Field(default_factory=list,max_length=50)
    filter_column:str | None=None
    filter_value:str=Field(default='',max_length=200)

@app.post('/api/w/{wid}/datasets/{did}/preview')
def dataset_preview(wid,did,p:Preview,s=Depends(session)):
    d=load_dataset(wid,did);index={c['id']:i for i,c in enumerate(d['columns'])}
    if any(c not in index for c in p.reveal_columns) or (p.filter_column and p.filter_column not in index): fail('Choose columns in this dataset version.')
    selected=[(i,row) for i,row in enumerate(d['rows']) if not p.filter_column or p.filter_value.casefold() in str(row[index[p.filter_column]] or '').casefold()]
    return {'columns':d['columns'],'total':len(selected),'offset':p.offset,'rows':[{'record':i+1,'values':[v if c['id'] in p.reveal_columns else '•••' if v is not None else None for c,v in zip(d['columns'],row)]} for i,row in selected[p.offset:p.offset+p.limit]]}

@app.get('/api/w/{wid}/mapping-suggestions')
def mapping_suggestions(wid,s=Depends(session)):
    ds=items('dataset',wid);suggestions=[]
    for a in ds:
        for b in ds:
            if a['id']==b['id'] or b['role']=='internal':continue
            for ca in a['columns']:
                for cb in b['columns']:
                    if ca['name'].casefold()==cb['name'].casefold() and ca['type']==cb['type']:
                        suggestions.append({'source':a['id'],'target':b['id'],'source_column':ca['id'],'target_column':cb['id'],'reason':'Matching header spelling and reviewed type. Meaning is not established; confirm subject and context before use.'})
    return suggestions[:100]

@app.post('/api/w/{wid}/rule-profile')
def rule_profile(wid,r:Rule,s=Depends(session)):
    _,_,stats=bindings(wid,r.model_dump(),load_dataset(wid,r.source),load_dataset(wid,r.target));return stats

def validate_scenario(wid,body):
    d=body.model_dump();datasets={x['id']:x for x in items('dataset',wid)}
    if len(set(d['candidates']))!=len(d['candidates']):fail('Candidate versions must be distinct.')
    historical=[]
    for release in items('release',wid):
        if release['audience']==d['audience']:
            old=get(release['scenario'],'scenario',wid)
            for did in release['datasets']:
                if did in datasets:
                    historical.append(did)
                    if did not in d['available'] and did not in d['candidates']: d['available'].append(did)
            # The recorded review already established these references and rules for this audience.
            for did in old['available']:
                if did in datasets and did not in d['available'] and did not in d['candidates']:d['available'].append(did)
            for rule in old['rules']:
                if rule['source'] in datasets and rule['target'] in datasets:
                    historical_rule=copy.deepcopy(rule)
                    historical_rule['id']=token(wid,'historical-rule',[release['id'],rule['id']])[:32]
                    historical_rule['_historical']=True
                    if not any(r['source']==rule['source'] and r['target']==rule['target'] and r['source_columns']==rule['source_columns'] and r['target_columns']==rule['target_columns'] for r in d['rules']):
                        d['rules'].append(historical_rule)
            for a in old['anchors']:
                if a['dataset'] in datasets and not any(x['dataset']==a['dataset'] for x in d['anchors']):d['anchors'].append(a)
    if len(d['available'])>15 or len(d['rules'])>40:fail('Release history exceeds the bounded v1 scenario. Reduce new inputs or archive this review outside the product; do not silently omit history.')
    allowed=set(d['candidates']+d['available'])
    for did in allowed:
        ds=datasets.get(did)
        if not ds or ds['status']!='ready':fail('All selected versions must be ready in this workspace.')
        if ds['role']=='internal': fail('Internal-only datasets cannot participate. Reimport with a reviewed eligible role.')
    if any(datasets[x]['role']!='candidate' for x in d['candidates']):fail('Choose candidate dataset versions for release.')
    colmap={did:{c['id']:c for c in ds['columns']} for did,ds in datasets.items()}
    ruleids=[]
    for r in d['rules']:
        ruleids.append(r['id'])
        if r['source'] not in allowed or r['target'] not in allowed or r['source']==r['target']:fail('Rules must link different selected versions. Review historical rules and references if a historical version is missing.')
        if len(r['source_columns'])!=len(r['target_columns']):fail('Composite rules require equal component counts.')
        for a,b in zip(r['source_columns'],r['target_columns']):
            if a not in colmap[r['source']] or b not in colmap[r['target']]:
                if r.get('_historical'):continue # An explicitly removed historical field remains a blocked predicate.
                fail('Rule column is not in the selected version.')
            if colmap[r['source']][a]['type']!=colmap[r['target']][b]['type']:fail('Join components require compatible reviewed types.')
        if r['subject']=='unknown' and r['confirmed']:fail('Confirm the subject unit before enabling a rule.')
        if r['confirmed'] and any(datasets[x]['row_unit'] not in (r['subject'],'unknown') for x in (r['source'],r['target'])):fail('Rule subject conflicts with the declared dataset row unit.')
    if len(set(ruleids))!=len(ruleids):fail('Rule IDs must be unique.')
    for a in d['anchors']:
        if a['dataset'] not in allowed or any(c not in colmap[a['dataset']] for c in a['columns']):fail('Anchor must use columns of a selected version.')
        if datasets[a['dataset']]['row_unit']=='unknown':fail('An entity anchor requires a reviewed row unit.')
        if len(a['columns'])==1 and re.search(r'name',colmap[a['dataset']][a['columns'][0]]['name'],re.I):fail('Names alone cannot establish an identity anchor. Supply a defensible entity key.')
    for q in d['quasi_identifiers']:
        if q['dataset'] not in d['candidates'] or any(c not in colmap[q['dataset']] for c in q['columns']):fail('Choose quasi-identifiers in a candidate version.')
    for u in d['utility']:
        if u['dataset'] not in d['candidates']:fail('Utility requirements must concern candidate versions.')
        if any(c and c not in colmap[u['dataset']] for c in (u['group'],u['value'])):fail('Utility column is unavailable.')
    if any(c not in {c for did in d['candidates'] for c in colmap[did]} for c in d['protected']):fail('Protected column is unavailable.')
    byid={r['id']:r for r in d['rules']}
    for b in d['bundles']:
        ends=[]
        for path in b['paths']:
            current=b['source'];subjects=set();contexts=set()
            if not path or len(path)>d['max_depth']:fail('Knowledge bundle path is outside search bounds.')
            for rid in path:
                r=byid.get(rid)
                if not r or not r['confirmed'] or r['source']!=current:fail('Bundle paths must use consecutive confirmed rules.')
                subjects.add(r['subject']);contexts.add(r['context']);current=r['target']
            if len(subjects)!=1 or len(contexts)!=1:fail('Bundled predicates must share a confirmed subject and context.')
            ends.append(current)
        if len(set(ends))!=1:fail('Bundle paths must end at the same reference version.')
    d['historical']=list(dict.fromkeys(historical))
    return d

@app.post('/api/w/{wid}/scenarios')
def create_scenario(wid,body:Scenario,s=Depends(session)):
    with MUTATION:
        editable(wid)
        if len(items('scenario',wid))>=50:fail('Workspace snapshot limit reached (50). Export evidence and start a new review workspace.')
        d=validate_scenario(wid,body);d['workspace_revision']=bump(wid)
        return put('scenario',wid,d)

class AuditRequest(Strict): scenario:str
@app.post('/api/w/{wid}/audits')
def run_audit(wid,body:AuditRequest,request:Request,s=Depends(session)):
    with MUTATION:
        editable(wid);require_graph();scenario=get(body.scenario,'scenario',wid)
        if len(items('audit',wid))>=50:fail('Workspace audit limit reached (50). Delete unneeded audit evidence before running more.')
        if scenario['workspace_revision']!=workspace(wid)['revision']: raise HTTPException(409,'Scenario is stale. Save a new revision.')
        return {'job':enqueue(wid,'audit',body.model_dump(),request.headers.get('idempotency-key') or uid())}

@app.get('/api/w/{wid}/audits/{aid}/evidence/{fid}')
def evidence(wid,aid,fid,s=Depends(session)):
    get(aid,'audit',wid);require_graph();rows=Graph(wid,aid).evidence(fid)
    if not rows:raise HTTPException(404,'Finding evidence not found.')
    return json.loads(rows[0][0])

@app.post('/api/w/{wid}/repairs')
def repair(wid,body:Repair,request:Request,s=Depends(session)):
    with MUTATION:
        editable(wid);require_graph();base=get(body.scenario,'scenario',wid)
        if len(items('branch',wid))>=10:fail('Bounded recipe search reached 10 branches. Delete an unneeded branch before testing another.')
        if base['workspace_revision']!=workspace(wid)['revision']:raise HTTPException(409,'Scenario is stale.')
        for t in body.recipe:
            if t.dataset not in base['candidates']:fail('Only current candidate versions can be repaired; reference data remains unchanged.')
            if t.column in base['protected']:fail('A protected analytical column cannot be changed.')
            if t.column not in {c['id'] for c in get(t.dataset,'dataset',wid)['columns']}:fail('Repair column is unavailable.')
            if any(cid not in {c['id'] for c in get(t.dataset,'dataset',wid)['columns']} for cid in t.combination_columns):fail('Rare-combination column is unavailable.')
        return {'job':enqueue(wid,'repair',body.model_dump(),request.headers.get('idempotency-key') or uid())}

@app.get('/api/w/{wid}/jobs/{jid}')
def job(wid,jid,s=Depends(session)):
    with db() as c:r=c.execute('SELECT * FROM jobs WHERE id=? AND wid=?',(jid,wid)).fetchone()
    if not r:raise HTTPException(404,'Job not found.')
    return job_public(r)

@app.post('/api/w/{wid}/jobs/{jid}/cancel')
def cancel_job(wid,jid,s=Depends(session)):
    with db() as c:
        r=c.execute('SELECT * FROM jobs WHERE id=? AND wid=?',(jid,wid)).fetchone()
        if not r:raise HTTPException(404,'Job not found.')
        if r['kind']=='delete_workspace':raise HTTPException(409,'Deletion cannot be cancelled after it starts.')
        if r['state'] not in ('queued','running'):raise HTTPException(409,'This job is no longer cancellable.')
        c.execute('UPDATE jobs SET cancelled=1 WHERE id=?',(jid,))
    return {'cancellation_requested':True}

@app.post('/api/w/{wid}/jobs/{jid}/retry')
def retry_job(wid,jid,s=Depends(session)):
    with MUTATION,db() as c:
        r=c.execute('SELECT * FROM jobs WHERE id=? AND wid=?',(jid,wid)).fetchone()
        if not r:raise HTTPException(404,'Job not found.')
        if r['state'] not in ('failed','cancelled','interrupted'):raise HTTPException(409,'Only failed, cancelled or interrupted jobs can be retried.')
        if active(wid):raise HTTPException(409,'Another workspace job is active.')
        c.execute("UPDATE jobs SET state='queued',stage='Retry queued',cancelled=0,error=NULL,result=NULL WHERE id=?",(jid,))
    return {'job':jid}

class ExportRequest(Strict):
    audit:str
    acknowledge_limits:bool=False
    accept_utility_violation:bool=False

@app.post('/api/w/{wid}/packages')
def export(wid,body:ExportRequest,s=Depends(session)):
    with MUTATION:
        editable(wid);a=get(body.audit,'audit',wid);scenario=get(a['scenario'],'scenario',wid)
        if len(items('package',wid))>=25:fail('Workspace package limit reached (25). Keep exported copies and start a new review workspace.')
        if a['workspace_revision']!=workspace(wid)['revision']:raise HTTPException(409,'Audit is stale. Re-audit a new scenario revision before export.')
        if not body.acknowledge_limits:fail('Review and acknowledge residual findings and coverage limits before export.')
        branches=[b for b in items('branch',wid) if b['audit']==a['id']]
        b=branches[0] if branches else None
        utility=b['utility'] if b else {'status':'baseline','metrics':[],'retention':[]}
        if utility['status']=='violated' and not body.accept_utility_violation:fail('This repair violates analytical requirements. Reject it or explicitly accept the conflict.')
        data={d:load_dataset(wid,d) for d in scenario['candidates']}
        if any(digest(encode(d))!=a['dataset_digests'].get(did) for did,d in data.items()):raise HTTPException(409,'Candidate artifact no longer matches its audit digest. Re-audit before export.')
        raw,manifest=package(data,scenario,a,b['recipe'] if b else [],utility)
        aid=vault_write(wid,raw)
        return put('package',wid,{'audit':a['id'],'scenario':scenario['id'],'artifact':aid,'digest':digest(raw),'manifest':manifest,
                                  'created':time.time(),'workspace_revision':workspace(wid)['revision'],'datasets':scenario['candidates']})

@app.get('/api/w/{wid}/packages/{pid}/download')
def download(wid,pid,s=Depends(session)):
    workspace(wid);p=get(pid,'package',wid);raw=vault_read(wid,p['artifact'])
    return StreamingResponse(io.BytesIO(raw),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="mosaicguard-release-'+pid[:8]+'.zip"','X-Artifact-SHA256':p['digest'],'X-Historical-Scope':str(p['workspace_revision']!=workspace(wid)['revision']).lower()})

class Release(Strict):
    package:str
    audience:str=Field(min_length=3,max_length=300)
    date:str=Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
@app.post('/api/w/{wid}/releases')
def record_release(wid,body:Release,s=Depends(session)):
    with MUTATION:
        editable(wid);p=get(body.package,'package',wid);sc=get(p['scenario'],'scenario',wid)
        from datetime import date
        try:date.fromisoformat(body.date)
        except ValueError:fail('Choose a valid release date.')
        if body.audience!=sc['audience']:fail('Audience must match the reviewed package scope.')
        release=put('release',wid,{**body.model_dump(),'datasets':p['datasets'],'scenario':sc['id'],'created':time.time()});bump(wid)
        return release

@app.post('/api/w/{wid}/comparisons')
def compare_audits(wid,body:dict,s=Depends(session)):
    a=get(body.get('before',''),'audit',wid);b=get(body.get('after',''),'audit',wid)
    sa=get(a['scenario'],'scenario',wid);sb=get(b['scenario'],'scenario',wid)
    # Compare only scopes with matching candidate versions, audience, utility and existing rules.
    compatible=all(sa.get(k)==sb.get(k) for k in ('candidates','audience','purpose','anchors','quasi_identifiers','utility','threshold','max_depth'))
    oldrules={r['id']:r for r in sa['rules']};newrules={r['id']:r for r in sb['rules']}
    compatible &= all(newrules.get(k)==v for k,v in oldrules.items()) and set(sa['available'])<=set(sb['available'])
    if not compatible:fail('Scopes differ beyond added available data/rules. These audits cannot isolate release-addition impact.')
    index=lambda f:(f.get('source'),tuple(f.get('rules',[])))
    old={index(f):f for f in a['findings'] if f['kind']=='linkage'}
    changes=[]
    for f in b['findings']:
        if f['kind']!='linkage':continue
        prev=old.get(index(f));delta=f['single_candidate_rows']-(prev['single_candidate_rows'] if prev else 0)
        if not prev or delta:changes.append({'source':f['source'],'rules':f['rules'],'new_path':prev is None,'single_candidate_record_delta':delta})
    return {'before':a['id'],'after':b['id'],'changes':changes,'coverage_before':a['coverage'],'coverage_after':b['coverage']}

@app.delete('/api/w/{wid}/datasets/{did}')
def delete_dataset(wid,did,s=Depends(session)):
    with MUTATION:
        editable(wid);require_graph();ds=get(did,'dataset',wid)
        if any(did in sc['candidates']+sc['available'] for sc in items('scenario',wid)):raise HTTPException(409,'This version is used by an immutable scenario. Delete its audits/branches and create a new workspace if full removal is needed.')
        for aid in (ds.get('source_artifact'),ds.get('data_artifact')):
            if aid:vault_delete(wid,aid)
        remove(did);bump(wid)
    return {'deleted':True}

@app.delete('/api/w/{wid}/audits/{aid}')
def delete_audit(wid,aid,s=Depends(session)):
    with MUTATION:
        editable(wid);require_graph();get(aid,'audit',wid)
        if any(b['audit']==aid for b in items('branch',wid)):raise HTTPException(409,'Delete the repair branch containing this audit instead.')
        Graph(wid,aid).delete();remove(aid)
        for p in items('package',wid):
            if p['audit']==aid:vault_delete(wid,p['artifact']);remove(p['id'])
        with db() as c:c.execute('DELETE FROM jobs WHERE id=? AND wid=?',(aid,wid))
    return {'deleted':True}

@app.delete('/api/w/{wid}/branches/{bid}')
def delete_branch(wid,bid,s=Depends(session)):
    with MUTATION:
        editable(wid);require_graph();b=get(bid,'branch',wid)
        if any(set(b['derived'])&set(r['datasets']) for r in items('release',wid)):raise HTTPException(409,'A branch recorded as released must remain in history. Delete the entire workspace to remove local history.')
        Graph(wid,b['audit']).delete();remove(b['audit']);remove(b['scenario']);remove(bid)
        for did in b['derived']:
            d=get(did,'dataset',wid);vault_delete(wid,d['data_artifact']);remove(did)
        for p in items('package',wid):
            if p['audit']==b['audit']:vault_delete(wid,p['artifact']);remove(p['id'])
        with db() as c:c.execute('DELETE FROM jobs WHERE id=? AND wid=?',(b['audit'],wid))
    return {'deleted':True}

@app.delete('/api/w/{wid}')
def delete_workspace(wid,s=Depends(session)):
    with MUTATION:
        w=workspace(wid);w['deleting']=True;put('workspace',wid,w,wid)
        with db() as c:c.execute("UPDATE jobs SET cancelled=1 WHERE wid=? AND state IN ('queued','running')",(wid,))
        return {'job':enqueue(wid,'delete_workspace',{},'delete:'+wid)}

# Assistant uses a separate fixed allowlist and never accepts executable query text.
from .assistant import router as assistant_router
app.include_router(assistant_router,dependencies=[Depends(session)])

DIST=Path(__file__).resolve().parents[2]/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}')
    def frontend(path:str):
        if path.startswith('api/'):raise HTTPException(404,'Endpoint not found.')
        return FileResponse(DIST/'index.html')
