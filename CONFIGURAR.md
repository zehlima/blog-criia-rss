# Bóris Python — configuração para Zé

Conexão Supabase e escrita/leitura/exclusão R2 validadas em 14/09/2026. A primeira coleta está em execução. O agendamento está habilitado por padrão; resultado completo e cobertura ainda em validação.

## 1. GitHub — informar o repositório

Git oficial confirmado: https://github.com/zehlima/blog-criia-rss . A conta conectada `zehlima` tem permissão de escrita.

Se ainda não existe, crie um repositório em https://github.com/new com nome sugerido `blog-criia-rss`. Para usar runners padrão gratuitamente, o repositório precisa ser público; em privado, há franquia de minutos. Escolha a visibilidade conscientemente. Somente código/configuração e lista de fontes entram no Git: credenciais em Secrets, textos no bucket privado.

## 2. Supabase — criar o banco gratuito

Instale/conecte a integração Supabase sugerida nesta conversa. Crie um projeto dedicado em uma organização Free, nome sugerido `blog-criia-rss`. Posso executar o SQL por essa integração depois de conectado e identificado o projeto.

No painel https://supabase.com/dashboard :

1. New project → nome `blog-criia-rss` → plano Free → senha forte do banco.
2. Aguarde o projeto ficar pronto.
3. Clique **Connect → Session pooler**, porta **5432**. Copie a URI PostgreSQL substituindo o campo de senha pela senha do banco. Se a senha tiver caracteres reservados, use a representação percent-encoded na URI.
4. Essa URI será o secret `DATABASE_URL` no GitHub. Ela não é a URL da API nem a chave anon.

Use o **Session pooler**, não Transaction pooler 6543: esta implementação usa um lock de sessão para impedir sobreposição. A conexão usa TLS e funciona em ambientes IPv4 como o runner do GitHub.

O SQL está em `sql/001_schema.sql`; o modo `setup` também o executa automaticamente e carrega todos os 600 feeds. Não precisa fazer as duas coisas. As tabelas têm prefixo `news_`, não apagam dados existentes e começam sem leitura pública. O front será configurado na próxima fase, sem expor a senha do banco.

## 3. Cloudflare R2 — criar o arquivo de textos

No painel https://dash.cloudflare.com :

1. R2 Object Storage → criar bucket **Standard**, nome `blog-criia-articles`.
2. Mantenha o bucket **privado**: não habilite r2.dev nem domínio público nesta fase.
3. Em gerenciamento de tokens do R2, crie credenciais S3 com **Object Read & Write**, limitadas a esse bucket.
4. Guarde o **Access Key ID**, **Secret Access Key** e o **S3 API endpoint** exibidos pelo R2. O endpoint tem formato `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`; use o valor real do painel, inclusive eventuais variantes regionais.
5. Se a Cloudflare solicitar habilitar faturamento, confira a franquia e o painel de consumo antes de continuar. A franquia não é bloqueio automático contra excedentes.

## 4. GitHub — cinco Secrets

No repositório: **Settings → Secrets and variables → Actions → Secrets → New repository secret**.

| Nome exato | Valor a inserir diretamente no GitHub |
|---|---|
| DATABASE_PASSWORD | Somente a senha atual do banco; tem prioridade sobre DATABASE_URL |
| DATABASE_URL | Alternativa antiga; ignorada quando DATABASE_PASSWORD está preenchido |
| R2_ENDPOINT_URL | Endpoint S3 do R2 |
| R2_ACCESS_KEY_ID | Access Key ID do R2 |
| R2_SECRET_ACCESS_KEY | Secret Access Key do R2 |
| R2_BUCKET | `blog-criia-articles` ou o nome real escolhido |

As credenciais são inseridas nesses campos; não é necessário compartilhá-las na conversa nem nos arquivos.

## 5. Primeiro teste, com agendamento ainda desligado

Depois que o código estiver na branch padrão do repositório:

1. **Actions → Coleta global RSS → Run workflow → mode: setup**. Cria as tabelas e importa os 600 feeds.
2. Aguarde sucesso. Execute novamente com **mode: preflight**. Confere 600 feeds no banco e grava/lê/remove um pequeno objeto de teste no R2.
3. Aguarde sucesso. Execute com **mode: run**. Esse é o primeiro ciclo real; todos os 600 serão tentados, dentro do orçamento de tempo por execução.
4. Veja o resumo do job e a tabela `news_runs` no Supabase. `partial` exige olhar feeds com erro, fontes não tentadas e textos pendentes. `extracted` significa extração automática, não revisão humana do texto completo.
5. Se o tempo acabar, rode `run` novamente na mesma janela. Os feeds já concluídos são pulados; os artigos pendentes ficam no banco e a coleta retoma. Não há limite artificial de número de matérias por feed.

