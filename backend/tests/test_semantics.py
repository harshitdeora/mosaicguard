import copy
import csv
import io
import json
import zipfile
from collections import defaultdict
import pytest
from fastapi import HTTPException
from backend.app.ingestion import parse_csv, ParseConfig, csv_bytes, validate_columns, Column
from backend.app.matching import bindings, interval, overlap, canonical
from backend.app.repairs import transform, compare_utility, utility_result
from backend.app.exports import package

def data(headers,rows,types=None):return {'columns':[{'id':x,'name':x,'type':(types or {}).get(x,'text'),'date_format':'%Y-%m-%d'} for x in headers],'rows':rows}

@pytest.mark.parametrize('raw,cfg,count',[(b'id,n\r\n001,"two\nlines"\r\n',{},1),(b'\xef\xbb\xbfid;n\r\n001;"a;b"\r\n',{'delimiter':';'},1),(b'id\ttext\r\n001\tNA\r\n',{'delimiter':'\t'},1),('id,n\n001,café'.encode('cp1252'),{'encoding':'cp1252'},1)])
def test_csv_logical_records(raw,cfg,count):
    d=parse_csv(raw,ParseConfig(**cfg));assert len(d['rows'])==count;assert d['rows'][0][0]=='001'
    reopened=list(csv.reader(io.StringIO(csv_bytes(d['columns'],d['rows']).decode('utf-8-sig'))));assert reopened[1][0]=='001'

@pytest.mark.parametrize('raw',[b'',b'a,b\n',b'a,a\n1,2',b',b\n1,2',b'a,b\n1,2,3',b'a,b\n"broken,2',b'abc\x00def',b'a\n'+b'x'*8193])
def test_invalid_csv(raw):
    with pytest.raises(HTTPException):parse_csv(raw,ParseConfig())

def test_null_and_skipped_rows():
    d=parse_csv(b'id,n\n001,NA\n002,NULL\n003\n004,\n',ParseConfig(null_tokens=['NULL'],skip_bad_rows=True))
    assert d['excluded']==1 and d['rows']==[['001','NA'],['002',None],['004',None]]

def test_ambiguous_dates_need_format():
    d=parse_csv(b'day\n03/04/2026\n',ParseConfig());c=Column(**{**d['columns'][0],'type':'date'})
    with pytest.raises(HTTPException):validate_columns(d,[c])

def test_composite_and_missing():
    a=data(['x','y'],[['A','1'],['A','2'],[None,'1']]);b=data(['x','y'],[['A','1'],['A','3'],[None,'1']])
    r={'id':'test','source_columns':['x','y'],'target_columns':['x','y'],'predicate':'exact'}
    left,right,stats=bindings('w',r,a,b)
    actual={(x['idx'],y['idx']) for x in left for y in right if x['token']==y['token']}
    # Independent relational conjunction oracle, without using canonical(), HMAC or graph code.
    expected={(i,j) for i,ra in enumerate(a['rows']) for j,rb in enumerate(b['rows']) if all(v is not None for v in ra+rb) and ra==rb}
    assert actual==expected=={(0,0)} and stats['missing']==1

@pytest.mark.parametrize('kind,value,inside,outside',[('date_quarter','2026-05-12','2026-06-30','2026-07-01'),('date_month','2026-02-15','2026-02-28','2026-03-01'),('date_year','2026-05-12','2026-01-01','2027-01-01')])
def test_generalised_dates_widen(kind,value,inside,outside):
    d=data(['day'],[[value]],{'day':'date'});out,_=transform(d,[{'column':'day','kind':kind}],[])
    generalized=interval(out['rows'][0][0],out['columns'][0]);exact=lambda x:interval(x,d['columns'][0])
    assert overlap(generalized,exact(inside));assert not overlap(generalized,exact(outside));assert d['rows']==[[value]]

