from datetime import date
from typing import Literal
from pydantic import BaseModel,Field,model_validator,field_validator
class Claim(BaseModel):
    plot_id:str=Field(min_length=1,max_length=32)
    deed_no:str=Field(min_length=1,max_length=60)
    seller:str=Field(min_length=1,max_length=150)
    buyer:str=Field(min_length=1,max_length=150)
    portion_code:str=Field(min_length=1,max_length=60)
    share_start:float=Field(ge=0,le=1)
    share_end:float=Field(ge=0,le=1)
    deed_date:date
    mutation_owner:str|None=Field(default=None,max_length=150)
    mutation_status:Literal['completed','pending','unknown']='unknown'
    previous_deed:str|None=Field(default=None,max_length=60)
    district:str|None=Field(default=None,max_length=90)
    mouza:str|None=Field(default=None,max_length=90)
    khatian:str|None=Field(default=None,max_length=60)
    dag:str|None=Field(default=None,max_length=60)
    ref_key:str|None=Field(default=None,max_length=100)
    sha256:str|None=None
    @model_validator(mode='after')
    def interval(self):
        if self.share_end <= self.share_start:raise ValueError('End share must exceed start share')
        return self
    @field_validator('sha256')
    @classmethod
    def digest(cls,s):
        if s is not None and (len(s)!=64 or any(c not in '0123456789abcdefABCDEF' for c in s)):raise ValueError('SHA-256 must be 64 hex characters')
        return s.lower() if s else s
class Assessment(BaseModel):
    claims:list[Claim]=Field(min_length=1,max_length=10)
