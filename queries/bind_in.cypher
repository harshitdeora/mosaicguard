UNWIND $rows AS row
MATCH (r:Record {wid:$wid,sid:$sid,did:$did,idx:row.idx})
MERGE (k:JoinKey {wid:$wid,sid:$sid,rule:$rule,token:row.token})
CREATE (r)-[:IN_KEY]->(k)
