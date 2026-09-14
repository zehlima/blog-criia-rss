# Handoff Bóris — Supabase configurado

Projeto: blog-criia-rss
Organização: Criia (otsijsltcmdkfunsplnx)
Supabase ref: ikoqkeqxqfqkfjmcwwdq
Região: sa-east-1
Custo de criação confirmado pelo conector e usuário: US$ 0/mês.

Executado: projeto criado ACTIVE_HEALTHY; migration news_ingestion_schema aplicada; seis tabelas news_* com RLS e acesso anon/authenticated revogado; 600 feeds importados e contados por SQL; 0 artigos.
Security advisors: apenas seis INFO rls_enabled_no_policy, intencionais nesta fase privada. Referência: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy

Usuário confirmou salvar quatro secrets R2 no GitHub; valores e conexão ainda não testados. Pendente: DATABASE_URL com Session pooler porta5432; executar preflight e coleta real; habilitar ENABLE_COLLECTION após validação. Não há coleta em produção comprovada.
