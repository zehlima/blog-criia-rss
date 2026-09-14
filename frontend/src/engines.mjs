// Registration is local configuration. Never accept module URLs from API data.
export const engines = Object.freeze([
  {id:'articles',label:'Matérias',description:'Leitura e busca na base monitorada',endpoint:'articles',view:'articles'},
  {id:'trends',label:'Tendências',description:'Assuntos por país, continente e globo',endpoint:'trends',view:'trends'},
  {id:'operations',label:'Coleta',description:'Cobertura, textos e erros dos feeds',endpoint:'operations',view:'operations'},
]);
export function engineById(id) {return engines.find(engine=>engine.id===id) || engines[0];}
