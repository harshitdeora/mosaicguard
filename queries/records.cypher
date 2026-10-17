UNWIND $rows AS row
CREATE (:Record {wid:$wid,sid:$sid,did:$did,idx:row.idx,entity:row.entity})
