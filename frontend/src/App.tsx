import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';

const Analytics=lazy(()=>import('./pages/Analytics').then(m=>({default:m.Analytics})));
const Auth=lazy(()=>import('./pages/Auth').then(m=>({default:m.Auth})));
const Dashboard=lazy(()=>import('./pages/Dashboard').then(m=>({default:m.Dashboard})));
const Home=lazy(()=>import('./pages/Home').then(m=>({default:m.Home})));
const Links=lazy(()=>import('./pages/Links').then(m=>({default:m.Links})));
const NotFound=lazy(()=>import('./pages/NotFound').then(m=>({default:m.NotFound})));

function Private({children}:{children:React.ReactNode}){return localStorage.getItem('access_token')?<>{children}</>:<Navigate to="/login" replace/>}
export default function App(){return <Suspense fallback={<p className="p-10" role="status">Loading…</p>}><Routes><Route element={<Layout/>}><Route index element={<Home/>}/><Route path="login" element={<Auth mode="login"/>}/><Route path="register" element={<Auth mode="register"/>}/><Route path="dashboard" element={<Private><Dashboard/></Private>}/><Route path="links" element={<Private><Links/></Private>}/><Route path="links/:id" element={<Private><Analytics/></Private>}/><Route path="*" element={<NotFound/>}/></Route></Routes></Suspense>}
