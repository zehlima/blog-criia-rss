# BLOG CRIIA — Bóris

Coleta de RSS e textos, armazenamento em Supabase/R2 e frequência de pautas por país, continente e globo.

- Inventário ativo: `data/feeds.json`, atualmente 675 feeds, incluindo 75 da América do Sul. Registros antigos são preservados no banco.
- Coleta: 00h, 06h, 12h e 18h de Brasília; recuperação nas demais horas. `ENABLE_COLLECTION=false` pausa somente os disparos agendados.
- Extração: 16 trabalhadores, fila contínua, gravação em lotes, retentativas com backoff. Conteúdo de página e conteúdo publicado no RSS têm estados separados; resumo não é promovido a texto completo.
- Tendências: representações multilíngues dos títulos, agrupamento de diâmetro limitado e deduplicação estimada de republicações. Relatórios vinculados ao encerramento da coleta, com alvos de +15/+20/+25 minutos. Atrasos e cobertura ficam explícitos.
- Relatórios: artefatos do Actions e cópias no R2 a cada encerramento. Erros de feeds separados dos erros de extração.
- Painel: estrutura preparada, ainda sem publicação.

Leia `CONFIGURAR.md` para configuração operacional e `VALIDACAO.json` para o último checkpoint documentado. O resultado verde de um workflow confirma execução técnica; não significa cobertura integral nem revisão editorial.

## Verificação local

```bash
pip install -r requirements.txt
python -m pytest -q
```

O fluxo de tendências instala também `trends/requirements.txt`. Para verificar os provedores, com os secrets já configurados:

```bash
python -m collector.main preflight
python -m collector.smoke
```
