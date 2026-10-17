'use client';
import {createContext,useCallback,useContext,useEffect,useState,type ReactNode} from 'react';
import {usePathname,useRouter} from 'next/navigation';
import {api,type User} from '@/lib/api';
type State={user:User|null;loading:boolean;register:(phone:string,password:string,otp:string)=>Promise<void>;login:(phone:string,password:string)=>Promise<void>;guest:()=>Promise<void>;logout:()=>Promise<void>};
const Context=createContext<State>({user:null,loading:true,register:async()=>{},login:async()=>{},guest:async()=>{},logout:async()=>{}});
export const useAuth=()=>useContext(Context);
export function AuthProvider({children}:{children:ReactNode}){const [user,setUser]=useState<User|null>(null);const [loading,setLoading]=useState(true);const pathname=usePathname();const router=useRouter();
 useEffect(()=>{let active=true;api<User>('/api/auth/me').then(p=>{if(active)setUser(p)}).catch(()=>{if(active)setUser(null)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[]);
 const isPublic=pathname==='/login'||pathname==='/register';
 useEffect(()=>{if(loading)return;if(!user&&!isPublic)router.replace(`/login?next=${encodeURIComponent(pathname)}`);if(user&&isPublic)router.replace('/')},[user,loading,isPublic,pathname,router]);
 const register=useCallback(async(phone:string,password:string,otp:string)=>{setUser(await api<User>('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,password,otp})}))},[]);
 const login=useCallback(async(phone:string,password:string)=>{setUser(await api<User>('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,password})}))},[]);
 const guest=useCallback(async()=>{setUser(await api<User>('/api/auth/guest',{method:'POST'}))},[]);
 const logout=useCallback(async()=>{try{await api('/api/auth/logout',{method:'POST'})}finally{setUser(null);router.replace('/login')}},[router]);
 return <Context.Provider value={{user,loading,register,login,guest,logout}}>{!isPublic&&(loading||!user)?<div className="container-main py-28 text-center text-slate-400">Loading session / সেশন পরীক্ষা হচ্ছে...</div>:children}</Context.Provider>;
}
