"""Constrained in-memory PDF/image parsing and precise field-by-field comparisons.

Not an AI forgery classifier. Different documents normally have different SHA-256.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from fastapi import HTTPException,UploadFile

MAX_BYTES=8*1024*1024
FIELDS={
 'plot_id':['Plot ID','প্লট আইডি'],'deed_no':['Deed No','দলিল নম্বর'],
 'seller':['Seller','বিক্রেতা'],'buyer':['Buyer','ক্রেতা'],
 'district':['District','জেলা'],'mouza':['Mouza','মৌজা'],
 'khatian':['Khatian','খতিয়ান','খতিয়ান'],'dag':['Dag','দাগ'],
 'portion_code':['Portion','Portion Code','জমির অংশ'],
 'share_start':['Share Start','অংশের শুরু'],'share_end':['Share End','অংশের শেষ'],
 'deed_date':['Deed Date','দলিলের তারিখ'],'mutation_owner':['Mutation Owner','নামজারির মালিক'],
 'mutation_status':['Mutation Status','নামজারির অবস্থা'],
 'previous_deed':['Previous Deed','আগের দলিল'],
}
def parse_text(content:str):
    content=content.translate(str.maketrans('০১২৩৪৫৬৭৮৯','0123456789'))
    data={}
    for field,labels in FIELDS.items():
        for label in labels:
            m=re.search(r'(?im)^\s*'+re.escape(label)+r'\s*[:：-]\s*([^\r\n]+)',content)
            if m:data[field]=m.group(1).strip()[:150];break
    return data
async def read_document(file:UploadFile):
    name=Path(file.filename or 'file').name[:150];ext=Path(name).suffix.lower()
    if ext not in {'.pdf','.jpg','.jpeg','.png'}:raise HTTPException(415,'Supported: PDF, PNG, JPG')
    raw=await file.read(MAX_BYTES+1);await file.close()
    if len(raw)>MAX_BYTES:raise HTTPException(413,'Maximum 8 MB')
    if len(raw)<8:raise HTTPException(422,'Invalid or empty document')
    text='';method='manual';notes=[]
    try:
        if ext=='.pdf':
            import fitz
            doc=fitz.open(stream=raw,filetype='pdf')
            if doc.page_count>5:raise HTTPException(422,'Up to 5 PDF pages')
            text='\n'.join(p.get_text() for p in doc)
            if text.strip():method='embedded_pdf_text'
            else:
                from PIL import Image
                import pytesseract
                for p in doc:
                    pix=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False)
                    img=Image.open(BytesIO(pix.tobytes('png')))
                    try:text+='\n'+pytesseract.image_to_string(img,lang='ben+eng')
                    except pytesseract.TesseractError:text+='\n'+pytesseract.image_to_string(img,lang='eng')
                method='tesseract_ocr'
        else:
            import pytesseract
            from PIL import Image
            img=Image.open(BytesIO(raw));img.verify();img=Image.open(BytesIO(raw))
            if img.width*img.height>24_000_000:raise HTTPException(422,'Image too large')
            try:text=pytesseract.image_to_string(img,lang='ben+eng')
            except pytesseract.TesseractError:text=pytesseract.image_to_string(img,lang='eng')
            method='tesseract_ocr'
    except HTTPException:raise
    except Exception:notes.append('Parsing unavailable; fill fields manually')
    fields=parse_text(text)
    notes.append('Review OCR fields manually before any assessment')
    return dict(filename=name,sha256=sha256(raw).hexdigest(),fields=fields,method=method,notes=notes,text_excerpt=text[:1300],stored=False)
def compare(extracted_a:dict,extracted_b:dict):
    a=extracted_a['fields'];b=extracted_b['fields']
    same_deed=bool(a.get('deed_no') and a.get('deed_no')==b.get('deed_no'))
    diff=[dict(field=k,first=a.get(k),second=b.get(k)) for k in sorted(set(a)|set(b)) if a.get(k) and b.get(k) and a[k].strip().casefold()!=b[k].strip().casefold()]
    return dict(same_deed_number=same_deed,sha256_equal=extracted_a['sha256']==extracted_b['sha256'],field_differences=diff,comparison_type='same_deed_versions' if same_deed else 'different_deeds',warning_en='Differences on same deed number need verification against a trusted original' if same_deed else 'These are different deeds; different hashes are NORMAL and not evidence of forgery',warning_bn='একই দলিল নম্বরের সংস্করণে পার্থক্য যাচাই প্রয়োজন' if same_deed else 'এগুলো আলাদা দলিল; Hash আলাদা হওয়া স্বাভাবিক, জালিয়াতির প্রমাণ নয়')
