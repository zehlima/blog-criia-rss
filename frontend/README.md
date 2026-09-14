# Painel Tabler — BLOG CRIIA

Publicação autorizada pelo usuário. Integração por snapshot do Supabase, renovado após coleta e tendências e a cada hora. O navegador atualiza a leitura a cada minuto. A data exibida é a data da fonte; não implica coleta em tempo real.

## Entrega
- Matérias: até 2.000 títulos mais recentes, busca por título e país, acesso ao veículo original.
- Tendências: país, continente e globo, última análise pronta, janela de 24h, revisão editorial pendente.
- Coleta: métricas, erros RSS e falhas de extração separados.
- Textos privados do R2 e credenciais não são exportados.

O workflow Painel Tabler gera o site com dados reais e guarda o artefato painel-tabler antes da publicação. Não declara deploy concluído se faltarem credenciais.

## Cloudflare Pages
Projeto: blog-criia-painel (produção main).
Secrets GitHub necessários para publicar: CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN (Account / Cloudflare Pages / Edit). DATABASE_PASSWORD já é reutilizado no runner. Não copiar senhas para frontend.

Executar manualmente Painel Tabler após configurar os secrets. O projeto Pages deve existir. A atualização não escreve no banco nem altera os motores.

## Limites desta versão
Acompanhamento de leitura; orientações compartilhadas e leitura privada integral ainda não implementadas. Discrepância, redação e SEO ainda não integrados. Snapshot atrasado continua mostrando a data original, sem aparentar atualização nova.
