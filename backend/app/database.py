"""Version 3 synthetic land database and DEMO identity accounts.

Separate Docker Compose project and volume from previous versions.
"""
import os
from datetime import date,datetime,timezone
from sqlalchemy import Boolean,Date,DateTime,Float,ForeignKey,Integer,String,Text,UniqueConstraint,create_engine
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship,sessionmaker

DB_URL=os.getenv('DATABASE_URL','sqlite:///./bhumi_v3.db')
engine=create_engine(DB_URL,pool_pre_ping=True,connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
class Base(DeclarativeBase):pass
class Plot(Base):
    __tablename__='plots'
    id:Mapped[str]=mapped_column(String(32),primary_key=True)
    district:Mapped[str]=mapped_column(String(90));district_bn:Mapped[str]=mapped_column(String(90))
    upazila:Mapped[str]=mapped_column(String(90));upazila_bn:Mapped[str]=mapped_column(String(90))
    mouza:Mapped[str]=mapped_column(String(90));mouza_bn:Mapped[str]=mapped_column(String(90))
    khatian:Mapped[str]=mapped_column(String(60));dag:Mapped[str]=mapped_column(String(60))
    area_decimal:Mapped[float]=mapped_column(Float)
    lat:Mapped[float|None]=mapped_column(Float,nullable=True)
    lng:Mapped[float|None]=mapped_column(Float,nullable=True)
    sales:Mapped[list['Sale']]=relationship(back_populates='plot')
class Sale(Base):
    __tablename__='sales'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    plot_id:Mapped[str]=mapped_column(ForeignKey('plots.id'))
    deed_no:Mapped[str]=mapped_column(String(60),unique=True)
    seller:Mapped[str]=mapped_column(String(150));buyer:Mapped[str]=mapped_column(String(150))
    portion_code:Mapped[str]=mapped_column(String(60))
    share_start:Mapped[float]=mapped_column(Float);share_end:Mapped[float]=mapped_column(Float)
    deed_date:Mapped[date]=mapped_column(Date)
    mutation_owner:Mapped[str|None]=mapped_column(String(150),nullable=True)
    mutation_status:Mapped[str]=mapped_column(String(24),default='unknown')
    previous_deed:Mapped[str|None]=mapped_column(String(60),nullable=True)
    plot:Mapped['Plot']=relationship(back_populates='sales')
class TrustedDocument(Base):
    __tablename__='trusted_documents'
    ref_key:Mapped[str]=mapped_column(String(100),primary_key=True)
    sha256:Mapped[str]=mapped_column(String(64))
    deed_no:Mapped[str]=mapped_column(String(60));description:Mapped[str]=mapped_column(Text)
class SavedReference(Base):
    """User-designated sample baseline; NOT a certified/official or government-verified deed.

    Each member owns a namespace; guest references belong to a single session.
    Only hashes + metadata are stored, never document bytes.
    """
    __tablename__='saved_references'
    __table_args__=(UniqueConstraint('owner_key','ref_key',name='uq_saved_ref_owner_key'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    owner_key:Mapped[str]=mapped_column(String(100),index=True)
    ref_key:Mapped[str]=mapped_column(String(60),index=True)
    sha256:Mapped[str]=mapped_column(String(64))
    deed_no:Mapped[str]=mapped_column(String(60),default='')
    label:Mapped[str]=mapped_column(String(120))
    file_name:Mapped[str]=mapped_column(String(150))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Member(Base):
    __tablename__='members'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    phone:Mapped[str]=mapped_column(String(11),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class AuthSession(Base):
    __tablename__='auth_sessions'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    member_id:Mapped[int|None]=mapped_column(ForeignKey('members.id'),nullable=True)
    role:Mapped[str]=mapped_column(String(16))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    revoked:Mapped[bool]=mapped_column(Boolean,default=False)
    member:Mapped['Member|None']=relationship()

PLOTS=[
 ('PLOT-001','Dhaka','ঢাকা','Savar','সাভার','Birulia','বিরুলিয়া','1042','508',18.,23.867,90.263),
 ('PLOT-002','Gazipur','গাজীপুর','Sreepur','শ্রীপুর','Barmi','বরমী','2081','224',30.,24.167,90.444),
 ('PLOT-003','Cumilla','কুমিল্লা','Chandina','চান্দিনা','Madhaiya','মাধাইয়া','3309','617',24.,23.478,91.008),
 ('PLOT-004','Khulna','খুলনা','Dumuria','ডুমুরিয়া','Raghunathpur','রঘুনাথপুর','1160','919',15.,22.806,89.455),
 ('PLOT-005','Rajshahi','রাজশাহী','Paba','পবা','Hargram','হরগ্রাম','5100','401',20.,24.400,88.600),
]
SALES=[
 ('PLOT-001','D-1001','Karim Ali','Rahim Uddin','SECTION-A',0.,.6,'2025-05-10','Rahim Uddin','completed',None),
 ('PLOT-001','D-1002','Karim Ali','Salma Akter','SECTION-A',0.,.6,'2025-05-25',None,'pending',None),
 ('PLOT-002','D-2001','Anis Rahman','Nadia Karim','SECTION-B',0.,1.,'2025-04-12','Nadia Karim','completed',None),
 ('PLOT-003','D-3001','Sujon Ahmed','Farhan Islam','SECTION-C',0.,1.,'2025-06-01','Maya Begum','completed',None),
 ('PLOT-004','D-4001','Mizan Hossain','Tania Begum','SECTION-D',0.,1.,'2025-07-05','Tania Begum','completed',None),
 ('PLOT-005','D-5001','Aminul Islam','Borna Begum','SECTION-E',0.,.4,'2025-01-15','Borna Begum','completed',None),
 ('PLOT-005','D-5002','Borna Begum','Chandan Mia','SECTION-E',0.,.4,'2025-06-20','Chandan Mia','completed','D-5001'),
]
def seed():
    from pathlib import Path
    from hashlib import sha256
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(Plot).first():
            for p in PLOTS:db.add(Plot(id=p[0],district=p[1],district_bn=p[2],upazila=p[3],upazila_bn=p[4],mouza=p[5],mouza_bn=p[6],khatian=p[7],dag=p[8],area_decimal=p[9],lat=p[10],lng=p[11]))
            for s in SALES:db.add(Sale(plot_id=s[0],deed_no=s[1],seller=s[2],buyer=s[3],portion_code=s[4],share_start=s[5],share_end=s[6],deed_date=date.fromisoformat(s[7]),mutation_owner=s[8],mutation_status=s[9],previous_deed=s[10]))
        # Baseline is the byte-exact hash of the included synthetic reference, not a forged certificate.
        doc=Path(__file__).parent.parent/'samples'/'D-4001_reference.pdf'
        if doc.exists() and not db.get(TrustedDocument,'DEMO-D4001'):
            db.add(TrustedDocument(ref_key='DEMO-D4001',sha256=sha256(doc.read_bytes()).hexdigest(),deed_no='D-4001',description='Byte-identical synthetic reference PDF (NOT government authenticated)'))
        db.commit()
