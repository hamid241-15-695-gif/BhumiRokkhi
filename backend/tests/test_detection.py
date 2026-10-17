from app.engine import assess,overlap
from app.schemas import Claim
from app.scenarios import SCENARIOS


def scenario(id):return next(x for x in SCENARIOS if x['id']==id)

def test_prepared_cases(client):
    client.post('/api/auth/guest')
    expected={'clean':0,'double_sale':80,'mutation':20,'integrity':30,'partial_overlap':80,'chain_gap':22}
    for id,score in expected.items():
        r=client.post('/api/assess',json={'claims':scenario(id)['claims']})
        assert r.status_code==200,(id,r.text)
        assert r.json()['score']==score,(id,r.json())
        assert 'ownership_graph' in r.json() and 'timeline' in r.json()

def test_partial_double_overlap_area(db):
    r=assess(db,[Claim(**x) for x in scenario('partial_overlap')['claims']])
    overlaps=[x for x in r['alerts'] if x['type']=='double_sale' and set(x['evidence'])=={'D-5101','D-5102'}]
    assert len(overlaps)==1
    assert overlaps[0]['overlap_fraction']==0.2
    assert overlaps[0]['overlap_decimal']==4.0

def test_no_overlap_when_distinct_portion(db):
    fields=dict(scenario('partial_overlap')['claims'][0]);fields['portion_code']='OTHER-SECTION';fields['deed_no']='D-5990'
    r=assess(db,[Claim(**fields)])
    assert not any(x['type']=='double_sale' for x in r['alerts'])

def test_exact_share_edge_touch_not_overlap():
    a=dict(plot_id='PLOT-001',portion_code='SECTION-A',share_start=0.,share_end=.5)
    b=dict(plot_id='PLOT-001',portion_code='SECTION-A',share_start=.5,share_end=1.)
    assert overlap(a,b)==0

def test_unknown_plot_not_falsely_cleared(db):
    fields={**scenario('clean')['claims'][0],'plot_id':'PLOT-UNKNOWN'}
    r=assess(db,[Claim(**fields)])
    assert r['score'] is None and r['status']=='insufficient_reference'

def test_identifier_warning(db):
    fields={**scenario('clean')['claims'][0],'khatian':'999999'}
    r=assess(db,[Claim(**fields)])
    assert r['score']==18 and r['alerts'][0]['type']=='identifier_mismatch'

def test_known_reference_matches(db):
    from app.database import TrustedDocument
    baseline=db.get(TrustedDocument,'DEMO-D4001').sha256
    fields={**scenario('integrity')['claims'][0],'sha256':baseline}
    r=assess(db,[Claim(**fields)])
    assert r['score']==0

def test_missing_reference_does_not_claim_integrity(db):
    fields={**scenario('integrity')['claims'][0],'ref_key':'UNREGISTERED'}
    r=assess(db,[Claim(**fields)])
    assert 'reference_mismatch' not in {x['type'] for x in r['alerts']}

def test_guest_can_assess(client):
    client.post('/api/auth/guest')
    r=client.post('/api/assess',json={'claims':scenario('double_sale')['claims']})
    assert r.status_code==200 and r.json()['score']==80

def test_invalid_share_rejected(client):
    client.post('/api/auth/guest')
    fields={**scenario('clean')['claims'][0],'share_start':0.9,'share_end':0.1}
    assert client.post('/api/assess',json={'claims':[fields]}).status_code==422
