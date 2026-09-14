# Configuração operacional — BLOG CRIIA

A infraestrutura existente está conectada. Não é necessário recriar contas, banco, bucket ou credenciais.

## Acessos existentes

- GitHub: https://github.com/zehlima/blog-criia-rss
- Supabase: projeto `ikoqkeqxqfqkfjmcwwdq`, Session pooler na porta 5432.
- R2: bucket privado `blog-criia-articles`.

Os workflows usam `DATABASE_PASSWORD` (somente senha), `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` e `R2_BUCKET`. `DATABASE_URL` é uma alternativa antiga, ignorada quando a senha separada está presente. Valores ficam somente nos Secrets; não inserir no Git ou no painel web.

## Execução

Actions → Coleta global RSS → Run workflow → `preflight` confere banco e R2; `run` coleta/retoma. O inventário ativo vem de `data/feeds.json`; registros históricos permanecem no banco. O modo `setup` é de instalação e não precisa ser repetido na operação atual.

Janelas: 00h, 06h, 12h e 18h de Brasília (03h, 09h, 15h e 21h UTC), com recuperação nas demais horas. O orçamento é de até 50 minutos por execução e termina antes da próxima janela quando ela estiver próxima. O timeout externo é de 65 minutos. A fila tem 16 trabalhadores e cadência por domínio. Há proteção contra coletores simultâneos. Push explícito de correção no arquivo `collect.trigger` substitui uma execução antiga; disparos agendados aguardam sua vez.

Para pausar apenas o agendamento, definir a variável de Actions `ENABLE_COLLECTION=false`. A ausência dessa variável mantém o agendamento habilitado. GitHub Actions pode atrasar disparos; os horários são alvos, não garantia de pontualidade.

## Como interpretar o resultado

- `complete`: sem pendências ou lacunas registradas naquele encerramento.
- `complete_with_gaps`: tentativa encerrada, com fontes/textos indisponíveis identificados.
- `partial`: há fontes não tentadas ou textos aguardando processamento/retentativa.
- Falha operacional: exceção de execução, reportada com código de erro.

Um checkpoint parcial válido retorna código zero, com aviso explícito e contagens. Sucesso técnico do job não equivale a coleta integral. `pending` significa ainda aguardando; `unavailable` registra tentativa sem texto disponível; `extracted` é extração automática da página; `rss_content` é conteúdo disponibilizado pelo próprio RSS, que pode ser parcial. Nenhum dos dois garante integralidade editorial.

Os limites de corpo são 32 MiB para RSS e 8 MiB para páginas; não há truncamento silencioso. Bloqueios de acesso, regras de robots e falhas TLS não são contornados. Resumos não são classificados como textos completos.

## Relatórios e tendências

Cada encerramento salva um registro imutável em `news_collection_attempts`, resumo e relatórios de erros em artefatos do Actions e no R2. `news_runs` representa o estado mutável da janela; consultar o registro imutável para comparar ciclos. `feed_errors.csv` identifica fonte, país, endereço e ação; `extraction_errors.csv` identifica páginas indisponíveis e próxima tentativa.

O motor processa o inventário de matérias até o corte e publica frequência das últimas 24 horas. Usa títulos para agrupamento semântico; textos disponíveis também são lidos para estimar republicações. País representa origem editorial do veículo, não o local do acontecimento. Matérias sem grupo permanecem visíveis. Contagens globais não somam matérias repetidas entre países. Crescimento/previsão não está validado.

Os três relatórios têm alvos de 15, 20 e 25 minutos após a coleta. O horário real e o atraso ficam registrados. Agrupamentos automáticos exigem avaliação editorial; a amostra de calibração não é prova de acurácia geral.

O painel continua sem publicação até a definição dos próximos motores. Credenciais do banco e R2 não devem entrar no navegador.
