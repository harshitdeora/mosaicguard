import copy
import json
import shutil
import threading
import time
from fastapi import HTTPException
from .core import *
from .graph import Graph
from .analysis import audit, load_dataset
from .ingestion import parse_csv, ParseConfig, profile
from .repairs import transform, compare_utility

STOP=threading.Event()
THREAD=None

def publish(jid,wid,objects,result,delete_ids=()):
    """One metadata transaction exposes completed snapshots and their job result together."""
    with db() as c:
        job=c.execute('SELECT cancelled FROM jobs WHERE id=?',(jid,)).fetchone()
        if not job or job['cancelled']:raise Cancelled()
        for kind,body,oid in objects:
            value={**body,'id':oid}
            c.execute('INSERT INTO objects VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                      (oid,kind,wid,seal(value),time.time()))
        for oid in delete_ids:c.execute('DELETE FROM objects WHERE id=? AND wid=?',(oid,wid))
        c.execute("UPDATE jobs SET state='complete',stage='Complete',result=? WHERE id=?",(seal(result),jid))
    return result

def cleanup_job(wid,jid):
    # Every job owns its projection and staging versions. A failed job cannot replace a successful result.
    try: Graph(wid,jid).delete()
    except Exception: pass  # Reconciled before retry; deletion jobs retain their tombstone until graph is online.
    for a in items('audit',wid):
        if a['id']==jid:remove(a['id'])
    for b in items('branch',wid):
        if b.get('job')==jid:remove(b['scenario']);remove(b['id'])
    for ds in items('dataset',wid):
        if ds.get('staging_job')==jid:
            for aid in (ds.get('data_artifact'),):
                if aid: vault_delete(wid,aid)
            remove(ds['id'])

def process(j):
    wid=j['wid'];jid=j['id'];p=unseal(j['payload'])
    if j['kind']=='delete_workspace':
        checkpoint(jid,'Deleting graph projections and encrypted artifacts')
        for a in items('audit',wid): Graph(wid,a['id']).delete()
        with db() as c: ids=c.execute('SELECT id FROM jobs WHERE wid=? AND id!=?',(wid,jid)).fetchall()
        for r in ids: Graph(wid,r['id']).delete()
        folder=DATA/'vault'/wid
        if folder.exists(): shutil.rmtree(folder)
        with db() as c:
            c.execute('DELETE FROM objects WHERE wid=?',(wid,))
            c.execute('DELETE FROM jobs WHERE wid=? AND id!=?',(wid,jid))
        return {'deleted':True}
    workspace(wid)
    if j['kind']=='import':
        checkpoint(jid,'Parsing all logical records')
        draft=get(p['draft'],'upload',wid)
        data=parse_csv(vault_read(wid,draft['source_artifact']),ParseConfig(**p['config']['parse']),draft['preview']['columns'])
        data['columns']=p['config']['columns'];data['parse']=p['config']['parse'];data['source_digest']=draft['digest']
        if sum(d['rows'] for d in items('dataset',wid))+len(data['rows'])>5000: raise ValueError('Workspace limit is 5,000 records.')
        checkpoint(jid,'Committing immutable dataset version')
        artifact=vault_write(wid,encode(data))
        dataset=put('dataset',wid,{'name':draft['name'],'status':'staging','role':p['config']['role'],'row_unit':p['config']['row_unit'],
                                 'columns':data['columns'],'rows':len(data['rows']),'excluded':data['excluded'],'warnings':data['warnings'],
                                 'data_artifact':artifact,'source_artifact':draft['source_artifact'],'source_digest':draft['digest'],'parse':data['parse'],
                                 'staging_job':jid},jid)
        checkpoint(jid,'Publishing the completed import')
        dataset.pop('staging_job');dataset['status']='ready';w=workspace(wid);w['revision']+=1
        return publish(jid,wid,[('dataset',dataset,jid),('workspace',w,wid)],{'dataset':jid},[draft['id']])
    if j['kind']=='audit':
        s=get(p['scenario'],'scenario',wid)
        if workspace(wid)['revision']!=s['workspace_revision']: raise ValueError('Scenario is stale. Save a new scenario snapshot before auditing.')
        result=audit(wid,s,jid,jid)
        checkpoint(jid,'Publishing the complete audit snapshot')
        return publish(jid,wid,[('audit',result,jid)],{'audit':jid})
    if j['kind']=='repair':
        base=get(p['scenario'],'scenario',wid)
        if workspace(wid)['revision']!=base['workspace_revision']: raise ValueError('Scenario is stale. Save a fresh scenario first.')
        original={d:load_dataset(wid,d) for d in dict.fromkeys(base['candidates']+base['available'])}
        changed=copy.deepcopy(original);notes=[];mapping={}
        for did in base['candidates']:
            recipe=[r for r in p['recipe'] if r['dataset']==did]
            if not recipe: continue
            changed[did],n=transform(original[did],recipe,base['protected']);notes.extend(n)
            derived=uid();mapping[did]=derived
            ds=get(did,'dataset',wid)
            put('dataset',wid,{**ds,'id':derived,'status':'staging','name':ds['name']+' · '+p['name'],'role':'candidate','data_artifact':vault_write(wid,encode(changed[did])),
                               'source_artifact':None,'columns':changed[did]['columns'],'parent':did,'staging_job':jid},derived)
        s=copy.deepcopy(base);s['id']=uid();s['name']=p['name'];s['candidates']=[mapping.get(d,d) for d in base['candidates']]
        def remap(d): return mapping.get(d,d)
        # Preserve historical versions in available. Only current candidate bindings are remapped.
        originals=copy.deepcopy(s['rules'])
        for r in s['rules']:
            r['source']=remap(r['source']);r['target']=remap(r['target'])
        for r in originals:
            if r['source'] in base.get('historical',[]) and r not in s['rules']:
                r['id']=uid();s['rules'].append(r)
        for q in s['quasi_identifiers']: q['dataset']=remap(q['dataset'])
        for a in s['anchors']: a['dataset']=remap(a['dataset'])
        for b in s.get('bundles',[]): b['source']=remap(b['source'])
        for d in mapping:
            if d not in base.get('historical',[]): s['available']=[x for x in s['available'] if x!=d]
            elif d not in s['available']: s['available'].append(d)
        measurement=compare_utility(original,changed,base)
        result=audit(wid,s,jid,jid,overrides={new:changed[old] for old,new in mapping.items()})
        checkpoint(jid,'Saving repair, audit and utility comparisons')
        branch={'id':uid(),'name':p['name'],'base_scenario':base['id'],'scenario':s['id'],'audit':jid,'recipe':p['recipe'],
                'utility':measurement,'notes':notes,'derived':list(mapping.values()),'created':time.time(),'job':jid}
        objects=[('scenario',s,s['id']),('audit',result,jid),('branch',branch,branch['id'])]
        for derived in mapping.values():
            ds=get(derived,'dataset',wid);ds.pop('staging_job',None);ds['status']='ready';objects.append(('dataset',ds,derived))
        return publish(jid,wid,objects,{'branch':branch['id'],'audit':jid})
    raise ValueError('Unsupported job kind.')

def worker():
    while not STOP.is_set():
        with db() as c:
            j=c.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if j: c.execute("UPDATE jobs SET state='running',stage='Starting' WHERE id=?",(j['id'],))
        if not j: STOP.wait(.25);continue
        try:
            checkpoint(j['id'],'Starting')
            if j['kind']!='delete_workspace':cleanup_job(j['wid'],j['id'])
            result=process(j)
            with db() as c: c.execute("UPDATE jobs SET state='complete',stage='Complete',result=? WHERE id=?",(seal(result),j['id']))
        except Cancelled:
            cleanup_job(j['wid'],j['id'])
            with db() as c: c.execute("UPDATE jobs SET state='cancelled',stage='Cancelled' WHERE id=?",(j['id'],))
        except Exception as e:
            cleanup_job(j['wid'],j['id'])
            # Never log exception text: CSV values / graph parameters can be embedded by dependencies.
            if isinstance(e,ValueError): error=str(e)
            elif isinstance(e,HTTPException): error='A required workspace item is unavailable. Review the scenario and retry.'
            else: error='Operation failed ('+type(e).__name__+'). Check graph health, supported limits and administrator diagnostics; no partial result was published.'
            with db() as c: c.execute("UPDATE jobs SET state='failed',stage='Failed',error=? WHERE id=?",(error,j['id']))

def start():
    global THREAD
    with db() as c:
        c.execute("UPDATE jobs SET state='interrupted',stage='Interrupted by restart; review and retry',error='Worker restarted. No partial job is treated as complete.' WHERE state='running'")
    STOP.clear();THREAD=threading.Thread(target=worker,daemon=True);THREAD.start()

def stop():
    STOP.set()
    if THREAD: THREAD.join(timeout=15)
