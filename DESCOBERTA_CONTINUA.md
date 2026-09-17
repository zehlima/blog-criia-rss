# Descoberta contínua de fontes — Bóris / Farza

Data: 17/09/2026. Base auditada: 9a09d21a4d6dbbe9f218d6479c85b97ac8bc91a8, repositório zehlima/blog-criia-rss.

## Entrega e limites

O Bóris continua sendo o único coletor do acervo. A extensão descobre feeds anunciados em sites e novos domínios a partir de links, mantém uma fila durável, observa conteúdo e prepara a admissão humana. Feedparser 6.0.14, Trafilatura 2.2.0, lxml e urllib3 já pertenciam ao projeto; não foram adicionados Scrapy ou Feedsearch. A rotina reaproveita parsing, extração e transporte existentes.

**Estado desta entrega: implementação local, switches versionados desligados.** Não houve crawler real, alteração de banco remoto, ativação de agenda, publicação editorial ou chamada de IA durante a implementação. Os testes usam respostas artificiais e PostgreSQL local PGlite.

A avaliação automática é **técnica**, nunca um selo de veracidade ou probabilidade. A integração de um avaliador de IA continua pendente. A decisão editorial exige operador autorizado, motivo, URLs de evidência, nome do veículo, país e região. Nenhuma fonte é ativada só porque o parser conseguiu lê-la.

## Fluxo implementado

1. Sementes: homepages de fontes já cadastradas ou URL explícita. Primeiro ciclo habilitado semeia a fila vazia em lote, com auditoria; não modifica o inventário ativo.
2. Descoberta: links RSS/Atom/JSON Feed anunciados e links externos nas páginas. Feeds de comentários são descartados. Não inventa endpoints nem contorna bloqueios.
3. Fila: próxima tentativa, número de tentativas, lease exclusivo de 10 minutos, retorno após interrupção e backoff. Prioridade persistente: duas oportunidades de validação de feed para uma de exploração de site; tipo ausente usa o outro.
4. Observação: RSS/Atom interpretado pelo parser de produção; até três artigos amostrados por tarefa com extração real. Amostras já obtidas sobrevivem ao esgotamento de orçamento, com cursor para continuar. Links também têm cursor; o lote não exclui definitivamente links seguintes.
5. Pronto para revisão: pelo menos duas observações ao longo de seis horas, com dois corpos distintos de artigos diferentes nos últimos sete dias; observação mais recente precisa ter extração utilizável. Revisões antigas do mesmo artigo não contam como dois artigos. Uma revisão humana de admissão exige verificação recente, de até dois dias, e ausência de erro atual.
6. Admissão: insere a fonte com identidade estável, evidências e responsável. Só passa a valer na próxima janela de seis horas de Brasília.
7. Coleta regular: manifesto curado mais admissões vigentes, congelado por janela; recuperação lê o mesmo snapshot. Tendências, exportação e fechamento recebem esse inventário. Um fechamento já concluído não é reescrito. A cobertura diária soma os quatro inventários observados, sem multiplicar o último tamanho por quatro.

JSON Feed é encontrado, mas fica registrado como formato não suportado: o coletor principal continua RSS/Atom. É necessário um adaptador antes de admitir esse formato.

Links de anúncios ou páginas sem natureza jornalística podem entrar como candidatos; a etapa humana decide sua adequação. Profundidade automática limitada a quatro e páginas de até 2 MiB são orçamento de exploração, não limite editorial nem promessa de cobrir a web inteira.

## Limites operacionais

| Controle | Valor inicial |
|---|---:|
| Agenda de descoberta | minuto 17 de cada hora |
| Chamadas HTTP por tick | 15 reservas |
| Tempo cooperativo por tick | 180 segundos; não começa outro item depois do prazo |
| Lease por tarefa | 10 minutos |
| Teto compartilhado por dia UTC | 120 requisições reservadas |
| Teto de corpos reservado por dia UTC | 128 MiB |
| Corpo de página/artigo | 2 MiB |
| Corpo de feed | 4 MiB |
| Robots | até 512 KiB |
| Margem por requisição | 64 KiB para o último bloco recebido |
| Amostragem por tarefa de feed | até 3 artigos, com cursor |
| Custo de IA na descoberta | nenhuma chamada de IA implementada |

