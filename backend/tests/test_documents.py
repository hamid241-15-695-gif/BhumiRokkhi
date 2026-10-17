from pathlib import Path
SAMPLES=Path(__file__).resolve().parents[1]/'samples'
def upload(client,path):
    with open(SAMPLES/path,'rb') as f:return client.post('/api/documents/extract',files={'file':(path,f,'application/pdf')})
def test_guest_upload_extracts_fields(client):
    client.post('/api/auth/guest')
    result=upload(client,'D-4001_reference.pdf')
    assert result.status_code==200
    data=result.json()
    assert data['fields']['deed_no']=='D-4001'
    assert data['fields']['buyer']=='Tania Begum'
    assert data['stored'] is False

def test_reference_exact_and_changed(client):
    client.post('/api/auth/guest')
    for name,match in [('D-4001_reference.pdf',True),('D-4001_changed_version.pdf',False)]:
        with open(SAMPLES/name,'rb') as f:
            r=client.post('/api/documents/reference-check?ref_key=DEMO-D4001',files={'file':(name,f,'application/pdf')})
        assert r.status_code==200 and r.json()['match'] is match

def test_same_deed_version_comparison(client):
    client.post('/api/auth/guest')
    with open(SAMPLES/'D-4001_reference.pdf','rb') as f1,open(SAMPLES/'D-4001_changed_version.pdf','rb') as f2:
        response=client.post('/api/documents/compare',files={'first':('D-4001_reference.pdf',f1,'application/pdf'),'second':('D-4001_changed_version.pdf',f2,'application/pdf')})
    assert response.status_code==200
    info=response.json()['comparison']
    assert info['same_deed_number'] is True
    assert info['sha256_equal'] is False
    assert any(d['field']=='buyer' for d in info['field_differences'])

def test_two_different_deeds_not_called_forged(client):
    client.post('/api/auth/guest')
    with open(SAMPLES/'D-4001_reference.pdf','rb') as f1,open(SAMPLES/'D-4002_other_sale.pdf','rb') as f2:
        r=client.post('/api/documents/compare',files={'first':('D-4001_reference.pdf',f1,'application/pdf'),'second':('D-4002_other_sale.pdf',f2,'application/pdf')})
    assert r.status_code==200
    result=r.json()['comparison']
    assert result['comparison_type']=='different_deeds'
    assert 'NORMAL' in result['warning_en']

def test_unsupported_upload_and_missing_auth(client):
    with open(SAMPLES/'D-4001_reference.pdf','rb') as f:
        assert client.post('/api/documents/extract',files={'file':('x.pdf',f,'application/pdf')}).status_code==401
    client.post('/api/auth/guest')
    assert client.post('/api/documents/extract',files={'file':('x.exe',b'bad file','application/octet-stream')}).status_code==415

def test_unknown_reference_denied(client):
    client.post('/api/auth/guest')
    with open(SAMPLES/'D-4001_reference.pdf','rb') as f:
        r=client.post('/api/documents/reference-check?ref_key=NOT-A-REF',files={'file':('x.pdf',f,'application/pdf')})
    assert r.status_code==404
