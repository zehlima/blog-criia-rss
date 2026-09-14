# BLOG CRIIA — fechamento parcial de 14/09/2026, 19h02 BRT

## Cobertura e origem dos textos

Fonte: Supabase ikoqkeqxqfqkfjmcwwdq, tabelas news_runs, news_collection_attempts, news_feed_runs, news_feeds, news_articles e news_article_feeds. Inventário: 675 URLs únicos de data/feeds.json, commit f66824bc0195b6a82cb2884bc655fca846e8d126. Métricas restritas a esses URLs; fontes históricas preservadas.

- Janela: 14/09/2026 18h BRT (21h UTC). Encerramento da tentativa: 19h02min14s BRT. Estado: partial.
- Tentados: 675/675 (100%). OK: 639 (94,7%). Erros: 36 (5,3%). Não tentados: 0.
- Notícias únicas por ID/URL: 26.874. Este número não representa deduplicação semântica entre veículos.
- Com content_key: 25.390. Corpos registrados como válidos: 25.385 = 24.476 extraídos da página + 909 fornecidos pelo publisher no RSS.
- Cinco content_key estão associados a referências inválidas e não entram no total de corpos válidos. Sete referências inválidas no total.
- Falhas de extração sem corpo: 1.482. Status pending: 0.
- Ainda devidas ao fechar: 1.740 rechecagens de matérias que já tinham corpo (1.724 de página + 16 RSS). Isso explica o encerramento parcial; não são 1.740 novas matérias sem texto.
- content_key e status de extração não demonstram integralidade editorial do texto. Títulos/resumos não foram contados como corpos. Conteúdo de publisher no RSS é separado de texto extraído da página.
- Variação contra o fechamento anterior: +2.455 notícias únicas; +2.209 corpos válidos; +10 feeds em erro.

