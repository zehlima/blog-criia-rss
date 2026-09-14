# BLOG CRIIA — implantação do motor de assuntos

Data: 14/09/2026. Estado deste checkpoint: implantado e em execução inicial; rankings ainda NÃO validados até este registro.

## Repositório e execuções
- https://github.com/zehlima/blog-criia-rss
- Implementação inicial: 51c07c428b3a225da280a4b1193478967ccbaf9f
- Vínculo imutável da análise ao ciclo: eefa678ce1e95e4eef04854884decf261853b896
- Gravação de textos em lotes e distribuição entre domínios: 89a4005e72cec8e38734bbea412ee3a819be51db
- Análise inicial: https://github.com/zehlima/blog-criia-rss/actions/runs/34840180581
- Recuperação da coleta: https://github.com/zehlima/blog-criia-rss/actions/runs/34840542353

## Comprovado
- 28 testes locais aprovados.
- A execução inicial no GitHub passou pelas dependências, testes e conexão real Supabase/R2; chegou ao processamento do corpus.
- Projeto Supabase ikoqkeqxqfqkfjmcwwdq; três tabelas aditivas criadas: news_analysis_runs, news_topic_snapshots, news_collection_attempts.
- RLS habilitado e acesso anon/authenticated revogado nas três. Auditoria sem ERROR/WARN; apenas INFO de RLS sem políticas, esperado porque estes dados são privados e usados pelo worker.
- Workflows configurados para 00/06/12/18h BRT e recuperação +1h.
- Análise acionada após encerramento da coleta. País/continente/globo têm alvos +15/+20/+25 minutos, com atraso real registrado se fila/preparação excederem o alvo.
- Automação horária 6aa7bf8fe5a0819182fc936aefb3b422 ampliada para consultar os snapshots e trazer os resultados à conversa, mantendo devolutiva de erros e registros no Drive.
- Nenhuma nova credencial foi pedida ou conta paga de IA ativada.

## Estado inicial de dados, antes desta recuperação
600 feeds tentados, 479 OK, 121 erros, 15.624 notícias, 1.625 textos extraídos, 13.448 pendentes e 551 indisponíveis.
Essas contagens pertencem ao ciclo anterior e devem ser atualizadas consultando o banco; não são contagens finais desta implantação.
Os 600 feeds não incluem América do Sul/Brasil. Preservar essa lacuna nos resultados.

## Causa do failure anterior
A execução atingiu o orçamento de 30 minutos com pendências, gravou checkpoint parcial e encerrou deliberadamente com exit code 2. A nova versão diferencia checkpoint parcial (warning e contagens) de falha operacional. Não altera pendente para concluído.
O acesso a parsed.version em feed vazio podia gerar AttributeError; corrigido para leitura defensiva e classificação de formato inválido.

## Continuação exata
1. Consultar news_analysis_runs id 34840180581 e os jobs do workflow.
2. Se failed, ler logs sanitizados e corrigir a causa sem refazer credenciais que já passaram no preflight.
3. Se ready, verificar três escopos em news_topic_snapshots com mesmo run_id, horários, contagens e evidências.
4. Validar amostra de tópicos e comparações país/continente/globo; temas são estimados, não acontecimentos confirmados.
5. Conferir a recuperação 34840542353: checkpoint imutável, CSV/Markdown no R2 e artifacts; confirmar que seu encerramento aciona a próxima análise.
6. Atualizar este handoff e devolver contagens ao usuário. Não declarar 100% nem produção integralmente validada antes disso.

## Configuração, código e resultados
Consulte OPERACAO_TENDENCIAS.md. Modelos e código estão em trends/; extração em collector/; banco em sql/001_schema.sql. Credenciais permanecem em GitHub Secrets.
Resultados persistem em R2 analysis/runs/<id>/ e em public.news_topic_snapshots; sumários e artifacts no GitHub. Frequência usa a janela de 24 horas, com auditoria de todo o corpus. Não há previsão estatística ou taxa de crescimento validada nesta versão.
