# Painel BLOG CRIIA — preparação

**Publicação suspensa por instrução do usuário.** Ainda entram outros motores antes de subir o painel. Não há projeto Pages criado nem workflow de deploy nesta entrega.

## Base preparada
Tabler Core 1.4.0 (MIT, CDN fixado) + HTML/CSS/JavaScript, sem etapa obrigatória de build. Layout responsivo com Matérias, Tendências e Coleta. Tema azul/ardósia e leitura em painel modal. Registro central de motores em src/engines.mjs; adaptador HTTP em src/api.mjs.

O front está preparado, mas NÃO está conectado ao banco. Sem API, mostra estado de preparação, sem números ou notícias inventados. A validação dos motores analíticos existentes é independente desta estrutura de interface.

## Contrato de integração proposto, versão 1
Toda resposta HTTP JSON:

```json
{
  "schema_version": 1,
  "status": "ready",
  "as_of": "2026-09-14T12:00:00Z",
  "run_id": "id-real-da-execucao",
  "coverage": {},
  "data": {}
}
```

`status`: ready, partial, building, unavailable ou failed. `data` é específico de cada motor. Datas, cobertura, referências e tipo de texto precisam vir dos dados reais.

| Área | Endpoint proposto | Dados do serviço existente | data esperado |
|---|---|---|---|
| Matérias | GET /api/articles?q=&place=&limit=30 | news_articles + news_article_feeds + news_feeds | items[] com id, title, summary, source, country, url, published_at |
| Leitura | GET /api/articles/{id} | news_articles e objeto privado no R2 | title, url, summary, text, text_basis |
| Tendências | GET /api/trends?scope=country&place= | news_analysis_runs + news_topic_snapshots | items[] com label, place, articles, publishers |
| Coleta | GET /api/operations | news_collection_attempts + contagens de artigos | metrics e errors[] |

Esses endpoints são contratos planejados, não endpoints publicados. O adaptador de servidor será implementado ao integrar o conjunto de motores. Ele deve ler somente os campos necessários e manter credenciais de banco/R2 fora do navegador. Não liberar as tabelas privadas para anon para contornar a ausência da API.

## Como encaixar os próximos motores
1. Identificar finalidade, entrada, saída, frequência, dependência e sinais de execução concluída de cada motor apresentado pelo usuário.
2. Adicionar um adaptador de servidor para traduzir a saída real ao contrato comum, sem redesenhar tabelas existentes sem necessidade.
3. Registrar a área em src/engines.mjs e implementar a visualização correspondente.
4. Preservar IDs, data de corte, cobertura incompleta e evidências. Não confundir saída de um motor com conclusão de todos.
5. Validar a integração e então retirar o hold de publicação conforme a direção do usuário.

Nenhum motor adicional foi presumido ou instalado. As próximas áreas serão definidas a partir dos motores que o usuário indicar.

## Publicação futura
Cloudflare Pages com frontend/ como diretório de arquivos estáticos. A camada /api deve ser servida na mesma origem (Pages Functions ou serviço associado) e ter acesso controlado antes de expor os textos privados. Definir público do painel antes da publicação; não presumir que matérias arquivadas no R2 podem ser disponibilizadas publicamente.

Sem automação de deploy nesta fase. release.json registra explicitamente o hold.

## Revisão local
Servir frontend/ por HTTP. Sem backend a navegação e os filtros funcionam, mostrando a integração pendente. Não abrir via file://, pois módulos JavaScript precisam de origem HTTP.

Tabler: https://github.com/tabler/tabler — licença MIT. Manter avisos da licença ao distribuir seus arquivos.
