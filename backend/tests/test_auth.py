from app.database import Member
from app.auth import PW_HASHER

def test_guest_access_to_every_demo_route(client):
    assert client.get('/api/plots').status_code==401
    r=client.post('/api/auth/guest');assert r.status_code==200
    assert r.json()['role']=='guest' and r.json()['full_access']
    assert 'httponly' in r.headers['set-cookie'].lower()
    for path in ['/api/stats','/api/plots','/api/plots/PLOT-004','/api/scenarios']:
        assert client.get(path).status_code==200,path
    assert client.get('/api/auth/me').json()['role']=='guest'
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/stats').status_code==401

def test_registration_password_login_no_login_otp(client,db):
    body=dict(phone='01712345678',password='DemoPass123',otp='1234')
    r=client.post('/api/auth/register',json=body)
    assert r.status_code==200,r.text
    assert r.json()['role']=='member'
    assert r.json()['phone_masked']=='017****5678'
    row=db.query(Member).filter(Member.phone=='01712345678').first()
    assert row and row.password_hash!='DemoPass123' and PW_HASHER.verify(row.password_hash,'DemoPass123')
    assert client.get('/api/plots').status_code==200
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/plots').status_code==401
    wrong=client.post('/api/auth/login',json={'phone':'01712345678','password':'wrongPassword1'})
    assert wrong.status_code==401
    login=client.post('/api/auth/login',json={'phone':'01712345678','password':'DemoPass123'})
    assert login.status_code==200 and login.json()['role']=='member'
    assert client.get('/api/plots').status_code==200

def test_cannot_register_twice(client):
    body={'phone':'01911112222','password':'Example123','otp':'1234'}
    assert client.post('/api/auth/register',json=body).status_code==200
    assert client.post('/api/auth/register',json=body).status_code==409

def test_invalid_otp_and_weak_password(client):
    assert client.post('/api/auth/register',json={'phone':'01712345678','password':'Example123','otp':'5555'}).status_code==400
    assert client.post('/api/auth/register',json={'phone':'01712345678','password':'passwordonly','otp':'1234'}).status_code==422
    assert client.post('/api/auth/register',json={'phone':'01212345678','password':'Example123','otp':'1234'}).status_code==422
    assert client.get('/api/plots').status_code==401

def test_bangla_phone(client):
    r=client.post('/api/auth/register',json={'phone':'০১৭১২৩৪৫৬৭৮','password':'Example123','otp':'1234'})
    assert r.status_code==200 and r.json()['phone_masked']=='017****5678'

def test_origin_check_on_credentials(client):
    r=client.post('/api/auth/guest',headers={'origin':'https://attacker.invalid'})
    assert r.status_code==403
