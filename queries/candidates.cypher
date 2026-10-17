// Full composite keys are atomic JoinKey nodes. Alternatives within this path are unioned.
MATCH __PATTERN__
RETURN DISTINCT s.idx, __END__.entity, __END__.idx
LIMIT 20001
