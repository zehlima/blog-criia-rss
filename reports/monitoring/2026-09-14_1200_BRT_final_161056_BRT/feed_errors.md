# Coleta RSS — complete_with_gaps

```json
{
  "slot": "2026-09-14T15:00:00+00:00",
  "expected_feeds": 675,
  "feeds_ok": 649,
  "feeds_errors": 26,
  "feeds_not_attempted": 0,
  "articles": {
    "total": 24419,
    "content_key_total": 23181,
    "valid_text_bodies": 23176,
    "without_text": 1243,
    "pending": 0,
    "unavailable": 1236,
    "invalid_references": 7,
    "page_texts": 22305,
    "publisher_rss_texts": 871,
    "title_summary_only": 0,
    "extracted": 23181,
    "content_key_does_not_prove_integrality": true
  },
  "due_articles": 0,
  "compressed_bytes_written": 2762,
  "status": "complete_with_gaps",
  "finished_at": "2026-09-14T19:10:56.720616+00:00"
}
```

| Veiculo | Pais | Erro | Acao |
|---|---|---|---|
| RCR Wireless News | Estados Unidos | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| VentureBeat | Estados Unidos | http_429 | Repetir com backoff e verificar causa; nao repor automaticamente. |
| La Gaceta de Panamá | Panamá | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Soy502 | Guatemala | invalid_or_malformed_feed | Inspecionar XML e endpoint oficial; retestar. |
| Silicon Republic | Irlanda | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| AIN | Ucrânia | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Keddr | Ucrânia | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Kursors.lv | Letônia | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| 36Kr | China | invalid_or_malformed_feed | Inspecionar XML e endpoint oficial; retestar. |
| TechWeb | China | non_public_destination | Verificar acesso permitido; nao contornar restricoes. |
| Arab News — Science & Technology | Arábia Saudita | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Enterprise Channels MEA | Emirados Árabes Unidos | SSLError | Verificar certificado e URL oficial; manter validacao TLS. |
| The National — Technology | Emirados Árabes Unidos | invalid_empty_feed_or_entries | Conferir categoria e endpoint oficial; vazio nao prova indisponibilidade do veiculo. |
| Times of Israel — Tech Israel | Israel | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| PC Tech Magazine | Uganda | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Techawk | Nigéria | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| TechCabal | Nigéria | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| TechWeez | Quênia | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| APDR | Austrália | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Cook Islands News | Ilhas Cook | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| PowerUp! | Austrália | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| The National PNG | Papua-Nova Guiné | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| Click | Irã | http_404 | Validar URL oficial antes de corrigir ou repor. |
| Adrenaline | Brasil | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| IT Forum | Brasil | http_403 | Verificar acesso permitido; nao contornar restricoes. |
| TI Inside | Brasil | http_403 | Verificar acesso permitido; nao contornar restricoes. |
