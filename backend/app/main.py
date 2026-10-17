"""BhumiRokkhi source V4: demo signup/login/guest, P3 screening and sample references."""
import os,hashlib,re
from datetime import datetime,timezone
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,Depends,Response,Request,HTTPException,UploadFile,File,Form,Cookie,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from argon2 import exceptions as hash_exceptions
from .database import seed,Plot,Sale,TrustedDocument,SavedReference,Member,AuthSession
from .schemas import Assessment
from .scenarios import SCENARIOS
from .engine import assess as run_assessment
from .documents import read_document,compare
from .auth import COOKIE,DEMO_OTP,PW_HASHER,COOKIE_SECURE,Registration,Login,rate_limit,db_session,issue,require_user

@asynccontextmanager
async def lifespan(app:FastAPI):seed();yield
app=FastAPI(title='BhumiRokkhi — Hackathon Demo API',version='4.0.0',lifespan=lifespan)
allowed=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(',')]
app.add_middleware(CORSMiddleware,allow_origins=allowed,allow_credentials=True,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
@app.middleware('http')
async def csrf_origin_check(request:Request,call_next):
    if request.method in {'POST','PATCH','PUT','DELETE'} and request.url.path.startswith('/api/'):
        origin=request.headers.get('origin')
        if origin and origin not in allowed:return Response('Origin not permitted',status_code=403)
    return await call_next(request)
SAMPLES=Path(__file__).parent.parent/'samples'
app.mount('/samples',StaticFiles(directory=str(SAMPLES)),name='samples')
@app.get('/api/health')
def health():return dict(ok=True,version='4.0.0',demo=True,government_connected=False)
@app.post('/api/auth/register',dependencies=[Depends(rate_limit)])
def register(payload:Registration,response:Response,db:Session=Depends(db_session)):
    if payload.otp!=DEMO_OTP:raise HTTPException(400,'Incorrect DEMO OTP. Use 1234')
    if db.query(Member).filter(Member.phone==payload.phone).first():raise HTTPException(409,'Account exists. Go to Login')
    account=Member(phone=payload.phone,password_hash=PW_HASHER.hash(payload.password))
    db.add(account)
    try:db.commit();db.refresh(account)
    except IntegrityError:db.rollback();raise HTTPException(409,'Account already exists')
    return issue(response,db,account)
@app.post('/api/auth/login',dependencies=[Depends(rate_limit)])
def login(payload:Login,response:Response,db:Session=Depends(db_session)):
    account=db.query(Member).filter(Member.phone==payload.phone).first()
    if not account:raise HTTPException(401,'Incorrect phone or password')
    try:PW_HASHER.verify(account.password_hash,payload.password)
    except (hash_exceptions.VerificationError,hash_exceptions.InvalidHashError):raise HTTPException(401,'Incorrect phone or password')
    return issue(response,db,account)
@app.post('/api/auth/guest',dependencies=[Depends(rate_limit)])
def guest(response:Response,db:Session=Depends(db_session)):return issue(response,db)
@app.get('/api/auth/me')
def me(user:dict=Depends(require_user)):return user
@app.post('/api/auth/logout')
def logout(response:Response,token:str|None=Cookie(None,alias=COOKIE),db:Session=Depends(db_session)):
    if token:
        row=db.query(AuthSession).filter(AuthSession.token_hash==hashlib.sha256(token.encode()).hexdigest()).first()
        if row:row.revoked=True;db.commit()
    response.delete_cookie(COOKIE,samesite='lax',secure=COOKIE_SECURE,path='/')
    return dict(ok=True)
def plot_obj(p:Plot):return dict(id=p.id,district=p.district,district_bn=p.district_bn,upazila=p.upazila,upazila_bn=p.upazila_bn,mouza=p.mouza,mouza_bn=p.mouza_bn,khatian=p.khatian,dag=p.dag,area_decimal=p.area_decimal,lat=p.lat,lng=p.lng,source='synthetic')
def sale_obj(s:Sale):return dict(plot_id=s.plot_id,deed_no=s.deed_no,seller=s.seller,buyer=s.buyer,portion_code=s.portion_code,share_start=s.share_start,share_end=s.share_end,deed_date=s.deed_date.isoformat(),mutation_owner=s.mutation_owner,mutation_status=s.mutation_status,previous_deed=s.previous_deed)
@app.get('/api/stats')
def stats(user:dict=Depends(require_user),db:Session=Depends(db_session)):
    return dict(plots=db.query(Plot).count(),transactions=db.query(Sale).count(),test_cases=len(SCENARIOS),government_connected=False,version='4.0.0')
@app.get('/api/plots')
def plots(q:str=Query('',max_length=120),district:str=Query('',max_length=90),user:dict=Depends(require_user),db:Session=Depends(db_session)):
    from sqlalchemy import or_
    found=db.query(Plot)
    if q:
        val='%'+q.translate(str.maketrans('০১২৩৪৫৬৭৮৯','0123456789')).strip()+'%'
        found=found.filter(or_(Plot.id.ilike(val),Plot.mouza.ilike(val),Plot.mouza_bn.ilike(val),Plot.khatian.ilike(val),Plot.dag.ilike(val)))
    if district:found=found.filter(or_(Plot.district.ilike(district),Plot.district_bn.ilike(district)))
    return [plot_obj(x) for x in found.order_by(Plot.id).limit(40).all()]
@app.get('/api/plots/{plot_id}')
def plot_detail(plot_id:str,user:dict=Depends(require_user),db:Session=Depends(db_session)):
    plot=db.get(Plot,plot_id)
    if not plot:raise HTTPException(404,'Synthetic plot not found')
    return dict(plot=plot_obj(plot),transactions=[sale_obj(x) for x in sorted(plot.sales,key=lambda x:x.deed_date)])
@app.get('/api/scenarios')
def scenarios(user:dict=Depends(require_user)):return SCENARIOS
@app.post('/api/assess')
def assess(req:Assessment,user:dict=Depends(require_user),db:Session=Depends(db_session)):return run_assessment(db,req.claims)
@app.post('/api/documents/extract')
async def document_extract(file:UploadFile=File(...),user:dict=Depends(require_user)):
    return await read_document(file)
@app.post('/api/documents/compare')
async def document_compare(first:UploadFile=File(...),second:UploadFile=File(...),user:dict=Depends(require_user)):
    a=await read_document(first);b=await read_document(second)
    return dict(first=a,second=b,comparison=compare(a,b))
def owner_namespace(user:dict,token:str|None)->str:
    if user['role']=='member' and user['id'] is not None:
        return f"member:{user['id']}"
    if token is None:
        raise HTTPException(401,'A guest session is required')
    return 'guest:'+hashlib.sha256(token.encode()).hexdigest()


def public_reference(item:SavedReference)->dict:
    return dict(ref_key=item.ref_key,sha256=item.sha256,deed_no=item.deed_no,
        label=item.label,file_name=item.file_name,created_at=item.created_at.isoformat(),
        source='user_saved',officially_verified=False)


# Simplified two-upload workflow: no visible reference name, code or selector.
# Each account or guest session has exactly one active user-designated baseline.
ACTIVE_REFERENCE_KEY='AUTO-CURRENT'

def active_reference_record(db:Session, namespace:str):
    return db.query(SavedReference).filter(
        SavedReference.owner_key==namespace,
        SavedReference.ref_key==ACTIVE_REFERENCE_KEY,
    ).first()

@app.get('/api/documents/active-reference')
def active_reference(user:dict=Depends(require_user),
        token:str|None=Cookie(None,alias=COOKIE),db:Session=Depends(db_session)):
    record=active_reference_record(db,owner_namespace(user,token))
    return dict(reference=public_reference(record) if record else None)

@app.post('/api/documents/active-reference',status_code=201,dependencies=[Depends(rate_limit)])
async def upload_active_reference(file:UploadFile=File(...),acknowledge:bool=Form(False),
        user:dict=Depends(require_user),token:str|None=Cookie(None,alias=COOKIE),
        db:Session=Depends(db_session)):
    if not acknowledge:
        raise HTTPException(422,'Please confirm this is an authorized demo document')
    # The document is read and hashed in memory; its content is never persisted.
    document=await read_document(file)
    ns=owner_namespace(user,token)
    record=active_reference_record(db,ns)
    if record is None:
        record=SavedReference(owner_key=ns,ref_key=ACTIVE_REFERENCE_KEY,
            sha256=document['sha256'],deed_no=document['fields'].get('deed_no',''),
            label=document['filename'][:120],file_name=document['filename'])
        db.add(record)
    else:
        # Replaces only this user's active baseline. Legacy named references are untouched.
        record.sha256=document['sha256']
        record.deed_no=document['fields'].get('deed_no','')
        record.label=document['filename'][:120]
        record.file_name=document['filename']
        record.created_at=datetime.now(timezone.utc)
    try:
        db.commit();db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Please retry saving your sample document')
    return dict(reference=public_reference(record),document_stored=False,
        replaced=True,note='Sample SHA-256 stored only; NOT a verified original or official title')

@app.post('/api/documents/active-reference-check')
async def check_active_reference(file:UploadFile=File(...),
        user:dict=Depends(require_user),token:str|None=Cookie(None,alias=COOKIE),
        db:Session=Depends(db_session)):
    ref=active_reference_record(db,owner_namespace(user,token))
    if ref is None:
        raise HTTPException(409,'Save your own sample document before checking another file')
    document=await read_document(file)
    extracted_deed=document['fields'].get('deed_no')
    deed_matches=not bool(ref.deed_no and extracted_deed and extracted_deed!=ref.deed_no)
    equal=document['sha256']==ref.sha256
    return dict(reference_key=ref.ref_key,match=equal,deed_matches=deed_matches,
        document=document,reference_sha256=ref.sha256,submitted_sha256=document['sha256'],
        original_filename=ref.file_name,officially_verified=False,source='user_saved',
        explanation=('Uploaded bytes match the saved sample' if equal else
           'Uploaded bytes differ from the saved sample; not proof of forgery'),
        explanation_bn=('আপলোড করা ফাইলটি সংরক্ষিত নমুনার সঙ্গে হুবহু মিলেছে।' if equal else
           'আপলোড করা ফাইলটি সংরক্ষিত নমুনা থেকে আলাদা; এটি জালিয়াতির প্রমাণ নয়।'))

@app.get('/api/documents/references')
def list_references(user:dict=Depends(require_user),token:str|None=Cookie(None,alias=COOKIE),db:Session=Depends(db_session)):
    ns=owner_namespace(user,token)
    refs=db.query(SavedReference).filter(SavedReference.owner_key==ns).order_by(SavedReference.id.desc()).limit(30).all()
    return dict(references=[public_reference(x) for x in refs],demo_reference=dict(ref_key='DEMO-D4001',label='D-4001 synthetic sample',source='demo',officially_verified=False))


@app.post('/api/documents/references',status_code=201,dependencies=[Depends(rate_limit)])
async def register_reference(
    file:UploadFile=File(...),
    ref_key:str=Form(...,min_length=3,max_length=60),
    label:str=Form(...,min_length=3,max_length=120),
    acknowledge:bool=Form(False),
    user:dict=Depends(require_user),
    token:str|None=Cookie(None,alias=COOKIE),
    db:Session=Depends(db_session),
):
    if not acknowledge:
        raise HTTPException(422,'Confirm this is an authorized DEMO sample, not a government certificate')
    ref_key=ref_key.strip().upper()
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{2,59}',ref_key):
        raise HTTPException(422,'Reference key: 3–60 English letters, digits, underscore or dash')
    if ref_key.startswith('DEMO-'):
        raise HTTPException(409,'DEMO- reference keys are reserved')
    ns=owner_namespace(user,token)
    if db.query(SavedReference).filter(SavedReference.owner_key==ns).count()>=30:
        raise HTTPException(429,'Maximum 30 demo references per account/session')
    if db.query(SavedReference).filter(SavedReference.owner_key==ns,SavedReference.ref_key==ref_key).first():
        raise HTTPException(409,'This reference key is already registered. Choose a new key')
    document=await read_document(file)
    record=SavedReference(owner_key=ns,ref_key=ref_key,sha256=document['sha256'],
        deed_no=document['fields'].get('deed_no',''),label=label.strip(),file_name=document['filename'])
    db.add(record)
    try:
        db.commit();db.refresh(record)
    except IntegrityError:
        db.rollback();raise HTTPException(409,'This reference key is already registered')
    return dict(reference=public_reference(record),document_stored=False,
        note='User-saved SHA-256 only; not independently certified or government verified')


@app.post('/api/documents/reference-check')
async def reference_check(file:UploadFile=File(...),ref_key:str=Query(...,min_length=1,max_length=100),
        user:dict=Depends(require_user),token:str|None=Cookie(None,alias=COOKIE),db:Session=Depends(db_session)):
    if ref_key=='DEMO-D4001':
        ref=db.get(TrustedDocument,ref_key)
        if not ref:raise HTTPException(404,'Synthetic reference not found')
    else:
        ns=owner_namespace(user,token)
        ref=db.query(SavedReference).filter(SavedReference.owner_key==ns,SavedReference.ref_key==ref_key).first()
        if not ref:raise HTTPException(404,'Reference not found in this account/session')
    document=await read_document(file)
    extracted_deed=document['fields'].get('deed_no')
    deed_matches=not bool(ref.deed_no and extracted_deed and extracted_deed!=ref.deed_no)
    equal=document['sha256']==ref.sha256
    # Verifying a file's byte identity is not verifying its legal authenticity.
    return dict(reference_key=ref_key,match=equal,deed_matches=deed_matches,
        document=document,reference_sha256=ref.sha256,submitted_sha256=document['sha256'],
        officially_verified=False,source='demo' if ref_key=='DEMO-D4001' else 'user_saved',
        explanation=('Exact same bytes as saved reference' if equal else
            'Different bytes from saved reference; not proof of fraud'),
        explanation_bn=('সংরক্ষিত রেফারেন্স ও আপলোড করা ফাইল হুবহু একই।' if equal else
            'আপলোড করা ফাইলের Hash রেফারেন্সের সঙ্গে মেলে না; এটি জালিয়াতির প্রমাণ নয়।'))
