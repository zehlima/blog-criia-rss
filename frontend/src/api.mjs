export class APIError extends Error {
  constructor(status,code) {super(code);this.status=status;this.code=code;}
}
export function createAPI({base,fetcher=fetch}) {
  const root=new URL(base);
  if(!['http:','https:'].includes(root.protocol)) throw new TypeError('Invalid API protocol');
  return async function read(endpoint,params={},signal) {
    if(!/^[a-z][a-z0-9/-]*$/.test(endpoint)) throw new TypeError('Invalid endpoint');
    const url=new URL(endpoint,root);
    if(url.origin!==root.origin || !url.pathname.startsWith(root.pathname)) throw new TypeError('Invalid API destination');
    for(const [key,value] of Object.entries(params)) if(value!=='' && value!=null) url.searchParams.set(key,String(value));
    const response=await fetcher(url,{credentials:'same-origin',headers:{Accept:'application/json'},signal});
    if(!response.ok) throw new APIError(response.status,response.status===404?'not_connected':'request_failed');
    if(!response.headers.get('content-type')?.includes('application/json')) throw new APIError(502,'invalid_response');
    const result=await response.json();
    if(result.schema_version!==1 || !['ready','partial','building','unavailable','failed'].includes(result.status)) throw new APIError(502,'invalid_contract');
    if(!result.data || typeof result.data!=='object') throw new APIError(502,'invalid_contract');
    return result;
  };
}
