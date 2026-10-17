from typing import Literal
from pydantic import Field
from .ingestion import Strict

class Rule(Strict):
    id: str
    source: str
    target: str
    source_columns: list[str]=Field(min_length=1,max_length=5)
    target_columns: list[str]=Field(min_length=1,max_length=5)
    meaning: str=Field(min_length=3,max_length=200)
    subject: Literal['person','household','organisation','event','unknown']='unknown'
    context: str=Field(min_length=3,max_length=200)
    predicate: Literal['exact','compatible']='exact'
    trim: bool=False
    casefold: bool=False
    unicode_nfc: bool=False
    confirmed: bool=False
    revision: int=1

class Anchor(Strict):
    dataset: str
    columns: list[str]=Field(min_length=1,max_length=3)
    justification: str=Field(min_length=10,max_length=300)

class Utility(Strict):
    dataset: str
    group: str | None=None
    operation: Literal['count','mean','median','time_count']='count'
    value: str | None=None
    granularity: Literal['month','quarter','year']='month'
    max_relative_drift: float=Field(default=.1,ge=0,le=10)

class QI(Strict):
    dataset: str
    columns: list[str]=Field(min_length=1,max_length=5)

class Bundle(Strict):
    source: str
    paths: list[list[str]]=Field(min_length=2,max_length=5)
    same_subject_context: str=Field(min_length=10,max_length=300)
    confirmed: bool=False

class Scenario(Strict):
    name: str=Field(min_length=1,max_length=120)
    audience: str=Field(min_length=3,max_length=300)
    purpose: str=Field(min_length=3,max_length=500)
    candidates: list[str]=Field(min_length=1,max_length=5)
    available: list[str]=Field(default_factory=list,max_length=10)
    rules: list[Rule]=Field(default_factory=list,max_length=20)
    anchors: list[Anchor]=Field(default_factory=list,max_length=5)
    quasi_identifiers: list[QI]=Field(default_factory=list,max_length=10)
    utility: list[Utility]=Field(default_factory=list,max_length=10)
    protected: list[str]=Field(default_factory=list,max_length=50)
    min_retention: float=Field(default=1,ge=0,le=1)
    threshold: int=Field(default=5,ge=2,le=100)
    max_depth: int=Field(default=3,ge=1,le=3)
    reference_coverage: str=Field(default='Unknown completeness; supplied reference records only.',max_length=500)
    bundles: list[Bundle]=Field(default_factory=list,max_length=5)

class Transform(Strict):
    dataset: str
    column: str
    kind: Literal['drop','suppress','numeric_bucket','date_month','date_quarter','date_year','rare_suppress']
    width: float=Field(default=10,gt=0,le=1000000000)
    rare_threshold: int=Field(default=5,ge=2,le=100)

class Repair(Strict):
    scenario: str
    name: str=Field(min_length=1,max_length=120)
    recipe: list[Transform]=Field(min_length=1,max_length=20)
