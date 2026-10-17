import csv
import io
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, Field, ConfigDict
from fastapi import HTTPException
from .core import uid

MAX_BYTES=2*1024*1024
MAX_ROWS=1000
MAX_WORKSPACE_ROWS=5000
MAX_CELL=8192
csv.field_size_limit(MAX_CELL)

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class ParseConfig(Strict):
    encoding: str='utf-8-sig'
    delimiter: str=','
    quotechar: str='"'
    header: bool=True
    null_tokens: list[str]=Field(default_factory=list,max_length=20)
    skip_bad_rows: bool=False

class Column(Strict):
    id: str
    name: str=Field(max_length=200)
    type: str='text'
    date_format: str | None=None
    meaning: str=Field(default='',max_length=200)
    identifier: bool=False
    sensitive: bool=False

class ConfirmImport(Strict):
    parse: ParseConfig
    columns: list[Column]
    role: str='internal'
    row_unit: str='unknown'

def fail(message): raise HTTPException(422,message)

def suggest(values):
    vs=[v for v in values if v is not None]
    if not vs: return 'text'
    # No identifier/date coercion. Suggestions are review-only.
    if all(re.fullmatch(r'-?(0|[1-9]\d*)(\.\d+)?',v or ' ') for v in vs) and all(len(v)<16 for v in vs): return 'number'
    if all(re.fullmatch(r'\d{4}-\d{2}-\d{2}',v) for v in vs): return 'date'
    return 'text'

def parse_csv(raw, cfg: ParseConfig, previous=None):
    if not raw: fail('The file is empty. Choose a CSV with a header and at least one record.')
    if len(raw)>MAX_BYTES: fail('File exceeds the 2 MB supported limit.')
    if cfg.encoding not in ('utf-8-sig','utf-8','cp1252','latin-1'): fail('Choose UTF-8, Windows-1252 or Latin-1.')
    if cfg.delimiter not in (',',';','\t','|') or len(cfg.quotechar)!=1: fail('Choose a supported delimiter and one quote character.')
    try: text=raw.decode(cfg.encoding)
    except UnicodeDecodeError: fail('Cannot decode this file. Select the correct encoding before confirming.')
    if '\x00' in text or any(ord(c)<9 for c in text): fail('Binary content is not a supported CSV.')
    reader=csv.reader(io.StringIO(text,newline=''),delimiter=cfg.delimiter,quotechar=cfg.quotechar,strict=True)
    rows=[]; warnings=[]; excluded=0; headers=None; logical=0
    try:
        for record in reader:
            logical+=1
            if headers is None:
                if not record: fail('The first record is blank.')
                headers=record if cfg.header else ['Column '+str(i+1) for i in range(len(record))]
                if len(headers)>50: fail('Maximum 50 columns per file.')
                if any(not h.strip() or len(h)>200 for h in headers) or len(set(headers))!=len(headers):
                    fail('Headers must be nonblank, unique and at most 200 characters. Correct the source header or choose “No header”.')
                if cfg.header: continue
            if len(record)!=len(headers):
                if not cfg.skip_bad_rows: fail(f'Logical record {logical} has {len(record)} fields; expected {len(headers)}. Correct parsing or explicitly allow ragged-row exclusion.')
                excluded+=1
                if len(warnings)<20: warnings.append(f'Excluded ragged logical record {logical}.')
                continue
            if any(len(v)>MAX_CELL for v in record): fail(f'Logical record {logical} exceeds the 8,192-character cell limit.')
            rows.append([None if v=='' or v in cfg.null_tokens else v for v in record])
            if len(rows)+excluded>MAX_ROWS: fail('Maximum 1,000 logical data records per file.')
    except csv.Error:
        fail(f'Malformed quoting or oversized field near logical record {logical+1}. Correct the source file; no rows were silently skipped.')
    if not rows: fail('No usable data records. Headers-only files cannot be imported.')
    cols=[]
    for i,name in enumerate(headers):
        old=next((c for c in (previous or []) if c['name']==name),None)
        cols.append(old or {'id':uid(),'name':name,'type':suggest([r[i] for r in rows]),'date_format':None,'meaning':'','identifier':False,'sensitive':False})
    return {'columns':cols,'rows':rows,'excluded':excluded,'warnings':warnings,'imported_rows':len(rows),'logical_records':len(rows)+excluded}

def validate_columns(data, columns):
    if len(columns)!=len(data['columns']) or len({c.id for c in columns})!=len(columns): fail('Column schema does not match parsed file.')
    if [c.id for c in columns]!=[c['id'] for c in data['columns']]: fail('Review columns again after changing parsing settings.')
    for i,col in enumerate(columns):
        if col.type not in ('text','number','date'): fail('Supported reviewed types: text, number and date.')
        if col.type=='date' and col.date_format not in ('%Y-%m-%d','%d/%m/%Y','%m/%d/%Y'):
            fail('Date columns require an explicit supported format. Timestamps are supported only as exact text.')
        for n,row in enumerate(data['rows']):
            if row[i] is None: continue
            try:
                if col.type=='number':
                    d=Decimal(row[i])
                    if not d.is_finite(): raise ValueError()
                    if len(d.as_tuple().digits)>100 or not -100<=d.adjusted()<=100:
                        fail(f'Column {i+1}, logical data record {n+1}: numeric review supports up to 100 significant digits and adjusted exponents from -100 to 100. Select text to preserve a larger identifier or value.')
                elif col.type=='date':
                    from datetime import datetime
                    datetime.strptime(row[i],col.date_format)
            except (ValueError,InvalidOperation,OverflowError): fail(f'Column {i+1} contains an incompatible value at logical data record {n+1}. Choose text or correct the type/format.')

def profile(data):
    out=[]
    for i,col in enumerate(data['columns']):
        vs=[r[i] for r in data['rows']]
        out.append(dict(col,missing=sum(v is None for v in vs),distinct=len(set(v for v in vs if v is not None)),likely_identifier=bool(re.search(r'(^id$|email|phone|name|identifier)',col['name'],re.I))))
    return out

def csv_bytes(columns, rows, spreadsheet=True):
    out=io.StringIO(newline=''); w=csv.writer(out,lineterminator='\r\n')
    def escape(v):
        if v is None: return ''
        v=str(v)
        # Prefix apostrophe is a reversible transport step, not a semantic repair.
        if spreadsheet and (v.lstrip().startswith(('=','+','-','@')) or v.startswith(('\t','\r','\n',"'"))): return "'"+v
        return v
    w.writerow([escape(c['name']) for c in columns])
    w.writerows([[escape(v) for v in row] for row in rows])
    return out.getvalue().encode('utf-8-sig')
