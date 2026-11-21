const base='/api/v1';
export async function request(path,opts={}){
 const response=await fetch(base+path,{credentials:'same-origin',headers:{'Content-Type':'application/json',...opts.headers},...opts});
 if(!response.ok){let msg='Não foi possível concluir a solicitação.';try{const data=await response.json();msg=typeof data.detail==='string'?data.detail:msg;}catch{}throw new Error(msg);}
 return response.json();
}
export const getEvents=(params={})=>request('/events?'+new URLSearchParams(Object.entries(params).filter(([_,v])=>v)).toString());
export const getOrganizations=()=>request('/organizations');
export const getMcs=(search='')=>request('/mcs?'+new URLSearchParams({search}));
export const getEvent=slug=>request('/events/'+encodeURIComponent(slug));
export const getMc=slug=>request('/mcs/'+encodeURIComponent(slug));