Robots e cada redirecionamento consomem reservas. Reserva ocorre antes do HTTP; erros não geram reembolso de consumo incerto. O teto de bytes é de corpos, não uma medição financeira de tráfego total. Headers/TLS, minutos Actions e consultas PostgreSQL também têm custo de infraestrutura; nenhum valor monetário foi medido. O objetivo não é uma quota de fontes admitidas por dia.

Resolução DNS é conferida por destino e por redirecionamento; a conexão usa o IP validado preservando Host, SNI e validação do certificado do publisher. O transporte direto ignora proxies do ambiente. HTTP/HTTPS internos e destinos de metadados são recusados. Segredos não aparecem nos erros.

O coletor respeita Disallow de robots e conserva sua cadência por domínio. Limite atual: Crawl-delay e Retry-After não têm implementação específica; falhas HTTP usam espera progressiva persistente. Não apresentar esse comportamento como suporte completo a todos os controles de polidez.

## Configuração versionada e pausa

Arquivo config/discovery.json:

{
  "schema_version": 1,
  "discovery_enabled": false,
  "dynamic_inventory_enabled": false
}

Ambos ficam false nesta entrega. Depois da revisão, schemas e preflight, um commit explícito pode mudar ambos para true. O workflow de descoberta escuta a alteração desse arquivo em main e a agenda horária, sem exigir uma nova variável do painel.

As variáveis opcionais BORIS_DISCOVERY_ENABLED e BORIS_DYNAMIC_INVENTORY aceitam 1/true ou 0/false. Valor não vazio tem precedência sobre o arquivo, permitindo pausa operacional; valor inválido falha de forma visível. Elas não alteram os gates preexistentes de coleta, publicação ou análise.

Com descoberta desligada, o workflow faz checkout e confere o arquivo, mas não instala pacotes nem conecta ao banco ou à web. Isso ainda pode consumir um pequeno tempo de Actions. O computador do usuário não precisa permanecer ligado.

Desligar inventário dinâmico bloqueia novas incorporações; snapshots de janelas já congeladas permanecem válidos. Se o schema ainda não existe, só a consulta de existência precede o comportamento legado. Uma indisponibilidade real do banco não vira silenciosamente um inventário vazio.

## Ordem de implantação pelo responsável

1. Confirmar repositório zehlima/blog-criia-rss e Supabase **ikoqkeqxqfqkfjmcwwdq**, do Bóris. Não aplicar no Supabase do Farza editorial.
2. Conferir a base e o diff; executar testes/CI. Configuração segue false.
3. Preflight somente leitura: news_feeds, news_collection_attempts, news_daily_closures e news_article_observations precisam existir; verificar que não há outra versão parcial das tabelas novas.
4. Aplicar sql/002_continuous_discovery.sql e sql/003_dynamic_inventory.sql. São aditivos e não criam cron, alteram feeds existentes ou reconstruem história.
5. Conferir oito tabelas novas, RLS e ausência de permissões anon/authenticated. Executar status sem ativar coleta. Não é necessário R2 novo nem nova chave de IA.
6. Integrar/publicar o código revisado no main com switches desligados.
7. Commit operacional separado mudando os dois switches para true. Se houver override de ambiente 0, o arquivo não vence esse override; corrigir explicitamente a configuração operacional.
8. Primeiro workflow habilitado: semear homepages existentes se a fila estiver vazia, executar um tick limitado e registrar status. Verificar progresso real, orçamento e candidatos antes de declarar descoberta operacional.
9. Após pelo menos seis horas e observações suficientes, revisar candidato real; uma admissão humana vale somente na próxima janela. Verificar sua entrada na coleta, tendências e exportação antes de declarar o percurso completo homologado.

