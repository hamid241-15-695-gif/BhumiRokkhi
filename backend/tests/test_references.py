"""V4: user-saved reference lifecycle, per-session ownership, and demo safety."""
from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from app.auth import COOKIE
from app.main import app
from hashlib import sha256

SAMPLE=Path(__file__).resolve().parents[1]/'samples'/'D-4001_reference.pdf'
CHANGED=Path(__file__).resolve().parents[1]/'samples'/'D-4001_changed_version.pdf'

def put(client, path=SAMPLE, key='MY-DEED-001', acknowledge='true', label='My sample file'):
    with path.open('rb') as fh:
        return client.post('/api/documents/references',data={'ref_key':key,'label':label,'acknowledge':acknowledge},files={'file':(path.name,fh,'application/pdf')})

def verify(client, path=SAMPLE,key='MY-DEED-001'):
    with path.open('rb') as fh:
        return client.post('/api/documents/reference-check',params={'ref_key':key},files={'file':(path.name,fh,'application/pdf')})

def test_guest_registration_check_same_and_changed(client):
    assert client.post('/api/documents/references',data={}).status_code==401
    assert client.get('/api/documents/references').status_code==401
    client.post('/api/auth/guest')
    assert client.get('/api/documents/references').json()['references']==[]
    original=put(client)
    assert original.status_code==201,original.text
    record=original.json()['reference']
    assert record['ref_key']=='MY-DEED-001'
    assert record['sha256']==sha256(SAMPLE.read_bytes()).hexdigest()
    assert record['officially_verified'] is False
    assert original.json()['document_stored'] is False
    assert client.get('/api/documents/references').json()['references'][0]['ref_key']=='MY-DEED-001'
    same=verify(client).json()
    assert same['match'] is True
    assert same['officially_verified'] is False
    assert same['reference_sha256']==same['submitted_sha256']
    altered=verify(client,CHANGED).json()
    assert altered['match'] is False
    assert altered['reference_sha256']!=altered['submitted_sha256']


def test_guest_scope_logout_new_session_cannot_access(client):
    client.post('/api/auth/guest');assert put(client).status_code==201
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/documents/references').status_code==401
    client.post('/api/auth/guest')
    assert client.get('/api/documents/references').json()['references']==[]
    assert verify(client).status_code==404


def test_member_refs_persist_across_logins(client):
    payload={'phone':'01712345678','password':'DemoPass123','otp':'1234'}
    assert client.post('/api/auth/register',json=payload).status_code==200
    assert put(client,key='PRIVATE-A').status_code==201
    client.post('/api/auth/logout')
    assert client.post('/api/auth/login',json={k:payload[k] for k in ('phone','password')}).status_code==200
    assert client.get('/api/documents/references').json()['references'][0]['ref_key']=='PRIVATE-A'
    assert verify(client,key='PRIVATE-A').json()['match'] is True


def test_different_member_cannot_read_another_account_ref(client):
    p1={'phone':'01712345678','password':'DemoPass123','otp':'1234'}
    p2={'phone':'01812345678','password':'DemoPass456','otp':'1234'}
    client.post('/api/auth/register',json=p1);assert put(client,key='PERSONAL').status_code==201
    client.post('/api/auth/logout')
    client.post('/api/auth/register',json=p2)
    assert verify(client,key='PERSONAL').status_code==404
    assert client.get('/api/documents/references').json()['references']==[]


def test_reference_validation(client):
    client.post('/api/auth/guest')
    assert put(client,acknowledge='false').status_code==422
    assert put(client,key='DEMO-MYKEY').status_code==409
    assert put(client,key='NOT/VALID').status_code==422
    assert put(client,key='MY-DEED-001').status_code==201
    assert put(client,key='MY-DEED-001').status_code==409
    response=client.post('/api/documents/references',data={'ref_key':'TRY-EXE','label':'Sample only','acknowledge':'true'},files={'file':('evil.exe',b'MZ....','application/octet-stream')})
    assert response.status_code==415


def test_prepared_original_demo_unchanged(client):
    client.post('/api/auth/guest')
    result=verify(client,key='DEMO-D4001')
    assert result.status_code==200
    assert result.json()['match'] is True
    assert result.json()['source']=='demo'
    assert result.json()['officially_verified'] is False
