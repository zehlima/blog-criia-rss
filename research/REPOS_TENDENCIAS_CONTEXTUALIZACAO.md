# Bóris — repositórios para tendências e contextualização
Pesquisa concluída em 14/09/2026. Escopo: seleção técnica e desenho de integração, sem instalar componentes, executar benchmarks ou retomar a configuração da ingestão.

**Decisão:** começar com BERTopic + Sentence Transformers + datasketch; acrescentar StatsForecast quando houver histórico suficiente. BERTrend é o candidato especializado mais próximo do pedido de sinais emergentes, mas fica para um piloto posterior. Não encontrei, entre os avaliados, dois repositórios que entreguem toda a solução pronta, com validação probabilística e custo quase zero.

## 1. Seleção de 12 candidatos

A data abaixo é o último push informado pela API, não garantia de qualidade, versão publicada ou data do último commit na branch padrão. Os heads conferidos estão no JSON acompanhante. Licenças são as identificadas nos metadados/arquivos consultados; modelos e dependências precisam de conferência própria ao fixar a versão.

| Repositório | Função | Licença observada | Último push | Decisão e limite |
|---|---|---|---|---|
| [MaartenGr/BERTopic](https://github.com/MaartenGr/BERTopic) | Temas e evolução temporal | MIT | 2026-09-09 | adotar primeiro: Modelo de tópicos; exige camada própria de tendências e IDs estáveis. |
| [huggingface/sentence-transformers](https://github.com/huggingface/sentence-transformers) | Representação semântica multilíngue compartilhada | Apache-2.0 | 2026-09-11 | adotar primeiro: Não é contextualizador pronto; combinar semântica, entidades e tempo. |
| [Nixtla/statsforecast](https://github.com/Nixtla/statsforecast) | Previsão de séries de cobertura e validação temporal | Apache-2.0 | 2026-09-11 | adotar apos historico: Prevê séries numéricas; não lê notícias nem prevê adoção tecnológica. |
| [ekzhu/datasketch](https://github.com/ekzhu/datasketch) | Cópias e quase cópias lexicais | MIT | 2026-08-09 | adotar primeiro: MinHash não identifica sozinho paráfrases ou traduções. |
| [rte-france/BERTrend](https://github.com/rte-france/BERTrend) | Sinais fracos e evolução de tópicos | MPL-2.0 | 2026-09-11 | piloto posterior: Maior aderência funcional; dependências extensas e GPU recomendada. |
| [online-ml/river](https://github.com/online-ml/river) | Mudança de distribuição e aprendizado incremental | BSD-3-Clause | 2026-09-03 | opcional posterior: ADWIN detecta mudança; não equivale a probabilidade de futuro. |
| [moguiyu/NewsPrism](https://github.com/moguiyu/NewsPrism) | Mesmo evento, múltiplas fontes e perspectivas | MIT | 2026-09-13 | referencia produto: LLM e servidor no caminho padrão; adaptar políticas editoriais e persistência. |
| [sannuta/news-atom-lite](https://github.com/sannuta/news-atom-lite) | Eventos e afirmações atribuídas a fontes | MIT | 2026-05-12 | piloto posterior: Exige inferência LLM e avaliação; não garante resolução global de eventos. |
| [Priberam/projected-news-clustering](https://github.com/Priberam/projected-news-clustering) | Clustering multilíngue de notícias em fluxo | RESEARCH-ONLY; commercial license required | 2023-02-07 | referencia nao adotar: LICENSE.txt exige licença comercial; código antigo, componentes C# e serviços. |
| [ddangelov/Top2Vec](https://github.com/ddangelov/Top2Vec) | Descoberta de temas | BSD-3-Clause | 2024-11-14 | alternativa: Menor atividade recente; modo contextual beta com modelos específicos. |
| [aws-samples/news-clustering-and-summarization](https://github.com/aws-samples/news-clustering-and-summarization) | Arquitetura de notícias por evento | MIT-0 | 2026-02-14 | referencia nao adotar: Serviços AWS extras; não adequado à stack e orçamento inicial. |
| [vanam/Incremental-News-Clustering](https://github.com/vanam/Incremental-News-Clustering) | Clustering incremental | MIT | 2021-06-01 (arquivado) | descartar v1: Repositório arquivado; última atividade em 2021. |

Evidências que mudaram a seleção:
- BERTrend documenta classificação de sinais e comparação temporal. Recomenda GPU com 16 GB e tem ampla lista de dependências. O README pede Python 3.13, enquanto pyproject.toml declara >=3.12: a compatibilidade deve ser testada, não presumida. [README](https://github.com/rte-france/BERTrend) · [dependências](https://github.com/rte-france/BERTrend/blob/main/pyproject.toml).
- Priberam não pode ser tratada como BSD irrestrita: o cabeçalho do [LICENSE.txt](https://github.com/Priberam/projected-news-clustering/blob/master/LICENSE.txt) condiciona o uso comercial a licença específica.
- No exemplo AWS, o [LICENSE](https://github.com/aws-samples/news-clustering-and-summarization/blob/main/LICENSE) atual é MIT-0; há referência divergente a Amazon Software License na documentação indexada. O descarte inicial é por arquitetura/custo, não por assumir proibição de uso.
- NewsPrism reúne eventos e perspectivas, mas traz filtros editoriais próprios, preferência de saída em chinês e chamadas LLM. Não copiar seus pesos ou exclusões de fontes automaticamente.
- Top2Vec contextual declara beta e restringe modelos suportados; o suporte multilíngue da biblioteca não deve ser confundido com suporte de cada modo.

## 2. Motor de contextualização: executar antes dos rankings

Proposta de engenharia, ainda não implementada:
1. Receber ID da matéria, URL, veículo, país editorial da fonte, idioma, texto, data publicada, primeira observação e versão do conteúdo.
2. Identificar cópias exatas pelo hash e quase cópias com datasketch/MinHash. Manter todas as URLs e atribuições. Republicação não deve desaparecer da contagem de alcance, nem virar evidência independente automaticamente.
3. Gerar embeddings multilíngues uma única vez por versão do conteúdo e reutilizá-los nos dois motores.
4. Buscar candidatos em uma janela temporal e comparar entidades, ação, objeto, lugar e data. Similaridade textual é um filtro, não prova de identidade de evento. Duas matérias sobre chips podem tratar de fatos diferentes.
5. Criar relações matéria↔evento de muitos para muitos: uma reportagem pode cobrir vários acontecimentos. Manter topic_id separado de event_id.
6. Vincular eventos entre países no mesmo espaço semântico. Agregar por continente e global a partir das relações, sem somar rankings locais nem duplicar o evento.
7. Produzir resumo factual com atribuição, divergências e URLs. Para economizar, síntese por modelo de linguagem apenas nos eventos selecionados; análises de todos os textos usam blocos de texto, não apenas o título.

**Modelo candidato:** intfloat/multilingual-e5-small, utilizável em Sentence Transformers. Seu model card informa 384 dimensões, 100 idiomas com qualidade desigual e limite de 512 tokens. Usar blocos para textos extensos e prefixo query: nas tarefas simétricas; respeitar o limite incluindo o prefixo. Calibrar limiares com nossa amostra: cosseno alto não é probabilidade de ser o mesmo evento. [Model card](https://huggingface.co/intfloat/multilingual-e5-small).

A saída precisa distinguir:
- quantidade de matérias únicas;
- quantidade de veículos únicos;
- quantidade de grupos editoriais conhecidos;
- quantidade de famílias de republicação estimadas;
- países com cobertura, países mencionados e país do acontecimento;
- perspectivas e alegações com suas fontes;
- confiança do agrupamento e cobertura incompleta.

“País da fonte” não significa “país do acontecimento”. Os rankings devem se chamar “nos veículos monitorados de cada país”, e não “tudo que o país pensa”. Se a origem editorial ou relação societária for desconhecida, registrar desconhecido; não inferir independência só pelo domínio.

**Nota proposta, não calibrada:** ordenar inicialmente por veículos únicos, com desempate por diversidade editorial e novidade. Uma nota de 0 a 100 pode ser o percentil desse indicador dentro do mesmo país e janela, exibindo os componentes. Não chamar essa nota de veracidade, impacto econômico ou probabilidade. Contagens globais devem usar DISTINCT e separar participação de países de volume bruto.

## 3. Motor de tendências: presente, direção e memória

BERTopic organiza assuntos e representações ao longo do tempo. Sua documentação distingue modelagem dinâmica e incremental; partial_fit exige componentes compatíveis, como IncrementalPCA e MiniBatchKMeans, e não se acopla simplesmente a um modelo treinado por fit. [Dinâmico](https://maartengr.github.io/BERTopic/getting_started/topicsovertime/topicsovertime.html) · [Incremental](https://maartengr.github.io/BERTopic/getting_started/online/online.html).

Proposta inicial:
- Atualizar indicadores após cada uma das quatro janelas. Fazer descobertas/reorganização de temas em lote separado, com periodicidade ajustada após medir custo; não retreinar tudo quatro vezes ao dia.
- Medir volume, veículos, diversidade, novidade e velocidade de crescimento nas janelas de 6 h, 24 h, 7 e 30 dias.
- Manter painel de fontes comparáveis e registrar feeds com falha. Fonte indisponível gera dado ausente, não zero. Uma nova fonte ou recuperação da coleta não pode aparecer como explosão de interesse.
- Normalizar por fontes e volume efetivamente observados. Comparar mesma hora/dia da semana quando houver histórico para isso.
- Distinguir surgimento de novo assunto, aumento de assunto conhecido e mera republicação de um release.
- Manter topic_id estável, versões do modelo e mapa de fusões/divisões; mudanças de clusters não podem produzir tendência artificial.
- Explicar direção por evidência: por exemplo, mudança de “anúncios de IA” para “contratações e implantações de IA”. Isso exige classificar ações/estágios e preservar citações, não apenas contar palavras.

BERTrend pode ser comparado posteriormente ao baseline, reaproveitando os embeddings. River/ADWIN é uma opção para mudança de distribuição, não prioridade em um processo que roda em quatro lotes por dia.

## 4. O que significa “a gente previu e acertou”

Há dois alvos diferentes:
1. **Crescimento de cobertura:** determinado tema ganhará presença na imprensa monitorada.
2. **Adoção real da tecnologia:** empresas, investimentos ou usuários efetivamente crescerão.

Os RSSs permitem testar diretamente o primeiro. O segundo exige definir e coletar evidências externas de adoção. Repetição jornalística não confirma, por si, sucesso econômico.

StatsForecast oferece modelos estatísticos, intervalos e validação temporal para as séries numéricas; não interpreta o texto. Começar com baseline simples e comparar modelos, sem adotar automaticamente o mais complexo. [Projeto](https://github.com/Nixtla/statsforecast) · [Validação temporal](https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/crossvalidation.html).

Antes de uma previsão ser publicada, gravar:
- prediction_id, topic_id e país;
- generated_at, data_cutoff, horizonte e alvo verificável;
- valor previsto e intervalo; probabilidade somente se estimada/calibrada para o evento definido;
- versão de modelo, versão da taxonomia, cobertura e IDs das evidências;
- resultado observado e avaliação adicionados depois, sem reescrever a previsão original.

Exemplo de alvo a definir no piloto: “a participação deste tema em veículos monitorados crescerá acima de um limiar predefinido nos próximos sete dias”. Limiar, população de fontes e tratamento de falhas devem ser congelados antes da avaliação.

Fazer backtest com cortes cronológicos: treinar somente com informação disponível até cada corte. Não ajustar tópicos em todo o histórico, incluindo o futuro, e depois declarar que o modelo já sabia. Preservar textos como vistos na época; uma atualização posterior da matéria também pode vazar informação.

Registrar todas as previsões, inclusive erros e casos inconclusivos. Avaliar erro das séries, cobertura dos intervalos, precisão dos alertas e, havendo probabilidades de evento, Brier score/calibração. Trinta dias dão contexto inicial, não garantia de probabilidade confiável; séries esparsas ficam como histórico insuficiente. O teste começa com previsões registradas prospectivamente.

## 5. Custos e integração na arquitetura existente

A vantagem da seleção é permitir inferência local/CPU sem tarifa de API por matéria no caminho básico. Isso não comprova que caberá na franquia de hospedagem. Não foi executado benchmark com nossos textos e não há estimativa monetária validada.

Proposta:
- Separar ingestão de análise para uma não bloquear a outra.
- Processar apenas artigos novos/alterados; cache por content_hash + revisão do modelo.
- Persistir checkpoints por lote. Não depender do cache temporário do runner como única memória.
- Guardar textos, blocos e vetores históricos em arquivos no R2; índices/centroides e agregados compactos podem ficar no banco conforme medição.
- Um vetor de 384 float32 ocupa 1.536 bytes brutos; 100 mil vetores ocupam 153,6 MB decimais, sem índices ou metadados. Blocos por matéria multiplicam esse volume. Evitar colocar todo o histórico vetorial no pequeno banco.
- Considerar ONNX/quantização em CPU após comparar qualidade. [Documentação oficial](https://sbert.net/docs/sentence_transformer/usage/efficiency.html).
- Contabilizar textos com extração incompleta: se só há chamada/resumo, não afirmar que a análise leu a matéria integral.
- LLM opcional para sínteses dos principais eventos, com limite de entrada/saída e orçamento explícito. Nenhuma conta/modelo pago foi ativado nesta pesquisa.

Contrato futuro para o front: events, article_event_links, topic_snapshots, trend_signals, predictions e prediction_outcomes, com IDs, timestamps, country_scope, source_counts, coverage_status, model_version e evidence_article_ids. São propostas de entidades, não tabelas já criadas.

## 6. Piloto recomendado quando a ingestão estiver funcionando

1. Montar amostra rotulada com mesmo evento, eventos parecidos mas diferentes, traduções e republicações; incluir idiomas de baixa cobertura.
2. Avaliar agrupamento por evento (precisão/recall e erros de fusão), separação de republicações, país da fonte versus país do fato e integridade das evidências.
3. Medir CPU, RAM, duração, bytes e quantidade de blocos por matéria; comparar execução padrão com ONNX/quantização quando justificável.
4. Executar rankings em modo de observação. Comparar volumes brutos versus deduplicados para detectar inflação.
5. Construir histórico consistente, registrar previsões sem publicação automática e medir resultados antes de alegar capacidade preditiva.
6. Só então decidir se BERTrend e extração de afirmações do News Atom Lite melhoram o baseline o suficiente para justificar custo.

**Entrega desta etapa: pesquisa 100%. Implementação destes motores: 0%.** A ingestão continua pausada a pedido do usuário. O último bloqueio conhecido é a autenticação do banco; não foi retomada nem alterada nesta pesquisa.
