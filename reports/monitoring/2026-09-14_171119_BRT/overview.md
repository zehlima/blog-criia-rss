# BLOG CRIIA — fechamento da coleta 17:11 BRT

- GitHub Actions: `34891310949`
- Janela lógica: `2026-09-14T15:00:00Z`
- Inventário ativo derivado de `data/feeds.json`: 675 URLs únicas
- Tentados: 675/675 (100%)
- Feeds OK: 649
- Feeds com erro: 26
- Feeds ainda não tentados: 0
- Notícias únicas ligadas ao inventário ativo: 24.419
- `content_key`: 23.181, dos quais 23.176 são corpos válidos
- Texto extraído da página: 22.305
- Conteúdo oferecido pelo publisher no RSS: 871
- Somente título/resumo: 0
- Extrações indisponíveis: 1.236
- Referências inválidas: 7
- Estado: `complete_with_gaps`

Cobertura de tentativa dos 675 feeds não significa integralidade da coleta. Cinco registros com `content_key` não foram contados como corpo válido. O inventário histórico do banco contém 774 feeds, mas as métricas acima estão restritas às 675 URLs ativas.

## Separação das pendências

- `feed_errors.csv` e `feed_errors.md`: os 26 endpoints RSS que falharam, com erro original, classificação e ação recomendada.
- Feeds não tentados: nenhum nesta rodada.
- `extraction_failures.csv.gz`: 1.236 matérias cuja extração de página terminou indisponível. Esses casos são separados das falhas de RSS.

Classificação dos 26 endpoints: 20 bloqueios de acesso, 2 respostas com formato inválido, 1 falha temporária/rate limit, 1 TLS, 1 feed vazio e 1 endpoint ausente. Nenhuma substituição definitiva foi aplicada sem validação técnica e editorial.
