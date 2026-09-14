# Bóris — conexão por senha separada

Status: bloqueado antes da primeira coleta. Em 2026-09-14, run GitHub 34819787504, tentativa2, job103899959512: 16 testes passaram; Supabase retornou senha rejeitada. R2 ainda não validado. 600 feeds cadastrados, última contagem verificada 0 artigos.

Correção implementada no Git: DATABASE_PASSWORD é passado diretamente ao psycopg, sem edição ou escape de URI. Configuração do host e usuário verificados no print fica nos workflows. DATABASE_URL permanece como fallback. Os 16 testes locais passaram após a alteração.

Próximo passo necessário do usuário: criar secret DATABASE_PASSWORD contendo somente a senha atual do banco. Então iniciar bootstrap por push no arquivo .github/workflows/bootstrap.trigger e verificar preflight + coleta. Agendamento continua bloqueado por ENABLE_COLLECTION até validação.

Revisão identificou pendências de robustez para tratar após conexão: falha de persistência pode interromper ciclo; item inválido descarta feed; não declarar cobertura ou rotina ativa antes de medição.
