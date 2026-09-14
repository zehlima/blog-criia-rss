# Fechamento diário semântico

Dia civil: 00:00 inclusive até 00:00 exclusivo do dia seguinte, America/Sao_Paulo.
Executa após a coleta da janela 00h terminar em complete/complete_with_gaps. Uma coleta parcial aguarda a recuperação dessa mesma janela. Os disparos de outras janelas são descartados antes de instalar os modelos.

## Regras de contagem

- Publicações: URLs distintas com data de publicação no dia. Sem data: primeira descoberta, identificada como fallback. Uma publicação do dia encontrada na coleta de fechamento ainda entra no dia correto.
- Aparições em RSS: observações distintas por slot de seis horas, feed e URL. HTTP 304 preserva os itens recentes; retry não multiplica aparições. Aparecer no feed outra vez não é publicar outra vez.
- Textos distintos: famílias estimadas por corpo normalizado idêntico ou início quase idêntico, com título compatível. Todas as combinações internas precisam cumprir a regra; cadeias A~B~C não bastam.
- Cópias adicionais estimadas: publicações menos famílias de textos. Nenhuma matéria é apagada.
- Pautas: agrupamento semântico separado da deduplicação, com concordância de título e início do texto e regras editoriais já existentes. Uma pauta pode conter várias matérias originais.
- País refere-se à origem editorial do veículo. Contabilidade de continente e globo é recalculada sobre IDs únicos, não pela soma dos países.

## Motor e limites

Reutiliza sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 na revisão fixada e datasketch/MinHash. Título e primeiros 1.200 caracteres do texto recebem representações separadas, com limite de 256 tokens por entrada. Texto de RSS e título/resumo ficam identificados separadamente do texto extraído da página.

Busca candidatos pelos 32 vizinhos semânticos mais próximos, MinHash e hashes exatos. A busca é aproximada; não há garantia de encontrar todas as duplicações. Scores não são probabilidades calibradas. Equivalência semântica sem semelhança textual forte vira candidata a republicação e requer revisão, em vez de reduzir automaticamente a contagem.

O primeiro dia possui lacuna de observações: o sistema anterior só mantinha o último avistamento. Não reconstruímos artificialmente aparições antigas. O relatório inclui cobertura dos feeds, corpos ausentes, datas inferidas e quantidade de lotes observados frente aos esperados.

Corpos idênticos com títulos semanticamente incompatíveis são tratados como suspeita de extração de texto comum do site. Esses corpos ficam fora da deduplicação e da similaridade temática; os registros continuam na contabilidade. A v2 incorpora essa proteção após encontrar 42 URLs com assuntos distintos e o mesmo conteúdo extraído.

## Operação e armazenamento

- `.github/workflows/daily.yml`: `workflow_run` da coleta, entrada manual auto/preview; push no trigger executa prévia real.
- `news_article_observations` e `news_observation_batches`: histórico privado, com RLS e sem acesso anon/authenticated.
- `news_daily_closures`: índice privado dos fechamentos. Fechamento final é idempotente por versão/dia; prévias têm IDs próprios.
- R2 `daily/runs/<id>/report.json.gz` e `report.md`: dados, rankings por país/continente/globo e evidências por par. Leitura de retorno validada antes de gravar fechamento no banco.
- GitHub Actions: artefato `fechamento-diario`, resumo e relatório por execução. Não altera a usabilidade nem publica artigos editoriais.

Testes cobrem virada do dia, gate pós-meia-noite, título igual/corpo diferente, mesmo corpo/títulos diferentes, traduções candidatas, números conflitantes, texto ausente, CJK, cadeias de similaridade, duplicação entre países e retries.

Referências dos componentes: https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html e https://ekzhu.com/datasketch/lsh.html
