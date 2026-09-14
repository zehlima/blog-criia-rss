# Bóris — migração Python — 14/09/2026

Estado: PYTHON_CODE_READY_ACCOUNTS_PENDING. Avanço estimado da migração: 75%.

O usuário aceitou substituir Worker/D1 por Python + GitHub Actions + Supabase + R2, para 600 feeds em todas as janelas de 00h/06h/12h/18h de Brasília, armazenando chamadas e textos das matérias. A autorização de execução permanece válida.

## Entregue

Código modular, schema PostgreSQL com RLS, configuração Actions, inventário original com 600 feeds ativos na lógica de coleta, extração automática, textos comprimidos e versionados em R2, conteúdo RSS preservado quando fornecido, upsert de metadados e retomada persistente. Guia CONFIGURAR.md com cinco secrets e comandos de setup/preflight/run. Agendamento protegido por ENABLE_COLLECTION até o teste inicial. Recovery uma hora após cada janela. Sem exclusão automática de notícias.

16 testes locais passaram, Python compila, YAML interpretado e SQL validado sintaticamente por pglast. Supabase/R2 não foram testados remotamente. Amostra de três fontes falhou no DNS do ambiente antes do HTTP; não prova indisponibilidade dos sites. Não foi executado o ciclo real de 600 feeds.

## Acessos

GitHub confirmou usuário zehlima. Buscas específicas blog/rss/criia nessa conta não identificaram o repositório oficial. Solicitar URL exata; não presumir inexistência nem publicar em repositório de outro projeto.

Plugin Supabase encontrado e sugerido; conexão ainda não confirmada. R2 sem integração encontrada nesta busca, requer configuração de bucket e credenciais via GitHub Secrets conforme guia.

Nenhum push oficial, deploy, criação de banco/bucket remoto ou ativação de cobrança foi realizado. Próximos passos: identificar Git, conectar Supabase, preparar secrets R2, rodar setup, preflight e primeiro ciclo, medir tempo/espaço/cobertura, depois habilitar schedule.

O handoff diário já está agendado para 00h America/Sao_Paulo na pasta Bóris. Este documento substitui a arquitetura do handoff anterior; os arquivos Worker v1 são históricos, não a implementação escolhida.

## Limites

Actions não garante minuto exato; recuperação reduz risco. Rotina pode precisar de várias execuções na carga inicial. Status partial não é sucesso completo; extracted não é validação editorial. Sites bloqueados não são contornados. Supabase/R2 gratuitos têm cotas finitas. A primeira coleta só pode descobrir os itens ainda disponíveis nos RSSs, não todo o arquivo histórico dos veículos.
