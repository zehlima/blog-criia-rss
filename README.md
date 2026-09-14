# BLOG CRIIA — Bóris Python v2

Comece por **CONFIGURAR.md**. Migração da arquitetura Worker/D1 para Python + GitHub Actions + Supabase/PostgreSQL + R2.

## Arquivos

- `collector/`: HTTP, parser, extração, persistência e orquestração.
- `sql/001_schema.sql`: schema PostgreSQL idempotente.
- `.github/workflows/collect.yml`: quatro janelas Brasília e retomada uma hora depois.
- `data/feeds.json`: os 600 registros originais, sem exclusão dos pendentes.
- `requirements.txt`: versões instaladas fixadas.
- `tests/`: testes locais, sem credenciais.
- `VALIDACAO.json`: o que foi e não foi testado.

## Local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Os comandos abaixo requerem os cinco secrets descritos no guia, definidos como variáveis de ambiente:

```bash
python -m collector.main setup
python -m collector.main preflight
python -m collector.main run
```

Nada é publicado automaticamente ao descompactar. O agendamento só roda com `ENABLE_COLLECTION=true`. O teste completo dos provedores fica pendente dos acessos.
