"""Transparent, explainable P3 checks on synthetic/authorized sample records.

No claim is a legal determination or a statistical fraud likelihood.
"""
from collections import defaultdict
from sqlalchemy.orm import Session
from .database import Plot,Sale,TrustedDocument
from .schemas import Claim

WEIGHTS={'double_sale':45,'ownership_gap':22,'mutation_mismatch':20,'rapid_transfer':13,'reference_mismatch':30,'identifier_mismatch':18}
LEVELS={'double_sale':'critical','ownership_gap':'high','mutation_mismatch':'medium','rapid_transfer':'low','reference_mismatch':'high','identifier_mismatch':'medium'}
TEXT={
 'double_sale':('Conflicting buyer claims on an overlapping land share','একই জমির আংশিক বা পূর্ণ অংশে ভিন্ন ক্রেতার দাবি'),
 'ownership_gap':('Missing link in the available ownership chain','নমুনা মালিকানা হস্তান্তরের ধারায় সংযোগ অনুপস্থিত'),
 'mutation_mismatch':('Buyer differs from completed mutation owner','সম্পন্ন নামজারির মালিক ও দলিলের ক্রেতা আলাদা'),
 'rapid_transfer':('Overlapping claims within 30 days','৩০ দিনের মধ্যে একই অংশ নিয়ে পরস্পরবিরোধী দাবি'),
 'reference_mismatch':('Document does not match demo trusted reference hash','সংরক্ষিত নমুনা রেফারেন্সের Hash মিলছে না'),
 'identifier_mismatch':('Document identifiers differ from the sample plot index','দলিলের পরিচিতি নমুনা রেকর্ডের সঙ্গে মেলে না'),
}
def norm(x):return ' '.join((x or '').translate(str.maketrans('০১২৩৪৫৬৭৮৯','0123456789')).casefold().split())
def asdict_sale(s:Sale):return dict(plot_id=s.plot_id,deed_no=s.deed_no,seller=s.seller,buyer=s.buyer,portion_code=s.portion_code,share_start=s.share_start,share_end=s.share_end,deed_date=s.deed_date,mutation_owner=s.mutation_owner,mutation_status=s.mutation_status,previous_deed=s.previous_deed,source='synthetic_registry')
def asdict_claim(c:Claim):return dict(**c.model_dump(exclude={'ref_key','sha256'}),source='submitted')
def overlap(a,b):
    if a['plot_id']!=b['plot_id'] or norm(a['portion_code'])!=norm(b['portion_code']):return 0.
    return max(0.,min(a['share_end'],b['share_end'])-max(a['share_start'],b['share_start']))
