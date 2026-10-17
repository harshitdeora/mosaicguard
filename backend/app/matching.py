"""Typed compatibility in authorised processing memory; no ordered token comparison."""
import unicodedata
from datetime import datetime, date
from decimal import Decimal
from collections import defaultdict
from .core import token

def canonical(value, column, rule):
    if value is None or value=='': return None
    value=str(value)
    if rule.get('trim'): value=value.strip()
    if not value: return None
    if rule.get('unicode_nfc'): value=unicodedata.normalize('NFC',value)
    if rule.get('casefold'): value=value.casefold()
    if column['type']=='number' and not column.get('generalization'): return ['number',str(Decimal(value).normalize())]
    if column['type']=='date' and not column.get('generalization'):
        return ['date',datetime.strptime(value,column['date_format']).date().isoformat()]
    return ['text',value]

def interval(value, col):
    if value is None or value=='': return None
    g=col.get('generalization')
    if col['type']=='number':
        if g:
            lo,hi=value.split('..')
            return Decimal(lo),Decimal(hi),False
        d=Decimal(value); return d,d,True
    if col['type']=='date':
        if g=='month':
            y,m=map(int,value.split('-')); lo=date(y,m,1); hi=date(y+1,1,1) if m==12 else date(y,m+1,1)
        elif g=='quarter':
            y,q=value.split('-Q'); y=int(y); m=(int(q)-1)*3+1
            lo=date(y,m,1); hi=date(y+1,1,1) if m==10 else date(y,m+3,1)
        elif g=='year': lo=date(int(value),1,1); hi=date(int(value)+1,1,1)
        else:
            d=datetime.strptime(value,col['date_format']).date().toordinal(); return d,d,True
        return lo.toordinal(),hi.toordinal(),False
    raise ValueError('Unsupported typed interval.')

def overlap(a,b):
    if a is None or b is None: return False
    al,ah,ap=a; bl,bh,bp=b
    if ap and bp: return al==bl
    if ap: return bl<=al<bh
    if bp: return al<=bl<ah
    return max(al,bl)<min(ah,bh)

def compatible(va,ca,vb,cb,rule):
    if va is None or vb is None: return False
    if ca['type']!=cb['type']: return False
    if ca.get('generalization') or cb.get('generalization'):
        if rule['predicate']!='compatible': raise ValueError('Generalised exact field requires a confirmed typed-compatible rule.')
        return overlap(interval(va,ca),interval(vb,cb))
    return canonical(va,ca,rule)==canonical(vb,cb,rule)

def bindings(wid,rule,a,b,comparison_limit=250000):
    """Return key bindings, never an independent persistent linkage graph.

    Exact composites create one keyed hub per complete tuple. Interval compatibility
    uses exact components as a blocking key, then explicitly checks every predicate.
    """
    ac={c['id']:(i,c) for i,c in enumerate(a['columns'])}; bc={c['id']:(i,c) for i,c in enumerate(b['columns'])}
    if any(c not in ac for c in rule['source_columns']) or any(c not in bc for c in rule['target_columns']):
        return [],[],{'blocked':True,'reason':'Required column removed by the reviewed recipe.','fanout':0,'missing':len(a['rows'])}
    pairs=[(ac[x],bc[y]) for x,y in zip(rule['source_columns'],rule['target_columns'])]
    typed=[k for k,((_,ca),(_,cb)) in enumerate(pairs) if ca.get('generalization') or cb.get('generalization')]
    if typed and rule['predicate']!='compatible':
        return [],[],{'partial':True,'reason':'Generalised field needs a typed-compatible predicate. Exact text comparison was not used.','fanout':0,'missing':len(a['rows'])}
    def key_for(row,side,indices):
        vals=[]
        for k in indices:
            i,col=pairs[k][side]; v=canonical(row[i],col,rule)
            if v is None: return None
            vals.append(v)
        return token(wid,rule['id'],vals)
    complete_a=[i for i,row in enumerate(a['rows']) if all(row[p[0][0]] is not None for p in pairs)]
    complete_b=[i for i,row in enumerate(b['rows']) if all(row[p[1][0]] is not None for p in pairs)]
    left=[];right=[];fanout=0;maximum=0;missing=len(a['rows'])-len(complete_a)
    if not typed:
        groups=defaultdict(list)
        for j in complete_b:
            k=key_for(b['rows'][j],1,range(len(pairs)))
            if k is not None: groups[k].append(j); right.append({'idx':j,'token':k})
        for i in complete_a:
            k=key_for(a['rows'][i],0,range(len(pairs)))
            if k is None: missing+=1;continue
            left.append({'idx':i,'token':k})
            n=len(groups[k]);fanout+=n;maximum=max(maximum,n)
    else:
        exact=[k for k in range(len(pairs)) if k not in typed]
        groups=defaultdict(list)
        for j in complete_b: groups[key_for(b['rows'][j],1,exact)].append(j)
        comparisons=0
        for i in complete_a:
            n=0
            for j in groups[key_for(a['rows'][i],0,exact)]:
                comparisons+=1
                if comparisons>comparison_limit:
                    return [],[],{'partial':True,'reason':'Typed comparison budget reached. Narrow the rule with an exact component.','fanout':fanout,'missing':missing}
                if all(compatible(a['rows'][i][ia],ca,b['rows'][j][ib],cb,rule) for (ia,ca),(ib,cb) in pairs):
                    n+=1;fanout+=1
                    if fanout>20000: return [],[],{'partial':True,'reason':'Compatible match bound exceeded. Narrow this rule.','fanout':fanout,'missing':missing}
                    k=token(wid,rule['id'],['compatible',i,j])
                    left.append({'idx':i,'token':k});right.append({'idx':j,'token':k})
            maximum=max(maximum,n)
    return left,right,{'fanout':fanout,'max_candidates':maximum,'missing':missing,'partial':fanout>20000,
                        'reason':'Fan-out exceeds 20,000. Add a selective composite component or narrow the scenario.' if fanout>20000 else None}

def rule_paths(scenario):
    paths=[];truncated=False
    rules=[r for r in scenario['rules'] if r['confirmed']]
    available=set(scenario['candidates']+scenario['available'])
    def visit(did,chain,seen):
        nonlocal truncated
        if len(chain)>=scenario['max_depth']: return
        for rule in rules:
            if rule['source']!=did or rule['target'] not in available or rule['target'] in seen: continue
            path=chain+[rule]
            if len(paths)>=100: truncated=True;return
            paths.append(path)
            visit(rule['target'],path,seen|{rule['target']})
    for source in scenario['candidates']: visit(source,[],{source})
    return paths,truncated
