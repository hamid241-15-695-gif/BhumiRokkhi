'use client';
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {type Lang,txt} from '@/lib/i18n';
type TKey=keyof typeof txt.bn;
const Context=createContext<{lang:Lang;setLang:(v:Lang)=>void;t:(v:TKey)=>string}>({lang:'bn',setLang:()=>{},t:k=>txt.bn[k]});
export const useLanguage=()=>useContext(Context);
export function LanguageProvider({children}:{children:ReactNode}){const [lang,setLang]=useState<Lang>('bn');useEffect(()=>{const v=localStorage.getItem('br-v3-lang');if(v==='bn'||v==='en')setLang(v)},[]);useEffect(()=>{document.documentElement.lang=lang;document.title=lang==='bn'?'ভূমিরক্ষী':'BhumiRokkhi';localStorage.setItem('br-v3-lang',lang)},[lang]);return <Context.Provider value={{lang,setLang,t:k=>txt[lang][k]}}>{children}</Context.Provider>}
