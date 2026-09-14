# Bóris — operação iniciada em 14/09/2026

Supabase e R2 passaram no preflight remoto; 16 testes passaram no runner. DATABASE_PASSWORD separado resolveu a conexão. DATABASE_URL é fallback.

Rotina habilitada no collect.yml por padrão: 00h/06h/12h/18h America/Sao_Paulo (03/09/15/21 UTC); recuperação +1h. Para pausar: variável ENABLE_COLLECTION=false. Cron GitHub é best effort, não garantia de pontualidade.

Primeira execução: https://github.com/zehlima/blog-criia-rss/actions/runs/34827810364
Snapshot SQL:1510 matérias,53 feeds tentados,0 textos de páginas extraídos. O processamento de páginas começa após RSS; snapshot parcial. Não declarar ciclo completo nem600 fontes concluídas. RSS pode também conter conteúdo arquivado em rss_content_key, distinto da extração de página.

Otimização aplicada: upsert em lotes de250 com URL única; uploads RSS paralelos antes da transação. SQL de inserção/atualização/associação testado remotamente com rollback. Execução antiga substituída preservando checkpoints; nova retomou fontes pendentes.

Pendências de validação: fechamento de600 feeds, textos de páginas, erros por fonte, volume/CPU/custo do ciclo e primeira execução agendada. Falhas de fonte e páginas bloqueadas continuam reportadas, sem promessa de cobertura integral. Nenhuma ação manual do usuário necessária agora.
