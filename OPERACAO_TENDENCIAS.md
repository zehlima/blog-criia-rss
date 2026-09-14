# Operação BLOG CRIIA — motor de assuntos v1

## Configuração já existente
- Repositório: zehlima/blog-criia-rss, branch main.
- Supabase: ikoqkeqxqfqkfjmcwwdq; conexão Session pooler, TLS, porta 5432.
- GitHub Secrets: DATABASE_PASSWORD, R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET. DATABASE_URL é fallback legado.
- Host e usuário ficam nos workflows; nenhuma chave de IA paga é necessária.
- R2 privado: blog-criia-articles; textos, cache vetorial e relatórios.

## Execução
- Coleta: 00h/06h/12h/18h America/Sao_Paulo (03h/09h/15h/21h UTC).
- Recuperação: uma hora depois, com retomada dos pendentes.
- Limite de 30 minutos por execução da coleta; pendências ficam no banco. Não implica que 30 minutos bastam para drenar o estoque inicial.
- Finalização parcial é checkpoint válido com warning e contagens explícitas; exceções operacionais continuam falhando.
- Ao concluir Coleta global RSS, o workflow Tendencias pais continente globo prepara um snapshot imutável.
- País/continente/globo são programados para +15/+20/+25 minutos do encerramento da coleta. Se a preparação ou a fila do GitHub exceder esse prazo, publicam depois e registram o atraso. Não há garantia de pontualidade exata do GitHub Actions.
- Execução manual inicial: push do arquivo .github/workflows/trends.trigger; recuperação manual: push de .github/workflows/collect.trigger. Também há workflow_dispatch.

## O que o motor faz
1. Lê todas as matérias já cadastradas até o corte e os textos disponíveis no R2.
2. Processa texto extraído em blocos de até 450 tokens com multilingual-e5-small (Sentence Transformers), prefixo query:, média normalizada; títulos/resumos usados quando o corpo não está disponível. Falhas de leitura são explícitas.
3. Cache persistente no R2 por hash da entrada e versão do pipeline, com revisão do modelo fixada na primeira execução e reaproveitada.
4. BERTopic + HDBSCAN descobre temas nas matérias publicadas nas últimas 24 horas. Sem data de publicação, usa first_seen_at e contabiliza essa limitação. Históricas são processadas/cacheadas, mas não aparecem como assunto novo do dia.
5. IDs de temas reaproveitados quando o centro semântico é suficientemente similar; não são IDs de acontecimentos confirmados. Limiar 0,92 é heurístico, ainda não calibrado.
6. MinHash propõe famílias de republicação; Jaccard exato >=0,85 confirma semelhança lexical ao representante. Traduções não são deduplicadas como cópias automaticamente.
7. Um único conjunto de temas alimenta os três níveis. Matéria presente em vários países conta uma única vez no globo. Veículos são domínios distintos, não necessariamente grupos editoriais independentes.
8. Ranking por veículos distintos, depois matérias. Título representativo é rótulo do tema, no idioma original. Mostra URLs de evidência, famílias estimadas e matérias sem agrupamento.

## Limites visíveis
- Os 600 feeds atuais NÃO incluem América do Sul/Brasil; não apresentar cobertura global como exaustiva.
- Oriente Médio agrega na Ásia; Egito na África; Rússia e Turquia têm grupo transcontinental explícito.
- País representa origem editorial do veículo, não local do evento.
- Matérias sem corpo extraído são análises de título/resumo, não leitura integral.
- Modelagem de temas não verifica veracidade nem garante identidade de evento.
- Ainda não há série comparável validada para taxas de crescimento, StatsForecast ou previsões. Frequência observada é entregue; previsão não é simulada.
- Extração pode continuar com 403, robots.txt, 404 e indisponibilidade; sem contornar restrições.
- CPU sem tarifa de API não significa custo total zero: medir GitHub, armazenamento e operações R2 no uso real.

## Resultados e diagnóstico
- public.news_analysis_runs: execução, cutoff, versão, cobertura, snapshot e erro.
- public.news_topic_snapshots: resultados por país/continente/globo, horários planejado/real e caminho R2.
- R2 analysis/runs/<run_id>/: snapshot, auditoria do corpus e relatórios JSON/Markdown dos três níveis.
- GitHub Actions: Job Summary e artifacts (30 dias); R2 preserva resultados após expiração do artifact.
- reports/collection/: devolutiva CSV/Markdown e resumo por encerramento no R2; artifact também no GitHub.
- Estados: building/ready/failed. ready significa snapshot preparado; só três escopos persistidos confirmam as três publicações.

## Rollback
Pausar o workflow de tendências no GitHub; manter coleta. Reverter somente o commit de implementação se necessário. Tabelas novas são aditivas e podem permanecer sem uso. Não apagar matérias nem objetos históricos.

## Validação inicial
24 testes locais aprovados, incluindo contagens globais sem soma duplicada, famílias de republicação, países, datas, outliers e erros do coletor. Execução real deve ser registrada após o deploy com ID do workflow e contagens verificadas; não presumir aprovação a partir dos testes locais.
