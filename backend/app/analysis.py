import copy
import json
import time
from collections import Counter, defaultdict
from .core import get, items, vault_read, token, uid, checkpoint, encode, put, digest
from .graph import Graph, healthy
from .matching import bindings, canonical, rule_paths

def load_dataset(wid,did):
    ds=get(did,'dataset',wid)
    if ds['status']!='ready': raise ValueError('Dataset version is not ready.')
    return json.loads(vault_read(wid,ds['data_artifact']))

def anchor_entities(wid,did,data,scenario):
    anchor=next((a for a in scenario['anchors'] if a['dataset']==did),None)
    cols={c['id']:i for i,c in enumerate(data['columns'])}
    if anchor and all(c in cols for c in anchor['columns']):
        keys=[[row[cols[c]] for c in anchor['columns']] for row in data['rows']]
        if all(all(v is not None for v in k) for k in keys):
            return [token(wid,'anchor:'+did,k) for k in keys],'distinct '+get(did,'dataset',wid)['row_unit']+' entities under the confirmed key'
    return [token(wid,'record:'+did,[i]) for i in range(len(data['rows']))],'reference records'

def audit(wid,scenario,aid,jid,overrides=None):
    started=time.monotonic(); g=Graph(wid,aid)
    # Recovery removes any partially built namespace before retrying this job.
    g.delete();g.initialize()
    ids=list(dict.fromkeys(scenario['candidates']+scenario['available']))
    data={d:(overrides[d] if overrides and d in overrides else load_dataset(wid,d)) for d in ids}
    entities={};units={};coverage=[];rule_profiles={};findings=[];path_sets={}
    checkpoint(jid,'Building the scoped graph projection')
    for did in ids:
        ents,unit=anchor_entities(wid,did,data[did],scenario);entities[did]=ents;units[did]=unit
        g.records(did,[{'idx':i,'entity':v} for i,v in enumerate(ents)])
        ds=get(did,'dataset',wid)
        if ds.get('excluded'): coverage.append({'dataset':did,'reason':'Explicitly excluded malformed records','count':ds['excluded']})
    for rule in scenario['rules']:
        if not rule['confirmed']:
            coverage.append({'rule':rule['id'],'reason':'Mapping is unconfirmed and was excluded.'});continue
        checkpoint(jid,'Profiling approved rule '+rule['id'][:8])
        if rule['source'] not in data or rule['target'] not in data: continue
        left,right,stats=bindings(wid,rule,data[rule['source']],data[rule['target']])
        rule_profiles[rule['id']]=stats
        if stats.get('partial') or stats.get('blocked') or stats['missing']:
            coverage.append({'rule':rule['id'],**stats})
        if not stats.get('partial') and not stats.get('blocked'):
            g.bind(rule['source'],rule['id'],left,'out');g.bind(rule['target'],rule['id'],right,'in')
    paths,truncated=rule_paths(scenario)
    if truncated: coverage.append({'reason':'100 path search ceiling reached; unenumerated paths are unassessed.'})
    for n,path in enumerate(paths):
        checkpoint(jid,f'Investigating path {n+1} of {len(paths)}')
        source=path[0]['source'];target=path[-1]['target'];count=len(data[source]['rows']);chain=[r['id'] for r in path]
        first=path[0];indices={c['id']:i for i,c in enumerate(data[source]['columns'])}
        partial=any(rule_profiles.get(r['id'],{}).get('partial') for r in path) or time.monotonic()-started>120
        blocked=any(rule_profiles.get(r['id'],{}).get('blocked') for r in path)
        assessed=set()
        if not partial and not blocked and all(c in indices for c in first['source_columns']):
            assessed={i for i,row in enumerate(data[source]['rows']) if all(canonical(row[indices[c]],data[source]['columns'][indices[c]],first) is not None for c in first['source_columns'])}
        candidates=defaultdict(set);endpoints=defaultdict(list)
        if assessed:
            try:results=g.candidates(path,source,target)
            except Exception as e:
                if ('timeout' in str(e).lower() or 'timed out' in str(e).lower()) and healthy():
                    partial=True;assessed=set();results=[]
                    coverage.append({'path':chain,'reason':'Graph query timeout; this entire path is unassessed.'})
                else:raise
            if len(results)>20000:
                partial=True;assessed=set();coverage.append({'path':chain,'reason':'20,000 endpoint result ceiling reached.'})
            else:
                for idx,entity,endpoint in results:
                    candidates[idx].add(entity)
                    if len(endpoints[idx])<3: endpoints[idx].append(endpoint)
        if partial: coverage.append({'path':chain,'reason':'Path enumeration incomplete; no uniqueness claims made.'})
        path_sets[(source,tuple(chain))]={'sets':dict(candidates),'assessed':assessed,'target':target,'partial':partial}
        records=[{'record':i+1,'candidate_count':len(candidates[i]),'label':('One candidate under these assumptions' if len(candidates[i])==1 else 'Ambiguous linkage' if candidates[i] else 'No match found'),
                  'endpoint_records':[x+1 for x in endpoints[i]]} for i in sorted(assessed)]
        finding={'id':uid(),'kind':'linkage','source':source,'target':target,'rules':chain,'unit':units[target],'historical':source in scenario.get('historical',[]) and source not in scenario['candidates'],
                 'imported_rows':count,'assessed_rows':len(assessed),'unassessed_rows':count-len(assessed),'blocked_rows':count if blocked else 0,
                 'single_candidate_rows':sum(r['candidate_count']==1 for r in records),
                 'small_candidate_rows':sum(0<r['candidate_count']<scenario['threshold'] for r in records),
                 'no_match_rows':sum(r['candidate_count']==0 for r in records),'records':records,
                 'status':'partial' if partial else 'predicate blocked by reviewed column removal' if blocked else 'complete within scope',
                 'explanation':'Distinct endpoint candidates are unioned across intermediate matches for this rule chain. A single candidate is not proof of identity. Missing components are unassessed.'}
        finding['severity']='incomplete' if partial else 'high' if finding['single_candidate_rows'] else 'review' if finding['small_candidate_rows'] else 'scope'
        g.finding(finding['id'],encode({k:v for k,v in finding.items() if k!='records'}).decode(),chain)
        findings.append(finding)
    for bundle in scenario.get('bundles',[]):
        if not bundle['confirmed']: continue
        members=[path_sets.get((bundle['source'],tuple(p))) for p in bundle['paths']]
        if any(m is None or m['partial'] for m in members):
            coverage.append({'reason':'Knowledge bundle incomplete: one or more full paths unavailable.'});continue
        eligible=set.intersection(*(m['assessed'] for m in members))
        records=[]
        for i in sorted(eligible):
            sets=[m['sets'].get(i,set()) for m in members]
            intersection=set.intersection(*sets)
            records.append({'record':i+1,'candidate_count':len(intersection),'contradictory':all(sets) and not intersection})
        findings.append({'id':uid(),'kind':'knowledge_bundle','source':bundle['source'],'rules':bundle['paths'],
                         'assessed_rows':len(eligible),'single_candidate_rows':sum(r['candidate_count']==1 for r in records),
                         'contradictions':sum(bool(r['contradictory']) for r in records),'records':records,'unit':units[members[0]['target']],
                         'explanation':bundle['same_subject_context'],'severity':'review'})
    for did in scenario['candidates']:
        d=data[did]
        identifiers=[c['id'] for c in d['columns'] if c.get('identifier')]
        if identifiers: findings.append({'id':uid(),'kind':'direct_identifiers','source':did,'columns':identifiers,'affected_rows':len(d['rows']),'severity':'high','explanation':'User-marked identifier columns remain in the candidate.'})
        for qi in [q for q in scenario['quasi_identifiers'] if q['dataset']==did]:
            index={c['id']:i for i,c in enumerate(d['columns'])}
            if any(c not in index for c in qi['columns']):
                coverage.append({'dataset':did,'reason':'Quasi-identifier diagnostic blocked by column removal.'});continue
            keys=[tuple(row[index[c]] for c in qi['columns']) for row in d['rows']]
            counts=Counter(k for k in keys if None not in k)
            histogram=Counter(counts[k] for k in keys if None not in k)
            homogeneity=[]
            for c in [c for c in d['columns'] if c.get('sensitive')]:
                values=defaultdict(set)
                for row,k in zip(d['rows'],keys):
                    if None not in k and row[index[c['id']]] is not None: values[k].add(row[index[c['id']]])
                homogeneity.append({'column':c['id'],'single_value_classes':sum(len(v)==1 for v in values.values()),'assessed_classes':len(values)})
            findings.append({'id':uid(),'kind':'within_file','source':did,'columns':qi['columns'],'record_class_histogram':dict(histogram),
                             'assessed_rows':sum(histogram.values()),'unassessed_rows':sum(None in k for k in keys),'single_record_rows':histogram.get(1,0),
                             'unit':'records within this file','homogeneity':homogeneity,'severity':'review','explanation':'Equivalence-class sizes count records, independently of reference linkage. Small classes are review diagnostics.'})
    if not paths: coverage.append({'reason':'No eligible confirmed linkage path. Multi-file linkage is unassessed.'})
    # Missing release history persists even after local dataset deletion.
    present={d['id'] for d in items('dataset',wid)}
    for r in items('release',wid):
        if r['audience']==scenario['audience']:
            for did in r['datasets']:
                if did not in present: coverage.append({'reason':'Missing historical release data; past exposure cannot be reassessed.','dataset':did})
    summary={'candidate_rows':sum(len(data[d]['rows']) for d in scenario['candidates']),
             'single_candidate_path_records':sum(f.get('single_candidate_rows',0) for f in findings if f['kind']=='linkage' and not f.get('historical')),
             'historical_single_candidate_path_records':sum(f.get('single_candidate_rows',0) for f in findings if f['kind']=='linkage' and f.get('historical')),
             'single_candidate_denominator':'Sum of assessed source record/path pairs; records may occur on multiple paths.',
             'assessed_path_records':sum(f.get('assessed_rows',0) for f in findings if f['kind']=='linkage'),
             'unassessed_path_records':sum(f.get('unassessed_rows',0) for f in findings if f['kind']=='linkage'),
             'direct_identifier_columns':sum(len(f.get('columns',[])) for f in findings if f['kind']=='direct_identifiers'),
             'coverage_notes':len(coverage)}
    result={'id':aid,'scenario':scenario['id'],'workspace_revision':scenario['workspace_revision'],'scenario_digest':digest(encode(scenario)),
            'dataset_digests':{did:digest(encode(d)) for did,d in data.items()},
            'status':'partial' if truncated or not paths or any(c.get('partial') or 'incomplete' in c.get('reason','').lower() or 'unconfirmed' in c.get('reason','') or 'Missing historical' in c.get('reason','') for c in coverage) else 'complete within scope',
            'summary':summary,'findings':findings,'coverage':coverage,'rule_profiles':rule_profiles,'elapsed_seconds':round(time.monotonic()-started,3),
            'assumptions':{'audience':scenario['audience'],'purpose':scenario['purpose'],'reference_coverage':scenario['reference_coverage'],'max_depth':scenario['max_depth'],'threshold':scenario['threshold']},
            'limitations':['No findings means no findings detected within this scope; it does not establish anonymity.','Reference datasets may be incomplete. Candidate cardinalities are not re-identification probabilities.','Paths are evaluated separately unless explicitly bundled.','No fuzzy, external identity or unsupported timestamp interval matching.']}
    checkpoint(jid,'Saving validated audit results')
    return result
