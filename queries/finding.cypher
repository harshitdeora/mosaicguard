CREATE (f:Finding {wid:$wid,sid:$sid,fid:$fid,summary:$summary})
WITH f
UNWIND $rules AS rid
MERGE (r:JoinRule {wid:$wid,sid:$sid,rid:rid})
CREATE (f)-[:EVIDENCE_RULE]->(r)