Uma execução `partial` termina com código 2 e aparece vermelha no GitHub; é intencional, para não esconder cobertura incompleta. Falhas de fonte não apagam matérias já armazenadas. A próxima janela tenta novamente os 600 feeds.

## 6. Ligar a rotina

A rotina está habilitada por padrão após o teste remoto de Supabase/R2. Não é necessário criar uma variável para ligar. Para PAUSAR disparos agendados, em **Settings → Secrets and variables → Actions → Variables**, defina:

```text
ENABLE_COLLECTION = false
```

Execuções manuais continuam disponíveis. A condição está em `.github/workflows/collect.yml`.

O arquivo `.github/workflows/collect.yml` agenda **00h,06h,12h,18h de Brasília**. Em UTC: 03h,09h,15h,21h. Uma execução de recuperação às 01h/07h/13h/19h de Brasília retoma pendências da mesma janela, sem iniciar uma quinta rodada lógica dos 600.

GitHub Actions pode atrasar ou perder disparos. A recuperação reduz o risco, mas não é garantia de pontualidade. Sem atividade no repositório público por 60 dias, o GitHub pode desabilitar schedules; acompanhar Actions faz parte da operação. Se precisar de horário garantido, revisaremos o agendador depois da medição.

## O que medir antes de dizer que cabe no gratuito

- Duração do primeiro ciclo e das execuções seguintes.
- Fontes tentadas/600, fontes com sucesso e fontes com erro.
- Total de matérias, textos extraídos e textos indisponíveis.
- Bytes comprimidos escritos no R2 e espaço ocupado no Supabase.
- Minutos de Actions se o Git for privado; cota é compartilhada na conta.

O Supabase Free tem 500 MB de banco; R2 Standard inclui 10 GB-mês e franquias de operações. Essas cotas são finitas e o histórico cresce. Não há exclusão automática de notícias nem promessa de custo zero indefinido. O limite de execução está inicialmente em 30 minutos, com timeout do job em 40 minutos, e quatro requisições concorrentes com cadência por domínio. A primeira carga pode precisar de retomadas.

## Atualização e consumo futuro

Metadados e ligação com todas as fontes ficam no Supabase. Textos UTF-8 comprimidos em gzip ficam no R2, em chaves por hash de URL/conteúdo. Cada mudança de texto cria uma versão imutável; a tabela aponta para a mais recente. Upload ocorre antes de atualizar o ponteiro no banco. Uma interrupção entre essas operações pode deixar um objeto órfão reutilizável no retry, sem apontar o banco para um objeto inexistente.

Quando o próprio RSS entrega `content`, esse conteúdo também é preservado comprimido no R2, como JSON da lista original, em `rss_content_key`. Ele pode ser um texto integral ou parcial; é separado da extração da página. `compressed_bytes_written` mede os uploads de textos extraídos da página nesta execução; não inclui arquivos de conteúdo RSS nem mede o total do bucket, que deve ser consultado no painel do R2.

Páginas presentes no feed mais recente são rechecadas a cada janela, mesmo em RSS 304; textos nunca obtidos continuam na fila de tentativas com backoff. Páginas que saíram dos feeds e já têm texto ficam arquivadas, sem varredura eterna do histórico. XML/HTML acima de 8 MiB falha explicitamente, não é truncado. Robots, bloqueios, paywalls e extração insuficiente ficam registrados como pendência; não são contornados. Conteúdo extraído automaticamente pode conter omissões e exige avaliação na próxima fase.

O RSS só disponibiliza uma lista recente: a primeira coleta captura o que estiver disponível naquele momento, não todo o passado do veículo. Notícias publicadas e retiradas do feed entre duas janelas podem não ser descobertas. O catálogo cobre os 600 veículos fornecidos, não a totalidade da imprensa mundial.

## Fontes oficiais consultadas

- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://developers.cloudflare.com/r2/get-started/s3/
- https://developers.cloudflare.com/r2/examples/aws/boto3/
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://supabase.com/pricing
- https://developers.cloudflare.com/r2/pricing/

## Estado da entrega

Supabase ikoqkeqxqfqkfjmcwwdq: 600 feeds cadastrados; seis tabelas com acesso público bloqueado. Preflight remoto aprovado (banco + R2); 16 testes passaram. Primeira coleta iniciada; otimização em lotes de até250 registros com deduplicação por URL e uploads RSS paralelos. SQL validado remotamente em transação revertida, incluindo atualização sem duplicidade. Última contagem: 985 matérias e28 feeds tentados, ainda sem textos de páginas confirmados; é um retrato parcial, não o fechamento do ciclo. Rotina habilitada para00h/06h/12h/18h Brasília, com recuperação +1h. Acompanhar https://github.com/zehlima/blog-criia-rss/actions/runs/34827810364 .
