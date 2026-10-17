import pytest
from datetime import date
from hashlib import sha256
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base,Plot,Sale,TrustedDocument,PLOTS,SALES
from app.auth import db_session,ATTEMPTS
from app.main import app
@pytest.fixture
def db():
    eng=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False});Base.metadata.create_all(eng)
    maker=sessionmaker(bind=eng,expire_on_commit=False);session=maker()
    for p in PLOTS:session.add(Plot(id=p[0],district=p[1],district_bn=p[2],upazila=p[3],upazila_bn=p[4],mouza=p[5],mouza_bn=p[6],khatian=p[7],dag=p[8],area_decimal=p[9],lat=p[10],lng=p[11]))
    for s in SALES:session.add(Sale(plot_id=s[0],deed_no=s[1],seller=s[2],buyer=s[3],portion_code=s[4],share_start=s[5],share_end=s[6],deed_date=date.fromisoformat(s[7]),mutation_owner=s[8],mutation_status=s[9],previous_deed=s[10]))
    sample=Path(__file__).resolve().parents[1]/'samples'/'D-4001_reference.pdf'
    session.add(TrustedDocument(ref_key='DEMO-D4001',sha256=sha256(sample.read_bytes()).hexdigest(),deed_no='D-4001',description='synthetic'))
    session.commit();yield session;session.close();eng.dispose()
@pytest.fixture
def client(db):
    ATTEMPTS.clear()
    def override():yield db
    app.dependency_overrides[db_session]=override
    with TestClient(app) as c:yield c
    app.dependency_overrides.clear();ATTEMPTS.clear()
