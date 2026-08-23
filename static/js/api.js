const API_BASE='/api';const TOKEN_KEY='expense_portal_token';
function getToken(){return localStorage.getItem(TOKEN_KEY)}
function setToken(value){localStorage.setItem(TOKEN_KEY,value)}
function clearToken(){localStorage.removeItem(TOKEN_KEY)}
function tokenPayload(){try{return JSON.parse(atob(getToken().split('.')[1].replace(/-/g,'+').replace(/_/g,'/')))}catch{return{}}}
async function apiFetch(path,options={}){const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(options.headers||{})};if(getToken())headers.Authorization=`Bearer ${getToken()}`;const response=await fetch(`${API_BASE}${path}`,{...options,headers});const body=await response.json().catch(()=>({}));if(response.status===401){clearToken();location.href='/login';throw Error('Your session has expired.')}if(response.status===403)throw Error('You are not authorized for this action.');if(!response.ok)throw Error(body.error||`Request failed (${response.status}).`);return body}
function jsonBody(form){return Object.fromEntries(new FormData(form).entries())}
