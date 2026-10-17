'use client';
import {useEffect,useState,type FormEvent} from 'react';
import {Hash,ShieldCheck,UploadCloud,Save,SearchCheck,Info,CheckCircle2,AlertTriangle,FileText} from 'lucide-react';
import FilePicker from './FilePicker';
import {useLanguage} from './LanguageProvider';
import {api,type ReferenceCheck,type SavedReference} from '@/lib/api';

type ActiveReferenceResponse={reference:SavedReference|null};
type UploadedBaseline={reference:SavedReference;document_stored:false;replaced:boolean};

function localizedError(e:unknown,lang:'bn'|'en',fallback:string){
  const message=e instanceof Error?e.message:String(e);
  if(lang==='en')return message;
  if(message.includes('Maximum 8 MB'))return 'ফাইলের আকার সর্বোচ্চ ৮ এমবি হতে পারবে।';
  if(message.includes('Supported:')||message.includes('Only'))return 'শুধু PDF, JPG ও PNG ফাইল আপলোড করা যাবে।';
  if(message.includes('authorized demo'))return 'শুধু নিজের বা অনুমোদিত নমুনা দলিল ব্যবহার করুন।';
  if(message.includes('Save your own sample'))return 'যাচাইয়ের আগে উপরের নিজের নমুনা দলিলটি সংরক্ষণ করুন।';
  return fallback;
}

