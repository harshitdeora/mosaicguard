import copy
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR, localcontext
from statistics import mean, median
from .core import get

def transform(data,recipe,protected):
    out=copy.deepcopy(data);notes=[]
    for t in recipe:
        idx=next((i for i,c in enumerate(out['columns']) if c['id']==t['column']),None)
        if idx is None: raise ValueError('Recipe column is unavailable.')
        col=out['columns'][idx]
        if t['column'] in protected: raise ValueError('A protected column cannot be transformed or removed.')
        if col.get('generalization'): raise ValueError('Only one generalisation per column is supported per recipe.')
        if t['kind']=='drop':
            out['columns'].pop(idx)
            for row in out['rows']: row.pop(idx)
        elif t['kind'] in ('suppress','rare_suppress'):
            combination=t.get('combination_columns') or [t['column']]
            lookup={c['id']:i for i,c in enumerate(out['columns'])}
            if any(c not in lookup for c in combination):raise ValueError('Rare-combination fields must remain available at this recipe step.')
            keys=[tuple(row[lookup[c]] for c in combination) for row in out['rows']]
            freq=Counter(k for k in keys if None not in k)
            count=0
            for row,k in zip(out['rows'],keys):
                if t['kind']=='suppress' or (None not in k and freq[k]<t['rare_threshold']):
                    count+=row[idx] is not None;row[idx]=None
            notes.append({'column':t['column'],'suppressed_cells':count})
        elif t['kind']=='numeric_bucket':
            if col['type']!='number': raise ValueError('Numeric buckets require a reviewed numeric column.')
            width=Decimal(str(t['width']))
            with localcontext() as ctx:
                ctx.prec=512
                for row in out['rows']:
                    if row[idx] is not None:
                        lo=(Decimal(row[idx])/width).to_integral_value(rounding=ROUND_FLOOR)*width
                        row[idx]=f'{lo}..{lo+width}'
            col['generalization']='numeric_bucket';col['bucket_width']=str(width)
        else:
            if col['type']!='date': raise ValueError('Date generalisation requires an explicit reviewed date format.')
            precision=t['kind'].split('_')[1]
            for row in out['rows']:
                if row[idx] is None: continue
                d=datetime.strptime(row[idx],col['date_format'])
                if d.year>=9999: raise ValueError('Year 9999 cannot be generalised to an open-ended date interval.')
                row[idx]=f'{d.year:04}-{d.month:02}' if precision=='month' else f'{d.year:04}-Q{(d.month-1)//3+1}' if precision=='quarter' else str(d.year)
            col['generalization']=precision
    return out,notes

def utility_result(data,u):
    index={c['id']:i for i,c in enumerate(data['columns'])}
    if (u.get('group') and u['group'] not in index) or (u.get('value') and u['value'] not in index): return None,'Required analytical column was removed.'
    if u['operation'] in ('mean','median'):
        if not u.get('value'): return None,'Select a numeric value column.'
        col=data['columns'][index[u['value']]]
        if col['type']!='number' or col.get('generalization'): return None,'Exact numeric statistic is unavailable for a generalised or nonnumeric field.'
    groups=defaultdict(list)
    for row in data['rows']:
        group=row[index[u['group']]] if u.get('group') else 'All records'
        if u['operation']=='time_count':
            if not u.get('group') or group is None: continue
            col=data['columns'][index[u['group']]]
            if col['type']!='date' or col.get('generalization'): return None,'Time counts currently require unmodified reviewed dates.'
            d=datetime.strptime(group,col['date_format']);grain=u['granularity']
            group=f'{d.year:04}-{d.month:02}' if grain=='month' else f'{d.year:04}-Q{(d.month-1)//3+1}' if grain=='quarter' else str(d.year)
        key='Missing' if group is None else str(group)
        if u['operation'] in ('mean','median'):
            value=row[index[u['value']]]
            if value is not None: groups[key].append(float(Decimal(value)))
            else: groups[key]  # preserve empty groups
        else: groups[key].append(1)
    result={k:(mean(v) if u['operation']=='mean' else median(v)) if v and u['operation'] in ('mean','median') else None if u['operation'] in ('mean','median') else len(v) for k,v in groups.items()}
    return result,None

def compare_utility(original,repaired,scenario):
    metrics=[];violated=False
    for u in scenario['utility']:
        did=u['dataset'];before,error1=utility_result(original[did],u);after,error2=utility_result(repaired[did],u)
        rows=[];valid=not(error1 or error2)
        if valid:
            for key in sorted(set(before)|set(after)):
                b=before.get(key);a=after.get(key)
                absolute=None if b is None or a is None else abs(a-b)
                relative=None if absolute is None or b==0 else absolute/abs(b)
                ok=absolute==0 if b==0 else relative is not None and relative<=u['max_relative_drift']
                valid=valid and ok
                # Group labels remain encrypted and authenticated in the product; omitted from default reports.
                rows.append({'group':key,'original':b,'repaired':a,'absolute_change':absolute,'relative_change':relative,'satisfies':ok})
        violated=violated or not valid
        metrics.append({'definition':u,'status':'satisfied' if valid else 'violated','unavailable_reason':error1 or error2,'groups':rows})
    retention=[]
    for did in scenario['candidates']:
        n=len(original[did]['rows']);m=len(repaired[did]['rows']);ratio=m/n if n else None
        ok=ratio is not None and ratio>=scenario['min_retention'];violated|=not ok
        retention.append({'dataset':did,'original_rows':n,'retained_rows':m,'suppressed_rows':n-m,'retention':ratio,'satisfies':ok,
                          'missing_cells_before':sum(v is None for r in original[did]['rows'] for v in r),
                          'missing_cells_after':sum(v is None for r in repaired[did]['rows'] for v in r),
                          'generalised_columns':sum(bool(c.get('generalization')) for c in repaired[did]['columns'])})
    return {'status':'violated' if violated else 'satisfied','metrics':metrics,'retention':retention,'population_note':'No row suppression is performed; retained and original cohorts coincide.'}
