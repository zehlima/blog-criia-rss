"""Persistent feed error handoff for every completed collector invocation."""
import csv
import io
import json
import os
from pathlib import Path
from .inventory import urls as active_urls


def classify(error):
    if error in ('AttributeError','TypeError','KeyError'):
        return 'coletor', 'Corrigir coletor e retestar; nao substituir fonte.'
    if error in ('http_404','http_410'):
        return 'endpoint', 'Validar URL oficial antes de corrigir ou repor.'
    if error in ('http_403','http_401','robots_disallowed','non_public_destination'):
        return 'acesso', 'Verificar acesso permitido; nao contornar restricoes.'
    if error in ('invalid_or_malformed_feed','entry_without_title_or_link'):
        return 'formato', 'Inspecionar XML e endpoint oficial; retestar.'
    return 'temporario_ou_investigar', 'Repetir com backoff e verificar causa; nao repor automaticamente.'


def write_feed_report(db,s3,slot,report):
    rows=db.execute('''SELECT f.id,f.name,f.country,f.region,f.rss_url,
      coalesce(r.status,'not_attempted') status,r.error,r.checked_at
      FROM news_feeds f LEFT JOIN news_feed_runs r ON r.feed_id=f.id AND r.slot=%s
      WHERE f.rss_url=ANY(%s) AND r.status IS DISTINCT FROM 'ok' ORDER BY f.id''',(slot,active_urls())).fetchall()
    fields=['id','name','country','region','rss_url','status','error','checked_at','classification','action']
    buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
    for r in rows:
        r['classification'],r['action']=classify(r['error']) if r['status']!='not_attempted' else ('pendente','Executar feed; sem evidencia de falha.')
        writer.writerow(r)
    # Separate article-level extraction failures from RSS endpoint failures.
    extraction=db.execute('''SELECT id,url,title,content_status,last_error,attempts,next_attempt_at
      FROM news_articles WHERE content_key IS NULL AND content_status='unavailable' ORDER BY id''').fetchall()
    exbuf=io.StringIO();exwriter=csv.DictWriter(exbuf,fieldnames=['id','url','title','content_status','last_error','attempts','next_attempt_at']);exwriter.writeheader();exwriter.writerows(extraction)
    stamp=report['finished_at'].replace(':','-')
    prefix=f'reports/collection/{slot.strftime("%Y-%m-%d_%H%MUTC")}/{stamp}'
    md='# Coleta RSS — '+report['status']+'\n\n```json\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n```\n\n'
    md+='| Veiculo | Pais | Erro | Acao |\n|---|---|---|---|\n'
    for r in rows:
        md+='| '+' | '.join(str(r[k] or '').replace('|','/').replace('\n',' ') for k in ('name','country','error','action'))+' |\n'
    for name,value in [('extraction_errors.csv',exbuf.getvalue()),('feed_errors.csv',buf.getvalue()),('feed_errors.md',md),('summary.json',json.dumps(report))]:
        Path('reports',name).write_text(value,encoding='utf-8')
        s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=prefix+'/'+name,Body=value.encode(),ContentType='text/plain; charset=utf-8')
