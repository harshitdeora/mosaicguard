import csv
import io
import json
import os
import zipfile
from .core import encode, digest
from .ingestion import csv_bytes

def sanitized_audit(audit):
    a={k:v for k,v in audit.items() if k!='findings'}
    a['findings']=[{k:v for k,v in f.items() if k!='records'} for f in audit['findings']]
    return a

def package(data,scenario,audit,recipe,utility):
    files={};transport={};schema={}
    for n,did in enumerate(scenario['candidates']):
        d=data[did];name=f'candidate-{n+1}.csv';raw=csv_bytes(d['columns'],d['rows'])
        parsed=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline='')))
        semantic=[[c['name'] for c in d['columns']]]+[['' if v is None else str(v) for v in r] for r in d['rows']]
        escaped=[]
        for i,row in enumerate(parsed):
            for j,value in enumerate(row):
                if value!=semantic[i][j]:
                    if value!="'"+semantic[i][j]: raise ValueError('Export transport verification failed.')
                    escaped.append([i,j]);parsed[i][j]=value[1:]
        if parsed!=semantic: raise ValueError('Export semantic contents differ from audited branch.')
        files[name]=raw;transport[name]={'prefix_apostrophe_cells':escaped,'semantic_sha256':digest(encode(semantic))}
        schema[name]={'columns':d['columns'],'source_parse':d.get('parse'),'source_sha256':d.get('source_digest'),'audited_data_sha256':audit['dataset_digests'][did],'export_encoding':'utf-8-sig','delimiter':',','quotechar':'"','null_representation':''}
    safe=sanitized_audit(audit)
    safe_utility={**utility,'metrics':[{**m,'groups':[{**g,'group':f'Group {n+1}'} for n,g in enumerate(m['groups'])]} for m in utility.get('metrics',[])]}
    files['audit.json']=encode(safe);files['recipe.json']=encode({'transformations':recipe,'source_digests':{did:d.get('source_digest') for did,d in data.items()}});files['schema.json']=encode(schema);files['utility.json']=encode(safe_utility)
    files['scenario.json']=encode(scenario)
    report=('MosaicGuard release review\n\nStatus: '+audit['status']+'\n\n'+
            json.dumps(audit['summary'],indent=2)+'\n\nCoverage\n'+json.dumps(audit['coverage'],indent=2)+
            '\n\nLimitations\n'+'\n'.join(audit['limitations'])+
            '\n\nFormula-like cells have a reversible apostrophe prefix for spreadsheet transport. This is not a privacy transformation.\n'+
            'Candidate files were reopened and their semantic contents compared with the audited branch.\n'+
            'This package excludes confidential row examples and private lineage. Downloading does not record or publish a release.\n')
    files['review-report.txt']=report.encode()
    manifest={'format':'mosaicguard-package-v1','software':'MosaicGuard 0.1.0','scenario_id':scenario['id'],'audit_id':audit['id'],
              'source_revision':os.getenv('MOSAIC_BUILD_COMMIT','development / untagged'),
              'scenario_digest':digest(encode(scenario)),'normalization_version':'canonical-v1','transport':transport,
              'files':{name:digest(value) for name,value in files.items()}}
    files['manifest.json']=encode(manifest)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,value)
    return stream.getvalue(),manifest