def test_numeric_negative_boundary():
    d=data(['n'],[['-1'],['0'],['9.999'],['10']],{'n':'number'});o,_=transform(d,[{'column':'n','kind':'numeric_bucket','width':10}],[])
    assert [r[0] for r in o['rows']]==['-10..0','0..10','0..10','10..20']
    assert not overlap(interval('0..10',o['columns'][0]),interval('10',d['columns'][0]))

def test_generalisation_does_not_compare_hmac_order():
    a=data(['n'],[['12']],{'n':'number'});a,_=transform(a,[{'column':'n','kind':'numeric_bucket','width':10}],[])
    b=data(['n'],[['11'],['19'],['20']],{'n':'number'})
    r={'id':'typed','source_columns':['n'],'target_columns':['n'],'predicate':'compatible'}
    left,right,stats=bindings('w',r,a,b)
    assert {y['idx'] for x in left for y in right if x['token']==y['token']}=={0,1}
    r['predicate']='exact';assert bindings('w',r,a,b)[2]['partial']

def test_undefined_metrics_and_protected_fields():
    d=data(['group','n'],[['a','1']],{'n':'number'})
    with pytest.raises(ValueError):transform(d,[{'column':'n','kind':'drop'}],['n'])
    o,_=transform(d,[{'column':'n','kind':'drop'}],[])
    result=compare_utility({'d':d},{'d':o},{'candidates':['d'],'min_retention':1,'utility':[{'dataset':'d','group':'group','value':'n','operation':'mean','max_relative_drift':.1}]})
    assert result['status']=='violated' and result['metrics'][0]['unavailable_reason'] and not result['metrics'][0]['groups']

def test_formula_transport_is_reversible():
    d=data(['id'],[['001'],['=SUM(A1)'],['-5'],["'literal"],[' @formula']])
    raw=csv_bytes(d['columns'],d['rows']);rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    assert rows[1][0]=='001';assert rows[2][0]=="'=SUM(A1)";assert rows[3][0]=="'-5";assert rows[4][0]=="''literal"

def test_low_selectivity_bound():
    a=data(['x'],[['same']]*150);b=data(['x'],[['same']]*150)
    _,_,s=bindings('w',{'id':'fan','source_columns':['x'],'target_columns':['x'],'predicate':'exact'},a,b)
    assert s['partial'] and s['fanout']==22500

def test_case_unicode_and_large_ids_preserved():
    c={'type':'text'};assert canonical('00000000000000001234',c,{})==['text','00000000000000001234']
    assert canonical('É',c,{})!=canonical('E',c,{})
    assert canonical('É',c,{'casefold':True,'unicode_nfc':True})==canonical('e\u0301',c,{'casefold':True,'unicode_nfc':True})

def test_rare_combinations_suppress_only_declared_cells():
    d=data(['region','cohort','score'],[['A','X','2'],['A','X','3'],['A','Y','4'],['B',None,'5']],{'score':'number'})
    out,notes=transform(d,[{'column':'region','kind':'rare_suppress','rare_threshold':2,'combination_columns':['region','cohort']}],[])
    assert out['rows']==[['A','X','2'],['A','X','3'],[None,'Y','4'],['B',None,'5']]
    assert notes[0]['suppressed_cells']==1 and d['rows'][2][0]=='A'

def test_long_reviewed_numbers_never_round_into_exact_matches():
    c={'type':'number'}
    a='1234567890123456789012345678901234567890'
    b='1234567890123456789012345678901234567891'
    assert canonical(a,c,{})!=canonical(b,c,{})
    assert canonical('1e3',c,{})==canonical('1000.00',c,{})
    assert canonical('-0.00',c,{})==canonical('0',c,{})
    d=data(['n'],[[b]],{'n':'number'});out,_=transform(d,[{'column':'n','kind':'numeric_bucket','width':10}],[])
    assert out['rows'][0][0]==a+'..1234567890123456789012345678901234567900'
