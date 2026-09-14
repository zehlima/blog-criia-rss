# CRIIA — 15 grandes fontes globais de tecnologia

Pesquisa e implementação em 14/09/2026. Resultado no GitHub: **13/15 fontes acessíveis (86,7%)**. Gizmodo e VentureBeat continuam indisponíveis nesse ambiente; os impedimentos não são marcados como sucesso.

## Critério de seleção

Painel editorial internacional por alcance documentado quando disponível, relevância setorial e diversidade geográfica. Não é um ranking estatístico dos 15 maiores sites por audiência: não foi encontrada uma medição mundial única, pública e comparável que reúna veículos, base de dados e comunidades. A ordem abaixo não expressa posição no mercado. Estados Unidos/Reino Unido, Alemanha e China estão representados; o painel não pretende cobrir todos os países. Crunchbase News e Reddit foram incluídos conforme o pedido.

CNET e ZDNET divulgam médias de visitantes únicos globais de 23 milhões e 6,4 milhões (Comscore FY2025, dados publicados pelo grupo). TechRadar divulga alcance de até 30 milhões por mês; heise divulga 41,3 milhões de visitas em seu portal comercial. São métricas e períodos diferentes e não foram usados para produzir uma ordem artificial.

## Fontes e acesso gratuito

RSS/Atom público dispensa assinatura para ler o feed. Isso não concede acesso integral a artigos pagos. O RSS do Crunchbase News não é a API comercial nem uma exportação da base de empresas do Crunchbase. Reddit r/technology é classificado como comunidade, não como redação.