[Coleta encerrada](https://github.com/zehlima/blog-criia-rss/actions/runs/34897398916).

## Classificação das 36 falhas RSS

21 bloqueios HTTP 403; 1 bloqueio de destino não público; 8 falhas temporárias de rede/servidor; 1 HTTP 429; 2 respostas/XML inválidos; 1 TLS; 1 feed vazio; 1 HTTP 404. Nenhuma reposição definitiva foi aplicada. AttributeError seria classificado como erro interno, nunca como prova de feed inválido.

## Pendências separadas

- feeds_pending.csv: nenhum feed não tentado neste fechamento.
- extraction_errors.csv: 1.482 falhas de extração de matérias, com tentativas e próxima tentativa preservadas.
- Os 36 erros RSS abaixo não são somados às falhas de extração de matérias.
- As 1.740 rechecagens vencidas conservam conteúdo existente e checkpoints. Não foi resetado backoff.

## Interrupção, causa e correção

A [retomada 34902726986](https://github.com/zehlima/blog-criia-rss/actions/runs/34902726986) falhou antes da coleta: tests/test_daily.py importava numpy indisponível no ambiente leve. Não houve nova rodada fechada nessa execução.

A [análise 34902039672](https://github.com/zehlima/blog-criia-rss/actions/runs/34902039672) foi cancelada às 19h11min23s BRT. Log do job 104170002858 confirmou cancelamento após cache de embeddings completo (26.867 artigos), sem snapshot nem escopos persistidos. O workflow disparado pela coleta fracassada compartilhava concorrência com cancelamento incondicional. O registro building foi corrigido para failed, mantendo progresso e histórico.

[Correção 514408c](https://github.com/zehlima/blog-criia-rss/commit/514408c9d219366c70d6a69cf67c00172cbd275a): testes analíticos opcionais no ambiente leve, testes integrais preservados nos ambientes analíticos; eventos de coleta fracassada isolados da concorrência elegível; novas coletas não cancelam a análise em andamento; cancelamento explícito por revisão continua permitido; etapa final registra preparo interrompido, sem modificar snapshots prontos.

Validação: 108 testes locais passaram. [Retomada real 34903677679](https://github.com/zehlima/blog-criia-rss/actions/runs/34903677679) passou pelos testes e iniciou coleta. Um worker de coleta; um de análise. Sem publicação Cloudflare, sem mudança de inventário, sem remoção de histórico.

## Tendências

[Nova execução 34903677667](https://github.com/zehlima/blog-criia-rss/actions/runs/34903677667) retomada, ainda sem entrega confirmada neste relatório. Só é entregue com snapshot ready e country, continent e globe persistidos. Alvos originais do fechamento: 19h17min14s, 19h22min14s e 19h27min14s BRT. O cancelamento atrasou a preparação; os atrasos efetivos serão registrados por escopo ao persistir. Não apresentar esta execução como produção validada.

A v18 anterior (34891535968) continua sendo o último conjunto entregue: 105 recortes de países/territórios editoriais + 7 continentes + globo = 113. Revisão amostral não é validação editorial geral. A v2 reprovada continua excluída. Este acompanhamento não substitui a contabilidade diária nem os agendamentos do coletor.

## Todos os feeds em erro

| ID | Veículo | País editorial | Região | RSS URL | Status | Erro original | Horário UTC | Classificação | Ação recomendada |
|---|---|---|---|---|---|---|---|---|---|
| 38 | Infochannel | México | América do Norte | https://infochannel.info/feed/ | error | ReadTimeout | 2026-09-14T21:13:00.559474+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 52 | RCR Wireless News | Estados Unidos | América do Norte | https://rcrwireless.com/feed | error | http_403 | 2026-09-14T21:13:15.023034+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 72 | VentureBeat | Estados Unidos | América do Norte | https://venturebeat.com/feed | error | http_429 | 2026-09-14T21:13:36.271384+00:00 | temporario_limite_http | Respeitar Retry-After e backoff. Não forçar tentativas nem repor a fonte. |
| 118 | La Gaceta de Panamá | Panamá | América Central e Caribe | https://www.lagacetadepanama.com/rss/ | error | http_403 | 2026-09-14T21:14:15.911501+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 142 | Soy502 | Guatemala | América Central e Caribe | https://www.soy502.com/rss.xml | error | invalid_or_malformed_feed | 2026-09-14T21:14:40.69144+00:00 | xml_ou_resposta_invalida | Inspecionar resposta e XML do endpoint oficial. Não concluir que o veículo é inválido. |
| 157 | BASIC thinking | Alemanha | Europa Ocidental | https://www.basicthinking.de/blog/feed/ | error | ConnectionError | 2026-09-14T21:14:59.780895+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 197 | MuyComputer | Espanha | Europa Ocidental | https://www.muycomputer.com/feed/ | error | http_500 | 2026-09-14T21:15:41.892642+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 207 | Silicon Republic | Irlanda | Europa Ocidental | https://www.siliconrepublic.com/feed/ | error | http_403 | 2026-09-14T21:15:49.95387+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 227 | AIN | Ucrânia | Europa Oriental (Leste Europeu) | https://ain.ua/feed/ | error | http_403 | 2026-09-14T21:16:14.914148+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 253 | GSMmaniak | Polônia | Europa Oriental (Leste Europeu) | https://www.gsmmaniak.pl/feed/ | error | ConnectTimeout | 2026-09-14T21:16:39.997856+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 262 | Keddr | Ucrânia | Europa Oriental (Leste Europeu) | https://keddr.com/feed/ | error | http_403 | 2026-09-14T21:16:47.822327+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 264 | Kursors.lv | Letônia | Europa Oriental (Leste Europeu) | https://kursors.lv/feed/ | error | http_403 | 2026-09-14T21:16:48.75862+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 284 | Rozetked | Rússia | Europa Oriental (Leste Europeu) | https://rozetked.me/rss.xml | error | ChunkedEncodingError | 2026-09-14T21:17:00.111654+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 294 | TECHBOX | Eslováquia | Europa Oriental (Leste Europeu) | https://www.techbox.sk/feed | error | ConnectTimeout | 2026-09-14T21:17:14.397739+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 301 | 36Kr | China | Ásia (Leste Asiático e Sudeste Asiático) | https://36kr.com/feed | error | invalid_or_malformed_feed | 2026-09-14T21:17:19.313761+00:00 | xml_ou_resposta_invalida | Inspecionar resposta e XML do endpoint oficial. Não concluir que o veículo é inválido. |
| 363 | TechWeb | China | Ásia (Leste Asiático e Sudeste Asiático) | https://www.techweb.com.cn/rss/all.xml | error | non_public_destination | 2026-09-14T21:18:15.643296+00:00 | bloqueio_seguranca_destino | Verificar DNS e endpoint público oficial. Não desabilitar proteção de destino. |
| 377 | Arab News — Science & Technology | Arábia Saudita | Oriente Médio | https://www.arabnews.com/taxonomy/term/46/all/feed | error | http_403 | 2026-09-14T21:18:30.776492+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 394 | Enterprise Channels MEA | Emirados Árabes Unidos | Oriente Médio | https://www.ec-mea.com/feed/ | error | SSLError | 2026-09-14T21:18:47.097495+00:00 | tls | Verificar cadeia de certificado e URL oficial. Manter verificação TLS. |
| 439 | The National — Technology | Emirados Árabes Unidos | Oriente Médio | https://www.thenationalnews.com/arc/outboundfeeds/rss/category/business/technology/?outputType=xml | error | invalid_empty_feed_or_entries | 2026-09-14T21:20:20.867257+00:00 | feed_vazio | Validar categoria e endpoint oficial. Feed vazio não prova encerramento do veículo. |
| 440 | Times of Israel — Tech Israel | Israel | Oriente Médio | https://www.timesofisrael.com/topic/tech-israel/feed/ | error | http_403 | 2026-09-14T21:20:21.351438+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 484 | PC Tech Magazine | Uganda | África | https://pctechmag.com/feed/ | error | http_403 | 2026-09-14T21:20:54.816808+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 494 | Techawk | Nigéria | África | https://www.techawkng.com/feed/ | error | http_403 | 2026-09-14T21:20:59.721812+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 497 | TechCabal | Nigéria | África | https://techcabal.com/feed/ | error | http_403 | 2026-09-14T21:21:01.116549+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 512 | TechTrendsKE | Quênia | África | https://techtrendske.co.ke/feed/ | error | ConnectTimeout | 2026-09-14T21:21:18.86358+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 513 | TechWeez | Quênia | África | https://techweez.com/feed/ | error | http_403 | 2026-09-14T21:21:19.327869+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 527 | APDR | Austrália | Oceania | https://asiapacificdefencereporter.com/feed/ | error | http_403 | 2026-09-14T21:21:26.356717+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 539 | Cook Islands News | Ilhas Cook | Oceania | https://www.cookislandsnews.com/feed/ | error | http_403 | 2026-09-14T21:21:34.54721+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 573 | PowerUp! | Austrália | Oceania | https://powerup-gaming.com/feed/ | error | http_403 | 2026-09-14T21:21:53.948823+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 587 | techAU | Austrália | Oceania | https://techau.com.au/feed/ | error | ConnectTimeout | 2026-09-14T21:22:12.64022+00:00 | temporario_rede_ou_servidor | Retestar na retomada autorizada com backoff. Preservar URL e identidade. |
| 597 | The National PNG | Papua-Nova Guiné | Oceania | https://www.thenational.com.pg/feed/ | error | http_403 | 2026-09-14T21:22:18.975175+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 675 | Techstrong AI | Estados Unidos | América do Norte | https://techstrong.ai/feed/ | error | http_403 | 2026-09-14T21:22:26.525051+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 985 | Click | Irã | Oriente Médio | https://www.click.ir/feeds | error | http_404 | 2026-09-14T21:23:37.075032+00:00 | endpoint_http | Confirmar mudança de URL em fonte oficial e validar tecnicamente/editorialmente antes de alterar. |
| 1206 | Adrenaline | Brasil | América do Sul | https://www.adrenaline.com.br/feed/ | error | http_403 | 2026-09-14T21:24:23.980861+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 1225 | IT Forum | Brasil | América do Sul | https://itforum.com.br/feed/ | error | http_403 | 2026-09-14T21:24:41.925691+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 1229 | TI Inside | Brasil | América do Sul | https://tiinside.com.br/feed/ | error | http_403 | 2026-09-14T21:24:48.595317+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
| 1260 | FOLOU | Colômbia | América do Sul | https://folou.co/feed/ | error | http_403 | 2026-09-14T21:25:16.29017+00:00 | bloqueio_http | Validar acesso permitido e endpoint oficial. Não contornar bloqueio nem substituir sem validação editorial. |
