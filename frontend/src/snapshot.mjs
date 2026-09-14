import {APIError} from './api.mjs';
export function createSnapshotAPI({url,fetcher=fetch}) {
 return async (endpoint,params={},signal)=>{
  const response=await fetcher(url,{cache:'no-store',signal});
  if(!response.ok)throw new APIError(response.status,'not_connected');
  const s=await response.json();
  if(s.schema_version!==1)throw new APIError(502,'invalid_contract');
  if(endpoint==='operations')return s.operations;
  const wrap=(data,as_of=s.generated_at)=>({schema_version:1,status:'partial',as_of,data});
  const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  if(endpoint==='articles')return wrap({items:s.articles.filter(a=>norm(a.title).includes(norm(params.q))&&norm(a.country).includes(norm(params.place))).slice(0,Number(params.limit)||30)});
  if(endpoint.startsWith('articles/')){
   const a=s.articles.find(a=>String(a.id)===endpoint.split('/')[1]);
   if(!a)throw new APIError(404,'not_found');
   return wrap({...a,summary:'Leia o texto completo no veículo de origem.',text_basis:'source_link'});
  }
  if(endpoint==='trends'){
   const rows=s.trends.filter(t=>t.scope===params.scope&&norm(t.place).includes(norm(params.place)));
   return wrap({items:rows.flatMap(t=>(t.payload.ranking||[]).map(r=>({...r,place:t.place})))},rows[0]?.finished_at||null);
  }
  throw new APIError(404,'not_found');
 };
}