| Fonte | Mercado editorial | RSS/Atom | Validação no GitHub |
|---|---|---|---|
| TechCrunch | Estados Unidos (en) | [Feed](https://techcrunch.com/feed/) | OK — 20 itens |
| The Verge | Estados Unidos (en) | [Feed](https://www.theverge.com/rss/index.xml) | OK — 10 itens |
| WIRED | Estados Unidos (en) | [Feed](https://www.wired.com/feed/rss) | OK — 50 itens |
| Ars Technica | Estados Unidos (en) | [Feed](https://feeds.arstechnica.com/arstechnica/index) | OK — 20 itens |
| Engadget | Estados Unidos (en) | [Feed](https://www.engadget.com/rss.xml) | OK — 20 itens |
| CNET | Estados Unidos (en) | [Feed](https://www.cnet.com/rss/news/) | OK — 25 itens |
| ZDNET | Estados Unidos (en) | [Feed](https://www.zdnet.com/news/rss.xml) | OK — 25 itens |
| TechRadar | Reino Unido (en) | [Feed](https://www.techradar.com/rss) | OK — 50 itens |
| Tom's Hardware | Estados Unidos (en) | [Feed](https://www.tomshardware.com/feeds.xml) | OK — 50 itens |
| VentureBeat | Estados Unidos (en) | [Feed](https://venturebeat.com/feed) | BLOQUEADO — 429 (limite de acesso) |
| Gizmodo | Estados Unidos (en) | [Feed](https://gizmodo.com/feed) | BLOQUEADO — 403 (RSS e robots) |
| Crunchbase News | Estados Unidos (en) | [Feed](https://news.crunchbase.com/feed/) | OK — 10 itens |
| Reddit r/technology | Estados Unidos (en) | [Feed](https://www.reddit.com/r/technology/new/.rss?limit=100) | OK — 100 itens |
| heise online | Alemanha (de) | [Feed](https://www.heise.de/rss/heise-atom.xml) | OK — 151 itens |
| 36Kr | China (zh) | [Feed](https://www.36kr.com/feed) | OK — 30 itens |

## Coleta e agendamento

- Agenda do coletor existente: diariamente às **00h, 06h, 12h e 18h de Brasília** (`America/Sao_Paulo`). Cron UTC: `0 3,9,15,21 * * *`. GitHub Actions pode atrasar disparos; o horário configurado não é uma garantia de início ao segundo.
- Recuperação horária já existente mantém checkpoints. Um lock no banco impede coletores simultâneos; fontes com sucesso na janela não são coletadas novamente.
- `data/feeds.json` passa de 675 para 678 fontes ativas: 12 cadastros reaproveitados e 3 adicionados ao manifesto (ZDNET, Gizmodo, Reddit). Identidades e notícias anteriores são preservadas.
- `data/technology15.json` identifica o recorte, idioma e tipo de fonte. `collector.technology15` testa esse recorte com o mesmo parser e HTTP do coletor principal.
- `collector.technology15_ingest` faz a primeira gravação usando o pipeline, o lock e as tabelas existentes. A coleta global continua responsável pela extração dos corpos de texto.
- Monitoramento de acompanhamento também agendado nos mesmos quatro horários; verifica o workflow existente, sem criar um segundo worker. Alertas apenas para falhas materiais ou mudanças relevantes.
- A variável `ENABLE_COLLECTION=false` continua sendo a forma explícita de pausar disparos agendados. Não foi alterada nesta tarefa.

## Alternativas e bloqueios

**36Kr:** o endereço sem www retornava HTML não reconhecido como feed. O coletor mantém a identidade original e usa `https://www.36kr.com/feed` como alternativa; 30 itens confirmados no GitHub. A página oficial de RSS é https://www.36kr.com/rss-center.

**Gizmodo:** os feeds principal, `/tech/feed` e `/rss` retornaram 403 no GitHub. A página oficial de distribuição é https://gizmodo.com/gizmodo-syndication-15739. Foi implementado coletor de manchetes da página pública; ele também não pôde operar porque a leitura de robots retornou 403. Estado: configurado, acesso bloqueado. Não há evidência de coleta bem-sucedida deste veículo.

**VentureBeat:** o feed gratuito retornou 7 itens no teste inicial local, mas o GitHub recebeu 429 mesmo após espera e nova tentativa. A página pública também foi testada e recebeu 429. O código final respeita o limite e deixa a recuperação para a próxima tentativa; não troca de rota para contornar 429. Estado: feed existente, indisponível no runtime atual.

O coletor de HTML aceita apenas títulos e URLs de artigos do próprio veículo, elimina duplicações e navegação e falha explicitamente quando não encontra conteúdo suficiente. Não inventa datas, não trata HTML de bloqueio como RSS e não transforma manchetes em texto integral. Validações HTTP não representam garantia futura de acesso.

## Limites da cobertura

Feeds têm janelas finitas (por exemplo, o teste da Verge trouxe 10 itens). Quatro consultas diárias não garantem capturar toda publicação feita entre consultas, sobretudo em fontes de alto volume. A coleta preserva o que cada feed efetivamente disponibiliza.

RSS de veículos generalistas de tecnologia também pode conter ciência, cultura, jogos e listas de compras. A seleção de veículos não equivale a filtro temático por matéria. O tipo social do Reddit está documentado no manifesto; esta tarefa não redesenhou a contabilidade editorial de tendências.

## Verificações e arquivos

- 117 testes locais passaram, incluindo seleção de URLs, parsing RSS/Atom, alternativas, duplicação, classificação e preservação de conteúdo.
- `runtime-validation.json`: 15 testes de rede no GitHub, com data, método, quantidade e erro.
- `probes.json`: tentativas iniciais locais, inclusive timeouts; não são o resultado final do runtime.
- `technology15.csv`: tabela com fontes, idioma, RSS, justificativa, evidência e status.
- `technology15.opml`: importação em leitores RSS. Endereços públicos podem sofrer os mesmos bloqueios; o OPML já usa a alternativa www da 36Kr.
- `selection.json`: base da seleção e URLs primárias.
- Código: `collector/publisher_listing.py`, `collector/technology15.py`, `collector/technology15_ingest.py`.
- Workflow de validação/integração: `.github/workflows/technology15.yml`; agenda de produção: `.github/workflows/collect.yml`.

## Evidências primárias da seleção

- **TechCrunch** — Startups, investimentos e inovação. https://techcrunch.com/about-techcrunch/
- **The Verge** — Tecnologia, cultura e grandes plataformas. https://www.theverge.com/about-the-verge
- **WIRED** — Tecnologia, ciência e sociedade. https://www.wired.com/feed/rss
- **Ars Technica** — Análise técnica, ciência e computação. https://arstechnica.com/about-us/
- **Engadget** — Eletrônicos e tecnologia de consumo. https://www.engadget.com/about/
- **CNET** — 23 milhões de visitantes únicos mensais globais médios; Comscore FY2025 segundo o grupo. https://www.ziffdavis.com/brands/technology/cnet
- **ZDNET** — 6,4 milhões de visitantes únicos mensais globais médios; Comscore FY2025 segundo o grupo. https://www.ziffdavis.com/brands/technology/zdnet
- **TechRadar** — Até 30 milhões de pessoas por mês segundo a Future; cobertura internacional. https://futureplc.com/brands/tech/
- **Tom's Hardware** — Hardware e computação; marca do portfólio tecnológico internacional da Future. https://futureplc.com/brands/tech/
- **VentureBeat** — IA e tecnologia para empresas. https://venturebeat.com/about
- **Gizmodo** — Tecnologia de consumo e cultura digital. https://gizmodo.com/about
- **Crunchbase News** — Redação sobre startups, capital e negócios; independente da venda de dados do grupo. https://news.crunchbase.com/about-news/
- **Reddit r/technology** — Comunidade de discussão; fonte social, não redação jornalística. https://www.reddit.com/r/technology/
- **heise online** — Referência de tecnologia em alemão; 41,3 milhões de visitas divulgadas no portal comercial, métrica não comparável a únicos. https://reachit.heise.de/
- **36Kr** — Plataforma chinesa da nova economia; inclui o mercado de tecnologia da China. https://36kr.com/pages/about-en

Validação de rede: https://github.com/zehlima/blog-criia-rss/actions/runs/34909638599

## Execução e preservação

A primeira integração (`34909812531`) gravou o recorte com 12 fontes OK e três erros: Gizmodo, VentureBeat e Reddit. O Reddit havia passado na validação, mas a segunda consulta imediata recebeu 429. O workflow foi corrigido para fazer apenas a consulta necessária à ingestão, aproveitando checkpoints. A evidência da primeira tentativa está em `ingestion-first-attempt.json`; o fechamento está em `ingestion-final.json`.

Os 117 testes locais incluem dependências de análise disponíveis no workspace. No GitHub, 49 testes passaram e duas suítes opcionais de análise foram ignoradas por falta dessas dependências; os testes do coletor e desta mudança foram executados. Nenhum teste ignorado foi contabilizado como aprovado.

O último disparo agendado anterior a esta entrega foi o workflow global `34907512243`, encerrado com sucesso técnico em 14/09/2026. A primeira execução deste novo recorte confirma gravação de dados; sucesso técnico não é sinônimo de ausência de lacunas.

**Fechamento confirmado às 20h41 BRT:** 13/15 fontes com coleta de metadados persistida na janela das 18h. Reddit: 100 publicações gravadas; 36Kr: 30; ZDNET: 25. Gizmodo permanece com 403; VentureBeat com 429. A execução mantém conclusão de falha para não ocultar essas lacunas. [Execução final](https://github.com/zehlima/blog-criia-rss/actions/runs/34909977876).
