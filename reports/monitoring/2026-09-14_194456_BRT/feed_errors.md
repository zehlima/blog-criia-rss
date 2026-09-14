# BLOG CRIIA — fechamento com lacunas

Data: 2026-09-14 22:44:56.665893+00 (UTC). [GitHub Actions](https://github.com/zehlima/blog-criia-rss/actions/runs/34904308547).

Inventário ativo: 675 URLs únicas em data/feeds.json, commit 550f3b6b74ecb8fbd40d16dc8ff240b95be98ea4. Todos os 675 feeds foram tentados (100%): 646 OK (95,70%), 29 erros e 0 não tentados. Isso não representa 100% de conteúdo obtido.

Notícias únicas associadas a URLs ativas: 26896. Referências content_key: 25420; corpos classificados válidos: 25415 = 24501 extraídos da página + 914 fornecidos no RSS. Falhas de extração: 1474; referências inválidas: 7; pendências: 0. content_key, tamanho mínimo e status não comprovam integralidade editorial do texto. Não contamos título/resumo como texto completo.

Fila devida desta rodagem: 0. A recuperação retomou checkpoints e preservou o backoff. A falha nativa anterior (free(): invalid pointer; saída 134) recebeu contenção de concorrência de parsing no commit 550f3b6. Esta execução terminou com sucesso, sem garantir eliminação de todo defeito nativo futuro.

Falhas de matérias estão separadas em extraction_errors.csv (1.474 linhas). Nenhuma substituição definitiva de RSS aplicada nesta verificação.

No Git, a lista extensa de falhas está em extraction_errors.csv.gz (CSV comprimido sem perda); a cópia no Drive permanece em CSV aberto.

## Feeds com erro

| ID | Veículo | País editorial | Região | RSS URL | Erro original | Horário UTC | Classificação | Ação recomendada |
|---|---|---|---|---|---|---|---|---|
| 38 | Infochannel | México | América do Norte | https://infochannel.info/feed/ | ReadTimeout | 2026-09-14 22:29:32.082764+00 | temporario_rede_ou_servidor | Retentar pelo coletor com backoff e preservar checkpoints; confirmar recorrência antes de alterar URL. |
| 52 | RCR Wireless News | Estados Unidos | América do Norte | https://rcrwireless.com/feed | http_403 | 2026-09-14 22:29:32.669353+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 72 | VentureBeat | Estados Unidos | América do Norte | https://venturebeat.com/feed | http_429 | 2026-09-14 22:29:33.254529+00 | temporario_http_429 | Respeitar Retry-After e backoff; não contornar bloqueio nem substituir definitivamente. |
| 118 | La Gaceta de Panamá | Panamá | América Central e Caribe | https://www.lagacetadepanama.com/rss/ | http_403 | 2026-09-14 22:29:33.839963+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 142 | Soy502 | Guatemala | América Central e Caribe | https://www.soy502.com/rss.xml | invalid_or_malformed_feed | 2026-09-14 22:29:34.425049+00 | xml_invalido | Inspecionar XML/resposta e endpoint oficial; validar tecnicamente e editorialmente antes de corrigir URL. |
| 207 | Silicon Republic | Irlanda | Europa Ocidental | https://www.siliconrepublic.com/feed/ | http_403 | 2026-09-14 22:29:35.010716+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 227 | AIN | Ucrânia | Europa Oriental (Leste Europeu) | https://ain.ua/feed/ | http_403 | 2026-09-14 22:29:35.596315+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 262 | Keddr | Ucrânia | Europa Oriental (Leste Europeu) | https://keddr.com/feed/ | http_403 | 2026-09-14 22:29:36.181729+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 264 | Kursors.lv | Letônia | Europa Oriental (Leste Europeu) | https://kursors.lv/feed/ | http_403 | 2026-09-14 22:29:37.03083+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 284 | Rozetked | Rússia | Europa Oriental (Leste Europeu) | https://rozetked.me/rss.xml | ChunkedEncodingError | 2026-09-14 22:29:38.069968+00 | temporario_rede_ou_servidor | Retentar pelo coletor com backoff e preservar checkpoints; confirmar recorrência antes de alterar URL. |
| 301 | 36Kr | China | Ásia (Leste Asiático e Sudeste Asiático) | https://36kr.com/feed | invalid_or_malformed_feed | 2026-09-14 22:29:38.654899+00 | xml_invalido | Inspecionar XML/resposta e endpoint oficial; validar tecnicamente e editorialmente antes de corrigir URL. |
| 363 | TechWeb | China | Ásia (Leste Asiático e Sudeste Asiático) | https://www.techweb.com.cn/rss/all.xml | non_public_destination | 2026-09-14 22:29:39.240306+00 | bloqueio_seguranca_destino | Inspecionar DNS/redirecionamento público oficial; manter proteção contra destino não público. |
| 377 | Arab News — Science & Technology | Arábia Saudita | Oriente Médio | https://www.arabnews.com/taxonomy/term/46/all/feed | http_403 | 2026-09-14 22:29:39.825128+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 394 | Enterprise Channels MEA | Emirados Árabes Unidos | Oriente Médio | https://www.ec-mea.com/feed/ | SSLError | 2026-09-14 22:29:40.410199+00 | tls | Verificar certificado e endpoint oficial; não desativar validação TLS. |
| 439 | The National — Technology | Emirados Árabes Unidos | Oriente Médio | https://www.thenationalnews.com/arc/outboundfeeds/rss/category/business/technology/?outputType=xml | invalid_empty_feed_or_entries | 2026-09-14 22:29:40.996252+00 | feed_vazio | Verificar categoria e itens oferecidos; feed vazio não prova veículo inativo. |
| 440 | Times of Israel — Tech Israel | Israel | Oriente Médio | https://www.timesofisrael.com/topic/tech-israel/feed/ | http_403 | 2026-09-14 22:29:41.581765+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 484 | PC Tech Magazine | Uganda | África | https://pctechmag.com/feed/ | http_403 | 2026-09-14 22:29:42.344196+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 494 | Techawk | Nigéria | África | https://www.techawkng.com/feed/ | http_403 | 2026-09-14 22:29:42.929298+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 497 | TechCabal | Nigéria | África | https://techcabal.com/feed/ | http_403 | 2026-09-14 22:29:43.514449+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 513 | TechWeez | Quênia | África | https://techweez.com/feed/ | http_403 | 2026-09-14 22:29:44.099725+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 527 | APDR | Austrália | Oceania | https://asiapacificdefencereporter.com/feed/ | http_403 | 2026-09-14 22:29:44.685021+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 539 | Cook Islands News | Ilhas Cook | Oceania | https://www.cookislandsnews.com/feed/ | http_403 | 2026-09-14 22:29:45.270381+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 573 | PowerUp! | Austrália | Oceania | https://powerup-gaming.com/feed/ | http_403 | 2026-09-14 22:29:45.855618+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 597 | The National PNG | Papua-Nova Guiné | Oceania | https://www.thenational.com.pg/feed/ | http_403 | 2026-09-14 22:29:46.441138+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 675 | Techstrong AI | Estados Unidos | América do Norte | https://techstrong.ai/feed/ | http_403 | 2026-09-14 22:29:47.222743+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 985 | Click | Irã | Oriente Médio | https://www.click.ir/feeds | http_404 | 2026-09-14 22:29:48.200295+00 | endpoint_http_404_410 | Investigar RSS oficial equivalente do mesmo veículo e testar antes de alterar; não recomendar reposição definitiva. |
| 1206 | Adrenaline | Brasil | América do Sul | https://www.adrenaline.com.br/feed/ | http_403 | 2026-09-14 22:29:48.786091+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 1225 | IT Forum | Brasil | América do Sul | https://itforum.com.br/feed/ | http_403 | 2026-09-14 22:29:49.371934+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
| 1229 | TI Inside | Brasil | América do Sul | https://tiinside.com.br/feed/ | http_403 | 2026-09-14 22:29:49.957543+00 | bloqueio_http | Verificar política e endpoint público oficial permitido; não contornar nem substituir sem validação editorial. |
