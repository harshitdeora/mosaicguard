"""Measured real-FalkorDB five-file envelope; isolated metadata, synthetic CSVs only."""
import json,os,sys,time,tracemalloc,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from dotenv import load_dotenv
load_dotenv(root/'.env')
os.environ['MOSAIC_DATA']=str(root/'work'/('benchmark-'+uuid.uuid4().hex))
from fastapi.testclient import TestClient
from backend.app.main import app
from fixtures.generate import kit
from backend.app.graph import Graph
from backend.tests.helpers import *
tracemalloc.start();started=time.perf_counter()
with TestClient(app,raise_server_exceptions=False) as c:
    auth=ok(c.post('/api/auth/setup',json={'username':'benchmark-owner','password':'Synthetic-benchmark-password-42'}));c.headers['x-csrf-token']=auth['csrf']
    w=workspace(c,'Five-file benchmark');datasets=[];sizes=[]
    for file in kit(1000):
        sizes.append(len(file['csv'].encode()));datasets.append(imported(c,w,file['csv'],file['role'],file['types']))
    f,attendance,directory,badges,calendar=datasets
    rules=[rule(f,attendance,['session'],['session']),rule(attendance,directory,['participant_key'],['participant_key']),
           rule(f,badges,['badge'],['badge']),rule(badges,directory,['participant_key'],['participant_key']),
           rule(f,calendar,['survey_day'],['survey_day']),rule(calendar,directory,['participant_key'],['participant_key'])]
    sc=scenario(c,w,[f],datasets[1:],rules,anchors=[{'dataset':directory['id'],'columns':[col(directory,'participant_key')],'justification':'Fictional generator uses a unique stable participant key.'}])
    a=audited(c,w,sc['id'])
    evaluation=[]
    for label,path in [('attendance',[rules[0],rules[1]]),('badge',[rules[2],rules[3]]),('calendar',[rules[4],rules[5]])]:
        results=Graph(w,a['id']).candidates(path,f['id'],directory['id'])
        pairs={(source,endpoint) for source,entity,endpoint in results}
        true=sum(source==endpoint for source,endpoint in pairs)
        evaluation.append({'path':label,'true_candidate_pairs':true,'candidate_pairs':len(pairs),'fixture_precision':true/len(pairs) if pairs else None,'fixture_recall':true/1000,
                           'interpretation':'Known fictional generator truth only; not real-world re-identification accuracy.'})
    peak=tracemalloc.get_traced_memory()[1]
    output={'files':5,'rows_per_file':1000,'workspace_rows':5000,'file_bytes':sizes,'max_depth':3,'rule_count':6,'query_timeout_ms':8000,
            'max_path_endpoint_results':20000,'max_paths':100,'audit_seconds':a['elapsed_seconds'],'import_and_audit_seconds':round(time.perf_counter()-started,3),
            'peak_traced_python_bytes':peak,'memory_scope':'Python tracemalloc only; excludes native allocations and FalkorDB process.','status':a['status'],'summary':a['summary'],
            'runtime':sys.version.split()[0],'graph':'real FalkorDB Docker image pinned in compose.yaml','synthetic_evaluation':evaluation}
    # Verify cleanup too; keep measured data out of the user installation.
    j=ok(c.delete(f'/api/w/{w}'))
    for _ in range(600):
        if c.get(f'/api/w/{w}/state').status_code==404:break
        time.sleep(.05)
(root/'docs').mkdir(exist_ok=True);(root/'docs'/'benchmark.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