export default function ReferenceManager(){
  const {lang,t}=useLanguage();
  const [baseline,setBaseline]=useState<SavedReference|null>(null);
  const [initialLoading,setInitialLoading]=useState(true);
  const [original,setOriginal]=useState<File|null>(null);
  const [consent,setConsent]=useState(false);
  const [saving,setSaving]=useState(false);
  const [saveError,setSaveError]=useState('');
  const [saveSuccess,setSaveSuccess]=useState(false);
  const [candidate,setCandidate]=useState<File|null>(null);
  const [checking,setChecking]=useState(false);
  const [verifyError,setVerifyError]=useState('');
  const [outcome,setOutcome]=useState<ReferenceCheck|null>(null);

  useEffect(()=>{
    let mounted=true;
    api<ActiveReferenceResponse>('/api/documents/active-reference')
      .then(data=>{if(mounted)setBaseline(data.reference)})
      .catch(()=>{if(mounted)setSaveError(t('refRegisterError'))})
      .finally(()=>{if(mounted)setInitialLoading(false)});
    return()=>{mounted=false};
  },[]);

  async function saveSample(e:FormEvent){
    e.preventDefault();setSaveError('');setSaveSuccess(false);
    if(!original||!consent){setSaveError(t('refFileRequired'));return}
    setSaving(true);
    try{
      const form=new FormData();form.append('file',original);form.append('acknowledge','true');
      const response=await api<UploadedBaseline>('/api/documents/active-reference',{method:'POST',body:form});
      setBaseline(response.reference);
      setSaveSuccess(true);
      setOriginal(null);
      setCandidate(null); // do not accidentally verify an older file against the new sample
      setOutcome(null);
      setVerifyError('');
    }catch(error){setSaveError(localizedError(error,lang,t('refRegisterError')))}finally{setSaving(false)}
  }

  async function verifyUploaded(){
    setVerifyError('');setOutcome(null);
    if(!baseline||!candidate){setVerifyError(t('refSelectRequired'));return}
    setChecking(true);
    try{
      const form=new FormData();form.append('file',candidate);
      const result=await api<ReferenceCheck>('/api/documents/active-reference-check',{method:'POST',body:form});
      setOutcome(result);
    }catch(error){setVerifyError(localizedError(error,lang,t('refVerifyError')))}finally{setChecking(false)}
  }

  return <div className="panel panel-pad" id="reference-manager">
    <h2 className="font-extrabold text-lg text-ink flex gap-2 items-center"><Hash size={21} className="text-forest"/>{t('referenceCheck')}</h2>
    <p className="text-sm muted mt-3 leading-6">{t('referenceHelp')}</p>
    <div className="rounded-xl bg-[#eef7f2] p-4 mt-5 flex gap-3 items-start"><Info size={18} className="shrink-0 text-forest mt-0.5"/><div className="text-xs text-[#436a5d] leading-6"><p>{t('refCreateSteps')}</p><p className="mt-1">{t('refNoAuthority')}</p></div></div>

    <h3 className="font-extrabold text-ink mt-7 mb-4 flex gap-2 items-center"><Save size={18} className="text-forest"/>{t('referenceTitle')}</h3>
    <form onSubmit={e=>void saveSample(e)} className="space-y-4">
      <FilePicker label={t('pickOriginal')} value={original} onChange={f=>{setOriginal(f);setSaveSuccess(false)}} disabled={saving}/>
      <label className="flex gap-3 items-start text-sm cursor-pointer"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)} className="mt-1 accent-[#106b56]" required disabled={saving}/><span>{t('refConsent')}</span></label>
      <button type="submit" disabled={saving||!original||!consent} className="btn btn-primary w-full"><ShieldCheck size={17}/>{saving?t('refSaving'):t('refSave')}</button>
    </form>
    {saveError&&<p role="alert" className="demo-box mt-4">{saveError}</p>}
    {saveSuccess&&<p role="status" className="text-sm text-forest font-bold mt-4 flex items-center gap-2"><CheckCircle2 size={18}/>{t('refSaved')}</p>}
    {!initialLoading&&(baseline?<div className="mt-4 p-4 bg-[#eaf8f0] border border-[#c7e6d5] rounded-xl break-words">
      <p className="text-xs font-bold text-forest flex gap-2 items-center"><FileText size={16}/>{t('refCurrent')}</p>
      <p className="text-sm font-bold text-ink mt-2 break-all">{baseline.file_name}</p>
      <p className="text-xs muted mt-2">{t('refReplaceHelp')}</p>
    </div>:<p className="mt-4 text-xs muted">{t('refNoSaved')}</p>)}

    <div className="border-t border-[#dce9e1] mt-7 pt-6">
      <h3 className="font-extrabold text-ink flex items-center gap-2"><SearchCheck size={18} className="text-forest"/>{t('refVerification')}</h3>
      <div className="mt-4"><FilePicker label={t('refUploaded')} value={candidate} onChange={f=>{setCandidate(f);setOutcome(null)}} disabled={checking}/></div>
      <button type="button" disabled={checking||!candidate||!baseline||initialLoading} className="btn btn-outline mt-4" onClick={()=>void verifyUploaded()}><Hash size={16}/>{checking?t('refVerifying'):t('refVerify')}</button>
      {!baseline&&!initialLoading&&<p className="mt-3 text-xs muted">{t('refSelectRequired')}</p>}
      {verifyError&&<p role="alert" className="demo-box mt-4">{verifyError}</p>}
      {outcome&&<div aria-live="polite" className={`rounded-xl p-4 mt-5 border ${outcome.match?'bg-[#eaf8f0] border-[#c7e6d5]':'bg-[#fff8eb] border-[#f1dfb6]'}`}>
        <p className="font-extrabold text-sm text-ink flex gap-2 items-center">{outcome.match?<CheckCircle2 size={18} className="text-forest"/>:<AlertTriangle size={18} className="text-amber-700"/>}{outcome.match?t('refExact'):t('refDifferent')}</p>
        <p className="text-sm mt-3 leading-6">{outcome.match?t('refSameWarning'):t('refDifferentWarning')}</p>
        {!outcome.deed_matches&&<p className="text-xs text-red-600 mt-2">{t('refDeedMismatch')}</p>}
        <div className="text-xs mt-4 space-y-2 break-all"><div><b>SHA-256 ({t('refCurrent')}):</b> <code>{outcome.reference_sha256}</code></div><div><b>SHA-256 ({t('refUploaded')}):</b> <code>{outcome.submitted_sha256}</code></div></div>
      </div>}
    </div>
    <p className="text-xs muted leading-5 mt-5">{t('refGuest')}</p>
  </div>
}
