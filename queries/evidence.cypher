MATCH (f:Finding {wid:$wid,sid:$sid,fid:$fid})
RETURN f.summary
