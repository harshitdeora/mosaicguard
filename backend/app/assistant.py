"""Bounded, opt-in assistant. Uploaded text never enters model context."""
import json
import os
import threading
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import Field
from .core import items, get, put, encode, digest, workspace
from .ingestion import Strict

router=APIRouter(prefix='/api/w/{wid}/assistant')
MODEL_LOCK=threading.Lock()
SYSTEM='Explain only the supplied scoped aggregates. A candidate match is not proof of identity. Never claim anonymity, compliance or a probability. Use the supplied read-only tools; no data modifications are available. Be concise.'
TASKS={'next_step':'Explain the next review step.','scope':'Explain coverage and limitations.','repairs':'Compare tested repair trade-offs.'}
NAMES=['get_schema_summary','get_sanitised_finding','get_utility_comparison','explain_release_limitations','propose_repair_recipes']
TOOLS=[{'type':'function','name':name,'description':name.replace('_',' '),'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False},'strict':True} for name in NAMES]

def context(wid):
    # Build from a fixed allowlist of numerical/enum fields. Never redact arbitrary row text after the fact.
    ds=items('dataset',wid);audits=items('audit',wid);branches=items('branch',wid)
    return {'datasets':[{'alias':f'dataset_{i+1}','rows':d['rows'],'columns':len(d['columns']),
                         'text_columns':sum(c['type']=='text' for c in d['columns']),'numeric_columns':sum(c['type']=='number' for c in d['columns']),
                         'date_columns':sum(c['type']=='date' for c in d['columns'])} for i,d in enumerate(ds)][:10],
            'latest_audit':({k:audits[-1]['summary'][k] for k in ('candidate_rows','single_candidate_path_records','assessed_path_records','unassessed_path_records','coverage_notes')} if audits else None),
            'branches':[{'alias':f'branch_{i+1}','utility_satisfied':b['utility']['status']=='satisfied','single_candidate_path_records':get(b['audit'],'audit',wid)['summary']['single_candidate_path_records']} for i,b in enumerate(branches)][:10]}

def request_payload(wid,task='scope'):
    return {'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'instructions':SYSTEM,'input':[{'role':'user','content':TASKS[task]+'\n'+encode(context(wid)).decode()}],
            'tools':TOOLS,'max_output_tokens':700,'store':False,'parallel_tool_calls':False}

@router.get('/policy')
def policy(wid):
    workspace(wid);p=request_payload(wid)
    consent=items('model_consent',wid)
    return {'provider':'OpenAI','configured':bool(os.getenv('OPENAI_API_KEY')),'enabled':bool(consent and consent[-1].get('enabled')),
            'initial_request':p,'preview_digest':digest(encode(p)),
            'policy':'Fixed tasks, opaque aliases, schema counts and bounded audit/utility aggregates only. No original names, filenames, cell text, rows, identity examples or arbitrary chat text. Dynamic responses use this same allowlist. Aggregates may still be sensitive.',
            'tool_budget':4,'history':items('model_history',wid)[-10:]}

class Consent(Strict):
    enabled:bool
    preview_digest:str
@router.post('/consent')
def consent(wid,body:Consent):
    p=request_payload(wid)
    if body.enabled and not os.getenv('OPENAI_API_KEY'):raise HTTPException(409,'No server-side model credential configured.')
    if body.enabled and body.preview_digest!=digest(encode(p)):raise HTTPException(409,'Payload preview changed. Review the current request before enabling.')
    return put('model_consent',wid,{'enabled':body.enabled,'preview_digest':body.preview_digest,'model':p['model']},'consent_'+wid)

def tool_result(wid,name):
    c=context(wid)
    if name=='get_schema_summary':return {'datasets':c['datasets']}
    if name=='get_sanitised_finding':return {'latest_audit':c['latest_audit']}
    if name=='get_utility_comparison':return {'branches':c['branches']}
    if name=='explain_release_limitations':return {'scope':'Supplied data and confirmed rules only. No matches does not establish anonymity. Reference coverage can be incomplete.'}
    if name=='propose_repair_recipes':return {'families':['column removal subject to protected constraints','suppression with lost assessment coverage','typed interval generalisation with full re-audit'],'requires_user_selection':True}
    raise ValueError('Unsupported assistant tool.')

def live_adapter(wid,task,client=None):
    if client is None:
        from openai import OpenAI
        client=OpenAI(timeout=20,max_retries=1)
    p=request_payload(wid,task);history=[dict(p)];calls=0
    response=client.responses.create(**p)
    conversation=list(p['input'])
    for turn in range(4):
        function_calls=[x for x in response.output if x.type=='function_call']
        if not function_calls:
            put('model_history',wid,{'requests':history,'tool_calls':calls})
            return {'mode':'live model','answer':response.output_text[:5000],'tool_calls':calls}
        conversation.extend(response.output)
        for call in function_calls:
            calls+=1
            if calls>4 or call.name not in NAMES or json.loads(call.arguments)!={}:raise ValueError('Model exceeded its allowed tool contract.')
            value=tool_result(wid,call.name)
            conversation.append({'type':'function_call_output','call_id':call.call_id,'output':encode(value).decode()})
        p={**p,'input':conversation,'tool_choice':'none' if calls>=4 else 'auto'}
        # Stored history includes exact sanitized tool outputs and outbound requests, excluding SDK objects.
        history.append(json.loads(json.dumps(p,default=lambda x:x.model_dump())))
        response=client.responses.create(**p)
    raise ValueError('Assistant turn budget reached.')

class Ask(Strict):
    task:Literal['next_step','scope','repairs']='scope'
    external:bool=False

@router.post('')
def ask(wid,body:Ask):
    workspace(wid)
    if body.external:
        c=items('model_consent',wid)
        if not c or not c[-1]['enabled'] or c[-1]['model']!=os.getenv('OPENAI_MODEL','gpt-4.1-mini'):raise HTTPException(403,'Review and enable the current provider/model payload policy first.')
        if not MODEL_LOCK.acquire(blocking=False):raise HTTPException(429,'A model request is already running. Try again after it completes.')
        try:return live_adapter(wid,body.task)
        except Exception:raise HTTPException(502,'Model request failed or exceeded its tool budget. Core review tools remain available.') from None
        finally:MODEL_LOCK.release()
    c=context(wid)
    if body.task=='next_step':
        answer='Import your candidate CSV and supplied reference files, then confirm their types, subject units and column meanings.' if not c['datasets'] else 'Define a release scenario: choose the candidate, audience, available references, confirmed mappings and analytical requirements. Then run an audit.' if c['latest_audit'] is None else 'Inspect the assumptions and coverage behind each finding, compare at least two repairs, then review a package tied to the exact audit revision.'
    elif body.task=='repairs':answer='Compare candidate counts, assessed and unassessed denominators, analytical drift and retained rows independently. Suppression can remove assessment coverage. A generalised date or number must match compatible reference values. An alternative path or historical release may preserve exposure.'
    else:answer='Findings cover only supplied versions, approved rules and stated bounds. One candidate under those assumptions is not proof of identity. No match found is not a guarantee of anonymity. Reference records are not distinct people unless a defensible entity key is confirmed.'
    return {'mode':'built-in rules-based guidance','answer':answer,'context':c}
