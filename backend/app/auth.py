"""Explicitly DEMO login. Passwords securely hashed but OTP is shared 1234.

A fixed OTP does NOT verify ownership of a telephone. This is not production auth.
"""
import hashlib,os,re,secrets,time
from collections import defaultdict,deque
from datetime import datetime,timedelta,timezone
from fastapi import Cookie,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field,field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from argon2 import PasswordHasher,exceptions as argon_errors
from .database import SessionLocal,Member,AuthSession

COOKIE='br_v4_session'
DEMO_OTP=os.getenv('DEMO_OTP','1234')
COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true'
PW_HASHER=PasswordHasher(time_cost=2,memory_cost=19456,parallelism=2)
# Short-window in-memory friction for a local single API; not distributed rate limiting.
ATTEMPTS:dict[str,deque[float]]=defaultdict(deque)
def rate_limit(request:Request):
    ip=request.client.host if request.client else 'unknown'
    now=time.monotonic()
    recent=ATTEMPTS[ip]
    while recent and now-recent[0]>60:recent.popleft()
    if len(recent)>=20:raise HTTPException(status_code=429,detail='Too many login attempts. Try again in a minute.')
    recent.append(now)
def db_session():
    db=SessionLocal()
    try:yield db
    finally:db.close()
def normalize_phone(v:str)->str:
    p=v.translate(str.maketrans('০১২৩৪৫৬৭৮৯','0123456789'))
    if not re.fullmatch(r'01[3-9][0-9]{8}',p):raise ValueError('Enter a Bangladeshi number: 01XXXXXXXXX')
    return p
class Registration(BaseModel):
    phone:str
    password:str=Field(min_length=8,max_length=128)
    otp:str
    @field_validator('phone')
    @classmethod
    def phone_number(cls,v):return normalize_phone(v)
    @field_validator('password')
    @classmethod
    def password_strength(cls,v):
        if not re.search('[a-zA-Z]',v) or not re.search('[0-9]',v):raise ValueError('Password needs 8+ characters including letters and numbers')
        return v
class Login(BaseModel):
    phone:str
    password:str
    @field_validator('phone')
    @classmethod
    def phone_number(cls,v):return normalize_phone(v)
def public_profile(role:str,member:Member|None,expires_at:datetime):
    return dict(id=member.id if member else None,role=role,phone_masked=member.phone[:3]+'****'+member.phone[-4:] if member else None,expires_at=expires_at.isoformat(),demo_only=True,full_access=True)
def issue(response:Response,db:Session,member:Member|None=None):
    token=secrets.token_urlsafe(32)
    now=datetime.now(timezone.utc);expires=now+timedelta(days=1)
    db.add(AuthSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),member_id=member.id if member else None,role='member' if member else 'guest',created_at=now,expires_at=expires,revoked=False));db.commit()
    response.set_cookie(COOKIE,token,httponly=True,secure=COOKIE_SECURE,samesite='lax',max_age=86400,path='/')
    return public_profile('member' if member else 'guest',member,expires)
def require_user(token:str|None=Cookie(default=None,alias=COOKIE),db:Session=Depends(db_session)):
    if not token:raise HTTPException(status_code=401,detail='Login or Guest Access required')
    hashed=hashlib.sha256(token.encode()).hexdigest()
    record=db.query(AuthSession).filter(AuthSession.token_hash==hashed,AuthSession.revoked.is_(False)).first()
    if not record:raise HTTPException(status_code=401,detail='Invalid session')
    exp=record.expires_at.replace(tzinfo=record.expires_at.tzinfo or timezone.utc)
    if datetime.now(timezone.utc)>=exp:raise HTTPException(status_code=401,detail='Expired session')
    return public_profile(record.role,record.member,exp)
