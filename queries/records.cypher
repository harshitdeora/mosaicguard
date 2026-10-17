MERGE (v:DatasetVersion {wid:$wid,sid:$sid,did:$did})
WITH v
UNWIND $rows AS row
CREATE (r:Record {wid:$wid,sid:$sid,did:$did,idx:row.idx,entity:row.entity})
CREATE (v)-[:HAS_RECORD]->(r)
