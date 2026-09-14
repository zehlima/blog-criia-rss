"""Editorial regression cases: observed false groups and explicit translated headline pairs."""
import json,os
from pathlib import Path
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from huggingface_hub import model_info

PAIRS=[
(False,'iOS 27 corrigiu um dos botões mais irritantes do iPhone!','Cuidado com WhatsApp no iPhone! Ataque rouba a conta sem ter de tocar no ecrã'),
(False,'Hackear um Boeing 737 em 60 segundos? Dispositivo minúsculo mostra que é possível','Microsoft alerta para nova onda de ataques contra contas Microsoft 365'),
(False,'LG nega que as suas Smart TVs estejam a espiar','Cuidado com WhatsApp no iPhone! Ataque rouba a conta sem ter de tocar no ecrã'),
(False,'ConnectWise修補ScreenConnect重大漏洞','GitLab修補CVSS滿分重大漏洞，公開隔天即出現漏洞探測'),
(False,'Google發布9月份Android例行更新，修補200個資安漏洞','Palo Alto Networks修補防火牆作業系統XML功能漏洞'),
(False,'美光、闪迪赴韩争抢半导体核心人才，三星加码薪酬与股权激励应对挖角','全球首次：杭州镓仁半导体实现 12 英寸氧化镓晶体等径生长'),
(False,'Apple is reportedly working on iPhone game controllers','Apple reports record quarterly revenue from iPhone sales'),
(False,'Anthropic CEO calls for slowing AI development','Apple is reportedly working on iPhone game controllers'),
(True,'Apple is reportedly working on iPhone game controllers','Apple is designing its own game controllers for iPhone, could be Beats branded'),
(True,'Apple is reportedly working on iPhone game controllers','Apple разрабатывает игровые контроллеры для iPhone — они выйдут под брендом Beats'),
(True,'Apple is reportedly working on iPhone game controllers','Apple’ın Yeni Oyun Kontrolcüleri Beats Markasıyla Gelebilir'),
(True,'Apple is reportedly working on iPhone game controllers','Apple estaria desenvolvendo controles de jogos para iPhone'),
(True,'Anthropic CEO Amodei calls for slowing AI development','Anthropic CEO’su Dario Amodei’den yapay zeka şirketlerine “yavaşlayın” çağrısı'),
(True,'Anthropic CEO Amodei calls for slowing AI development','CEO da Anthropic pede desaceleração do desenvolvimento de inteligência artificial'),
(True,'ConnectWise修補ScreenConnect重大漏洞','ConnectWise公布的ScreenConnect重大漏洞，傳出已於8月下旬被用於攻擊活動'),
(True,'Link4 marks 10 years as digital trade services grow','Link4 marks 10 years as digital trade services grow'),
]

def main():
 torch.set_num_threads(min(4,os.cpu_count() or 2))
 name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
 revision=model_info(name).sha
 model=SentenceTransformer(name,revision=revision,device='cpu',trust_remote_code=False)
 text=list(dict.fromkeys(t for _,a,b in PAIRS for t in (a,b)))
 vectors=model.encode(text,normalize_embeddings=True,batch_size=32)
 by=dict(zip(text,vectors));rows=[]
 for expected,a,b in PAIRS:
  rows.append({'same_event':expected,'a':a,'b':b,'similarity':float(by[a]@by[b])})
 report={'model':name,'revision':revision,'cases':rows,'note':'Small editorial regression sample, includes explicit translated variants; not a general accuracy benchmark.'}
 Path('reports').mkdir(exist_ok=True)
 Path('reports/headline-calibration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
