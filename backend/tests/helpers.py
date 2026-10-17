import time

def ok(r,code=200):
    assert r.status_code==code,r.text
    return r.json()

def workspace(c,name='Fictional review'):return ok(c.post('/api/workspaces',json={'name':name}))['id']

def wait(c,wid,jid):
    for _ in range(600):
        j=ok(c.get(f'/api/w/{wid}/jobs/{jid}'))
        if j['state'] in ('complete','failed','cancelled','interrupted'):return j
        time.sleep(.05)
    raise AssertionError('Job timeout')

def imported(c,wid,csv,role='candidate',types=None,unit='person',parse=None):
    u=ok(c.post(f'/api/w/{wid}/uploads',files={'file':('unfamiliar.csv',csv.encode() if isinstance(csv,str) else csv,'text/csv')}))
    p=parse or {'encoding':'utf-8-sig','delimiter':',','quotechar':'"','header':True,'null_tokens':[],'skip_bad_rows':False}
    preview=ok(c.post(f'/api/w/{wid}/uploads/{u["id"]}/preview',json=p))
    cols=[{k:v for k,v in col.items() if k in ('id','name','type','date_format','meaning','identifier','sensitive')} for col in preview['columns']]
    for col in cols:
        col['type']=(types or {}).get(col['name'],'text')
        if col['type']=='date':col['date_format']='%Y-%m-%d'
    j=ok(c.post(f'/api/w/{wid}/uploads/{u["id"]}/confirm',json={'parse':p,'columns':cols,'role':role,'row_unit':unit}))
    result=wait(c,wid,j['job']);assert result['state']=='complete',result
    state=ok(c.get(f'/api/w/{wid}/state'));return next(d for d in state['datasets'] if d['id']==j['job'])

def col(ds,name):return next(c['id'] for c in ds['columns'] if c['name']==name)

def rule(a,b,ac,bc,**kw):
    import uuid
    return {'id':uuid.uuid4().hex,'source':a['id'],'target':b['id'],'source_columns':[col(a,x) for x in ac],
            'target_columns':[col(b,x) for x in bc],'meaning':'Reviewed fictional subject attributes','subject':'person','context':'Same fictional cohort and period',
            'predicate':'compatible','trim':False,'casefold':False,'unicode_nfc':False,'confirmed':True,'revision':1,**kw}

def scenario(c,wid,candidates,available,rules,**kw):
    body={'name':'Test scenario','audience':'Test research audience','purpose':'Synthetic correctness evaluation','candidates':[d['id'] for d in candidates],
          'available':[d['id'] for d in available],'rules':rules,'anchors':[],'quasi_identifiers':[],'utility':[],'protected':[],
          'min_retention':1,'threshold':5,'max_depth':3,'reference_coverage':'Fictional fixture; known coverage','bundles':[],**kw}
    return ok(c.post(f'/api/w/{wid}/scenarios',json=body))

def audited(c,wid,sid):
    j=ok(c.post(f'/api/w/{wid}/audits',json={'scenario':sid}));r=wait(c,wid,j['job']);assert r['state']=='complete',r
    return next(a for a in ok(c.get(f'/api/w/{wid}/state'))['audits'] if a['id']==j['job'])

def repaired(c,wid,sid,recipe,name='Test branch'):
    j=ok(c.post(f'/api/w/{wid}/repairs',json={'scenario':sid,'recipe':recipe,'name':name}));r=wait(c,wid,j['job']);assert r['state']=='complete',r
    st=ok(c.get(f'/api/w/{wid}/state'));return next(b for b in st['branches'] if b['id']==r['result']['branch']),next(a for a in st['audits'] if a['id']==j['job'])