def assess(db:Session,claims:list[Claim]):
    ids=sorted({c.plot_id for c in claims})
    plots={p.id:p for p in db.query(Plot).filter(Plot.id.in_(ids)).all()}
    originals=db.query(Sale).filter(Sale.plot_id.in_(ids)).all()
    history=[asdict_sale(x) for x in originals]
    submitted=[asdict_claim(x) for x in claims]
    alerts=[];unique=set()
    def add(kind,en,bn,evidence,rule,details=None):
        key=(kind,tuple(sorted(map(str,evidence))))
        if key in unique:return
        unique.add(key)
        alerts.append(dict(id=f'{kind}-{len(alerts)+1}',type=kind,severity=LEVELS[kind],title_en=TEXT[kind][0],title_bn=TEXT[kind][1],detail_en=en,detail_bn=bn,evidence=evidence,rule=rule,weight=WEIGHTS[kind],**(details or {})))
    # Normalize same deed claims by preferring submitted record; retains known records for comparison.
    records={r['deed_no']:r for r in history}
    records.update({r['deed_no']:r for r in submitted})
    docs=list(records.values());docs.sort(key=lambda x:(x['deed_date'],x['deed_no']))
    for i,a in enumerate(docs):
        for b in docs[i+1:]:
            share=overlap(a,b)
            if share<=1e-9:continue
            # A single dag/plot identifier is never enough: exact portion + intersecting shares required.
            if norm(a['seller'])==norm(b['seller']) and norm(a['buyer'])!=norm(b['buyer']):
                p=plots.get(a['plot_id']);amount=round(share*p.area_decimal,3) if p else None
                detail=f"{a['deed_no']} and {b['deed_no']} claim an overlapping {share*100:.1f}% of portion {a['portion_code']} for different buyers from the same seller."
                add('double_sale',detail,f"{a['deed_no']} এবং {b['deed_no']} একই অংশের {share*100:.1f}% নিয়ে ভিন্ন ক্রেতার দাবি করছে।",[a['deed_no'],b['deed_no']],'R01_plot_portion_share_intersection',{'overlap_fraction':round(share,4),'overlap_decimal':amount})
            if abs((a['deed_date']-b['deed_date']).days)<=30 and norm(a['buyer'])!=norm(b['buyer']):
                add('rapid_transfer',f"Overlapping deeds {a['deed_no']} and {b['deed_no']} are within 30 days; verify whether they are legally distinct transactions.",f"একই অংশের {a['deed_no']} ও {b['deed_no']} ৩০ দিনের মধ্যে হয়েছে।",[a['deed_no'],b['deed_no']],'R04_overlap_within_30_days')
    for a in submitted:
        p=plots.get(a['plot_id'])
        if p:
            wrong=[]
            for key,variants in [('district',[p.district,p.district_bn]),('mouza',[p.mouza,p.mouza_bn]),('khatian',[p.khatian]),('dag',[p.dag])]:
                value=a.get(key)
                if value and norm(value) not in {norm(v) for v in variants}:wrong.append(f'{key}: {value} != {variants[0]}')
            if wrong:add('identifier_mismatch',f"Deed {a['deed_no']} differs from sample plot index: {'; '.join(wrong)}",f"দলিল {a['deed_no']}-এর জমির পরিচিতি নমুনা রেকর্ডের সঙ্গে মেলে না: {'; '.join(wrong)}",[a['deed_no'],a['plot_id']],'R06_record_identifier')
        if a['mutation_status']=='completed' and a.get('mutation_owner') and norm(a['buyer'])!=norm(a['mutation_owner']):
            add('mutation_mismatch',f"Buyer {a['buyer']} vs completed mutation owner {a['mutation_owner']}",f"ক্রেতা {a['buyer']} কিন্তু সম্পন্ন নামজারির মালিক {a['mutation_owner']}",[a['deed_no']],'R03_completed_mutation_buyer')
        # Ownership chain heuristic: look at the most recent PRECEDING overlapping sale in
        # the available sample registry, and check whether its buyer is this seller.
        prior=[r for r in history if r['deed_no']!=a['deed_no'] and r['deed_date']<a['deed_date'] and overlap(r,a)>0]
        if prior:
            latest=max(prior,key=lambda r:r['deed_date'])
            if norm(latest['buyer'])!=norm(a['seller']) and not (a.get('previous_deed') and a['previous_deed']==latest['deed_no'] and norm(a['seller'])==norm(latest['buyer'])):
                add('ownership_gap',f"Last available overlapping deed {latest['deed_no']} names buyer {latest['buyer']}, but seller of {a['deed_no']} is {a['seller']}. An omitted transfer/inheritance may explain this.",f"আগের {latest['deed_no']} দলিলে ক্রেতা {latest['buyer']}; নতুন {a['deed_no']}-এর বিক্রেতা {a['seller']}। অসম্পূর্ণ রেকর্ডও কারণ হতে পারে।",[latest['deed_no'],a['deed_no']],'R02_missing_chain_link')
    for c in claims:
        if c.ref_key and c.sha256:
            ref=db.get(TrustedDocument,c.ref_key)
            if ref and ref.deed_no==c.deed_no and c.sha256!=ref.sha256:
                add('reference_mismatch',f"SHA-256 differs from synthetic baseline {c.ref_key}; does not by itself prove a forged document.",f"নমুনা {c.ref_key}-এর সংরক্ষিত Hash ও দেওয়া Hash আলাদা। একা এটি জালিয়াতির প্রমাণ নয়।",[c.deed_no,c.ref_key],'R05_byte_hash_known_reference')
    score=min(100,sum(WEIGHTS[k] for k in {x['type'] for x in alerts}))
    missing=[x for x in ids if x not in plots]
    status='insufficient_reference' if missing else 'review_required' if alerts else 'no_alerts_in_sample'
    graph_nodes=set();graph_edges=[]
    for d in docs:
        graph_nodes.update([d['seller'],d['buyer']]);graph_edges.append(dict(from_name=d['seller'],to_name=d['buyer'],deed_no=d['deed_no'],date=d['deed_date'].isoformat(),plot_id=d['plot_id'],portion=d['portion_code'],source=d['source']))
    timeline=[{k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in d.items()} for d in docs]
    return dict(score=None if missing else score,level='unknown' if missing else 'high' if score>=60 else 'medium' if score>=25 else 'low',status=status,alerts=alerts,plot_ids=ids,unknown_plot_ids=missing,timeline=timeline,ownership_graph=dict(nodes=sorted(graph_nodes),edges=graph_edges),risk_components=[dict(type=k,weight=WEIGHTS[k]) for k in sorted({a['type'] for a in alerts})],synthetic_data=True,disclaimer_en='Synthetic screening only. No official data integration; alerts are not legal proof. Score is NOT a fraud probability.',disclaimer_bn='কৃত্রিম নমুনা যাচাই। সরকারি রেকর্ড সংযুক্ত নয়; সতর্কতা আইনগত প্রমাণ নয় এবং স্কোর জালিয়াতির সম্ভাবনার শতাংশ নয়।')
