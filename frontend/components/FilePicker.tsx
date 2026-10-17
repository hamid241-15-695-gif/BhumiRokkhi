'use client';
import {FileUp} from 'lucide-react';
import {useRef} from 'react';
import {useLanguage} from './LanguageProvider';
export default function FilePicker({value,onChange,label,disabled=false}:{value:File|null;onChange:(file:File|null)=>void;label:string;disabled?:boolean}){
  const input=useRef<HTMLInputElement|null>(null);
  const {t}=useLanguage();
  return <div>
    <span className="field-label">{label}</span>
    <input aria-label={label} ref={input} type="file" accept=".pdf,.png,.jpg,.jpeg" className="sr-only" disabled={disabled} onChange={e=>onChange(e.target.files?.[0]||null)}/>
    <button type="button" onClick={()=>{if(input.current){input.current.value='';input.current.click()}}} disabled={disabled} className="field !h-auto min-h-[47px] w-full flex items-center gap-2 text-left hover:border-forest focus:outline-forest">
      <FileUp size={17} className="shrink-0 text-forest"/>
      <span className="flex-1 min-w-0 truncate">{value?.name||t('chooseFile')}</span>
    </button>
  </div>
}
