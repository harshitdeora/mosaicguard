import os
from pathlib import Path
from falkordb import FalkorDB
from fastapi import HTTPException

QUERY_DIR=Path(__file__).resolve().parents[2]/'queries'

class Graph:
    def __init__(self,wid,sid):
        self.wid=wid;self.sid=sid
        self.db=FalkorDB(host=os.getenv('MOSAIC_GRAPH_HOST','localhost'),port=int(os.getenv('MOSAIC_GRAPH_PORT','6381')),
                        password=os.getenv('MOSAIC_GRAPH_PASSWORD') or None,socket_timeout=12,socket_connect_timeout=3)
        self.g=self.db.select_graph('mg_'+wid+'_'+sid)
    def query(self,text,params=None):
        return self.g.query(text,params={'wid':self.wid,'sid':self.sid,**(params or {})},timeout=8000).result_set
    def template(self,name,params=None): return self.query((QUERY_DIR/name).read_text(),params)
    def initialize(self):
        self.query('CREATE INDEX FOR (r:Record) ON (r.did, r.idx)')
        self.query('CREATE INDEX FOR (k:JoinKey) ON (k.rule, k.token)')
    def records(self,did,rows):
        for offset in range(0,len(rows),200): self.template('records.cypher',{'did':did,'rows':rows[offset:offset+200]})
    def bind(self,did,rule,rows,side):
        # These two fixed templates whitelist the only attacker traversal relationships.
        name='bind_out.cypher' if side=='out' else 'bind_in.cypher'
        for offset in range(0,len(rows),200): self.template(name,{'did':did,'rule':rule,'rows':rows[offset:offset+200]})
    def candidates(self,path,source,target):
        # Only generated identifiers and a maximum of 3 hops enter the template.
        pattern='(s:Record {wid:$wid,sid:$sid,did:$source})'
        params={'source':source,'target':target}
        for i,rule in enumerate(path):
            params['r'+str(i)]=rule['id'];params['d'+str(i)]=rule['target']
            pattern+=f'-[:OUT_KEY]->(k{i}:JoinKey {{wid:$wid,sid:$sid,rule:$r{i}}})<-[:IN_KEY]-(t{i}:Record {{wid:$wid,sid:$sid,did:$d{i}}})'
        last='t'+str(len(path)-1)
        text=(QUERY_DIR/'candidates.cypher').read_text().replace('__PATTERN__',pattern).replace('__END__',last)
        return self.query(text,params)
    def finding(self,fid,summary): self.template('finding.cypher',{'fid':fid,'summary':summary})
    def evidence(self,fid): return self.template('evidence.cypher',{'fid':fid})
    def delete(self):
        try: self.g.delete()
        except Exception as e:
            if 'does not exist' not in str(e) and 'Invalid graph operation on empty key' not in str(e): raise

def healthy():
    try:
        g=Graph('health','health')
        return bool(g.db.connection.ping())
    except Exception: return False

def require_graph():
    if not healthy(): raise HTTPException(503,'FalkorDB is unavailable. Start the graph service with docker compose up -d graph; audits and graph mutations are blocked.')