Credenciais PostgreSQL já usadas pelos workflows Bóris permanecem somente nos secrets do runner. A implementação não requer copiar credenciais para o Farza nem para o frontend.

## Comandos de operação

Executar em ambiente autorizado do Bóris, com as credenciais existentes injetadas no servidor:

- python -m collector.discovery setup — aplica somente os schemas 002 e 003; não coleta.
- python -m collector.discovery status — contagens, configuração, último progresso e orçamento.
- python -m collector.discovery seed --known-publishers --if-empty --actor OPERADOR — semeia uma fila vazia.
- python -m collector.discovery seed --url https://veiculo.example/ --actor OPERADOR — adiciona uma semente explícita.
- python -m collector.discovery tick — trabalha somente se o switch estiver ligado.
- python -m collector.discovery list --after 0 — página de 50 candidatos; usar next_after para continuar.
- python -m collector.discovery inspect --candidate ID — evidências e diagnóstico.
- python -m collector.discovery admit --candidate ID --actor OPERADOR --reason "Motivo editorial registrado" --evidence https://veiculo.example/sobre --name "Nome do veículo" --country "Brasil" --region "América do Sul"
- python -m collector.discovery reject --candidate ID --actor OPERADOR --reason "Motivo editorial registrado" --evidence https://veiculo.example/sobre

A identidade actor é uma declaração do operador do CLI, cujo acesso depende da credencial PostgreSQL; não é autenticação de jornalista. Nenhuma nova tela de admissão no Farza foi implementada nesta frente. Reativação de candidato já rejeitado e revogação de fonte admitida exigem uma operação administrativa própria; não são feitas automaticamente.

## Monitoramento

dashboard.json e data/explorer/manifest.json recebem o campo opcional source_discovery, sem mudar seus schemas existentes. Ele contém schema_version, measured_at, configuration, schema_ready, status, contagens por estado/tipo, orçamento reservado, tetos e último sucesso. Não contém amostras, credenciais, ator ou dados da revisão.

É um snapshot atualizado pelo exportador existente, não telemetria de minuto em minuto. Um consumidor precisa mostrar measured_at e considerar a defasagem. Campo ausente significa versão anterior; schema_ready=false significa não provisionado. Nenhum desses casos deve virar zero fontes ou motor saudável por inferência. O painel Farza não foi alterado nesta frente.

A saúde das fontes admitidas continua usando news_feed_runs, news_feeds.last_success_at e os relatórios de coleta do Bóris. Falta de notícias novas não remove automaticamente uma fonte.

## Verificação entregue

- Execução final local: **183 testes Python aprovados**, incluindo os seis de PostgreSQL real; **5 testes Node aprovados**. compileall e git diff --check passaram. CI de PR em .github/workflows/discovery-ci.yml repete a verificação sem secrets, crawler ou provedor de IA.
- Testes Python do projeto e testes novos de exploração, parser/extração, revisão, recência, cursor, orçamento, DNS/Host/SNI, timeout e inventário.
- Seis testes com PostgreSQL local PGlite executam os schemas e as funções Python reais: lease perdido/retomada; teto compartilhado; observação → revisão → admissão → próxima janela; rejeição; prioridade sem bloquear sites; RLS/permissões.
- PGlite é ferramenta opcional de teste; não foi adicionado ao runtime Python. Definir BORIS_PGLITE_MODULE para o index.js instalado de @electric-sql/pglite e executar pytest tests/test_discovery_postgres.py. Sem isso, esses seis testes são explicitamente pulados.
- Testes isolam os switches de produção; ativação futura do arquivo não inicia crawler durante pytest.
- Não foram medidos rendimento, qualidade editorial de fontes reais ou custos monetários.
