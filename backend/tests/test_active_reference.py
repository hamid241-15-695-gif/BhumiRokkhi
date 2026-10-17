"""The new beginner-friendly two-upload flow; no reference key/name/select input."""
from pathlib import Path
from hashlib import sha256
SAMPLES=Path(__file__).resolve().parents[1]/'samples'
GOOD=SAMPLES/'D-4001_reference.pdf'
CHANGED=SAMPLES/'D-4001_changed_version.pdf'


def save(c,p=GOOD, consent='true'):
    with p.open('rb') as f:
        return c.post('/api/documents/active-reference',data={'acknowledge':consent},
            files={'file':(p.name,f,'application/pdf')})


def check(c,p=GOOD):
    with p.open('rb') as f:
        return c.post('/api/documents/active-reference-check',files={'file':(p.name,f,'application/pdf')})


def test_auth_required_for_new_workflow(client):
    assert client.get('/api/documents/active-reference').status_code==401
    assert save(client).status_code==401
    assert check(client).status_code==401


def test_missing_sample_blocks_verification(client):
    client.post('/api/auth/guest')
    assert client.get('/api/documents/active-reference').json()['reference'] is None
    r=check(client)
    assert r.status_code==409
    assert 'Save your own sample' in r.json()['detail']


def test_guest_save_then_match_mismatch(client):
    client.post('/api/auth/guest')
    created=save(client)
    assert created.status_code==201,created.text
    ref=created.json()['reference']
    assert ref['sha256']==sha256(GOOD.read_bytes()).hexdigest()
    assert ref['file_name']==GOOD.name
    assert ref['officially_verified'] is False
    assert created.json()['document_stored'] is False
    assert client.get('/api/documents/active-reference').json()['reference']['file_name']==GOOD.name
    same=check(client);assert same.status_code==200
    assert same.json()['match'] is True
    assert same.json()['reference_sha256']==same.json()['submitted_sha256']
    changed=check(client,CHANGED);assert changed.status_code==200
    assert changed.json()['match'] is False
    assert changed.json()['officially_verified'] is False


def test_new_original_replaces_previous(client):
    client.post('/api/auth/guest')
    assert save(client).status_code==201
    newer=save(client,CHANGED)
    assert newer.status_code==201,newer.text
    assert newer.json()['reference']['file_name']==CHANGED.name
    assert len(client.get('/api/documents/references').json()['references'])==1
    assert check(client,CHANGED).json()['match'] is True
    assert check(client,GOOD).json()['match'] is False


def test_guest_logout_isolation(client):
    client.post('/api/auth/guest')
    assert save(client).status_code==201
    assert client.post('/api/auth/logout').status_code==200
    client.post('/api/auth/guest')
    assert client.get('/api/documents/active-reference').json()['reference'] is None
    assert check(client).status_code==409


def test_member_relogin_persists_reference(client):
    credentials={'phone':'01712345678','password':'DemoPass123','otp':'1234'}
    assert client.post('/api/auth/register',json=credentials).status_code==200
    assert save(client).status_code==201
    client.post('/api/auth/logout')
    assert client.post('/api/auth/login',json={k:credentials[k] for k in ('phone','password')}).status_code==200
    assert check(client).json()['match'] is True


def test_member_cannot_access_other_member_reference(client):
    assert client.post('/api/auth/register',json={'phone':'01712345678','password':'DemoPass123','otp':'1234'}).status_code==200
    assert save(client).status_code==201
    client.post('/api/auth/logout')
    assert client.post('/api/auth/register',json={'phone':'01812345678','password':'DemoPass123','otp':'1234'}).status_code==200
    assert client.get('/api/documents/active-reference').json()['reference'] is None
    assert check(client).status_code==409


def test_consent_and_invalid_upload(client):
    client.post('/api/auth/guest')
    assert save(client,consent='false').status_code==422
    assert client.get('/api/documents/active-reference').json()['reference'] is None
    r=client.post('/api/documents/active-reference',data={'acknowledge':'true'},files={'file':('invalid.exe',b'unknown','application/octet-stream')})
    assert r.status_code==415
    assert client.get('/api/documents/active-reference').json()['reference'] is None
