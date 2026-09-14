# BLOG CRIIA — revisão dos 121 erros de RSS

Data: 14/09/2026 (UTC).

**121 registros revisados: 27 URLs corrigidas, 77 veículos substituídos e 17 feeds mantidos após revalidação.** Todos os 121 endereços selecionados retornaram XML RSS/Atom analisável e itens com links em pelo menos um teste. O reteste final confirmou 121/121; falhas no último reteste: nenhuma. Isso não equivale a 121 sucessos no coletor de produção.

Fonte do problema: [relatório de 06h BRT](https://drive.google.com/file/d/163UN96TeCQ8qw47dhOFm07sMptkNhVxR/view), com 479 sucessos e 121 falhas entre 600 feeds.

## O que foi preservado

Os 479 registros fora do relatório de falhas foram preservados integralmente. A base revisada mantém 600 registros, 75 por região. A consolidação com América do Sul mantém 675 registros. Nenhuma repetição nova de nome ou URL RSS normalizada foi encontrada. Reposições foram confrontadas com os sites dos 675 registros anteriores. Marcas editoriais diferentes do mesmo grupo empresarial não foram tratadas automaticamente como duplicatas; isso inclui ITWeb Africa e ITWeb, publicações distintas. Connect.cz foi descartado por entregar o feed de Živě.cz, já cadastrado.

## Limites editoriais

A disponibilidade técnica foi testada diretamente. Não foi feita auditoria de SimilarWeb nem comparação numérica de audiência. **Não é possível afirmar que todas as 77 reposições sejam equivalentes estritas em audiência, país, especialidade ou frequência diária.** Foram priorizados veículos da mesma região com notícias recentes. Algumas reposições ampliam ou mudam o foco (por exemplo, EE Times em lugar de Digital Trends, Q Costa Rica em lugar de TechNewsTT e ScienceAlert em lugar de Information Age Austrália). Os jornais generalistas exigem filtro de tecnologia e negócios digitais. As diferenças estão na tabela e nas justificativas.

A janela de atualização usada para admitir novas fontes foi de até 14 dias, com exclusão de datas muito futuras. Essa janela identifica atividade recente, não comprova cadência diária. iAfrikan, por exemplo, tem uma notícia recente, mas cadência esparsa no XML. FinTech Futures contém também item com data futura; o feed foi admitido pelos demais itens atuais, não pelo máximo de datas.

We Are Tech, Ecofin Agency e Fintech News Middle East são edições voltadas às respectivas regiões, com editoras na Suíça. Connecting Africa tem redação na África do Sul e pertence à Informa britânica. País editorial/edição e propriedade são explicitados nos registros.

## Ações necessárias no coletor

- **TechNode (ID 358):** o RSS respondeu com cerca de 11,6 MB e 2.000 itens. O erro original `body_too_large` depende do coletor. Usar parsing incremental e um limite controlado por fonte, preservando limites de recursos e validação de destinos. Trocar a URL, por si só, não resolve esse limite.
- **Digital Trends, Eco TV e Telemetro (IDs 27, 93, 146):** o relatório contém `AttributeError`. Revisar traceback e normalização dos tipos usados pelo parser. Digital Trends recebeu reposição após testes de acesso falharem; Eco TV e Telemetro receberam URLs alternativas válidas. Isso não demonstra que o defeito interno do programa foi corrigido.
- **En Segundos Panamá (ID 105):** respondeu com XML válido com `Accept-Encoding: identity`; revisar tratamento de compressão.
- **TechWeb (ID 363):** foi substituído sem desabilitar a proteção de destino não público apontada no coletor.
- HTTP 403/429, timeouts, limites e falhas de servidor podem variar entre ambientes. Não há garantia de estabilidade permanente, nem garantia de extração do texto integral das matérias.

## Aplicação dos dados

1. Use o CSV/JSON de revisão para localizar o registro pelo **ID do relatório + URL anterior**. A posição de um array não deve ser presumida como chave universal do banco.
2. Para correção de URL ou mudança comprovada de marca (Daba → Condia), preserve a identidade e o histórico da fonte.
3. Para substituição de veículo, aposente a fonte antiga e crie a nova identidade conforme o schema do coletor. Não reatribua matérias históricas ao novo veículo.
4. Faça uma coleta de teste no ambiente real, incluindo as quatro pendências de parser/limite citadas acima. Os arquivos foram revisados; nenhuma alteração no banco, agendamento ou coletor em produção foi executada nesta atividade.

## Arquivos

CSV usa ponto e vírgula e UTF-8 com BOM. JSON da base mantém as seis chaves originais. A revisão de 121 linhas e as evidências têm campos adicionais de auditoria. Os 104 registros alterados são 27 correções e 77 reposições; os 17 revalidados aparecem na revisão completa.

## Relação de alterações

| ID | Ação | Veículo anterior | Veículo revisado | RSS revisado | Observação |
|---|---|---|---|---|---|
| 9 | substituir | BigDATAwire | Data Center Knowledge | https://www.datacenterknowledge.com/rss.xml |  |
| 27 | substituir | Digital Trends | EE Times | https://www.eetimes.com/feed/ | Relatório original contém AttributeError do coletor. Revisar traceback e normalização de tipos antes de concluir causa no veículo. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 36 | substituir | HPCwire | Semiconductor Engineering | https://semiengineering.com/feed/ |  |
| 52 | manter_revalidado | RCR Wireless News | RCR Wireless News | https://rcrwireless.com/feed |  |
| 53 | substituir | SC Media | The Cyber Express | https://thecyberexpress.com/feed/ |  |
| 72 | manter_revalidado | VentureBeat | VentureBeat | https://venturebeat.com/feed |  |
| 75 | substituir | ZDNET | Techstrong AI | https://techstrong.ai/feed/ |  |
| 76 | substituir | 100% Noticias | Nicaragua Investiga | https://nicaraguainvestiga.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. Filtragem temática necessária. |
| 77 | substituir | Artículo 66 | El Periódico Costa Rica | https://elperiodicocr.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 84 | substituir | CRHoy | The Costa Rica News | https://thecostaricanews.com/feed/ | Filtragem temática necessária. |
| 87 | substituir | Diario El Mundo | El Salvador Times | https://www.elsalvadortimes.com/rss/ | Filtragem temática necessária. |
| 90 | substituir | Diario Tiempo | Criterio.hn | https://criterio.hn/feed/ | Filtragem temática necessária. |
| 93 | corrigir_url | Eco TV | Eco TV | https://www.ecotvpanama.com/rss/pages/ultimas-noticias.xml | Relatório original contém AttributeError do coletor. Revisar traceback e normalização de tipos antes de concluir causa no veículo. Feed passou a geral: aplicar filtro temático de tecnologia e negócios digitais. Filtragem temática necessária. |
| 94 | substituir | El Caribe | El Nuevo Diario | https://elnuevodiario.com.do/feed/ | Filtragem temática necessária. |
| 95 | corrigir_url | El Diario de Hoy | El Diario de Hoy | https://www.elsalvador.com/sitemap.rss | Filtragem temática necessária. |
| 97 | substituir | El Economista Centroamérica | Diario Libre | https://www.diariolibre.com/rss/portada.xml | Reposição da mesma região; países anterior e novo indicados na tabela. Filtragem temática necessária. |
| 99 | corrigir_url | El Heraldo Honduras | El Heraldo Honduras | https://www.elheraldo.hn/rss/portada.xml | Filtragem temática necessária. |
| 105 | manter_revalidado | En Segundos Panamá | En Segundos Panamá | https://ensegundos.com.pa/feed/ | Filtragem temática necessária. |
| 107 | substituir | Estrategia & Negocios | The Tribune Bahamas | https://www.tribune242.com/rss/headlines/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 116 | substituir | Juventud Técnica | CiberCuba | https://www.cibercuba.com/rss.xml | Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 117 | substituir | La Estrella de Panamá | Dominican Today | https://dominicantoday.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 118 | manter_revalidado | La Gaceta de Panamá | La Gaceta de Panamá | https://www.lagacetadepanama.com/rss/ | Filtragem temática necessária. |
| 120 | substituir | La Prensa Gráfica | Diario Co Latino | https://www.diariocolatino.com/feed/ | Filtragem temática necessária. |
| 122 | substituir | La Prensa Nicaragua | Diario de Cuba | https://diariodecuba.com/rss.xml | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 127 | corrigir_url | Metro Libre | Metro Libre | https://www.metrolibre.com/rss/portada.xml | Filtragem temática necessária. |
| 132 | manter_revalidado | OnCuba News | OnCuba News | https://oncubanews.com/feed/ | Filtragem temática necessária. |
| 138 | corrigir_url | República | República | https://republica.com/feed | Filtragem temática necessária. |
| 142 | substituir | Soy502 | La Hora | https://lahora.gt/feed/ | Filtragem temática necessária. |
| 144 | substituir | TechNewsTT | Q Costa Rica | https://qcostarica.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 145 | substituir | TecnoComo | El Nacional | https://elnacional.com.do/rss/home.xml | Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 146 | corrigir_url | Telemetro | Telemetro | https://www.telemetro.com/rss/pages/ultimas-noticias.xml | Relatório original contém AttributeError do coletor. Revisar traceback e normalização de tipos antes de concluir causa no veículo. Feed passou a geral: aplicar filtro temático de tecnologia e negócios digitais. Filtragem temática necessária. |
| 159 | corrigir_url | CHIP | CHIP | https://www.chip.de/rss |  |
| 161 | corrigir_url | Computer Bild | Computer Bild | https://www.computerbild.de/rss/35011529.xml |  |
| 162 | corrigir_url | Computer Hoy | Computer Hoy | https://computerhoy.20minutos.es/rss/ |  |
| 165 | substituir | Computing | Inside IT | https://www.inside-it.ch/rss.xml | Reposição da mesma região; países anterior e novo indicados na tabela. |
| 180 | corrigir_url | Hardware Upgrade | Hardware Upgrade | https://feeds.hwupgrade.it/rss_hwup.xml |  |
| 184 | substituir | Information Age — Reino Unido | FinTech Futures | https://www.fintechfutures.com/rss.xml |  |
| 195 | substituir | Maddyness | Silicon Canals | https://siliconcanals.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. |
| 207 | manter_revalidado | Silicon Republic | Silicon Republic | https://www.siliconrepublic.com/feed/ |  |
| 227 | manter_revalidado | AIN | AIN | https://ain.ua/feed/ |  |
| 234 | substituir | BOOT.lv | MobilMania.cz | https://mobilmania.zive.cz/rss/sc-47/default.aspx | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 240 | substituir | Computerworld Magyarország | Mínuszos | https://www.minuszos.hu/feed/ |  |
| 243 | substituir | DEV Styler | ITReseller | https://itreseller.pl/feed/atom/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 262 | manter_revalidado | Keddr | Keddr | https://keddr.com/feed/ |  |
| 264 | manter_revalidado | Kursors.lv | Kursors.lv | https://kursors.lv/feed/ |  |
| 268 | substituir | Mezha.Media | Digitrendi | https://digitrendi.hu/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 271 | substituir | Mobilissimo | nwradu blog | https://www.nwradu.ro/feed/ |  |
| 274 | corrigir_url | Nextech | Nextech | https://www.nextech.sk/site/rssfeed/type/Produkty/page/1 | Feed escolhido é a seção de produtos, não todo o portal. |
| 277 | corrigir_url | Overclockers.ru | Overclockers.ru | https://overclockers.ru/rss/all.rss |  |
| 281 | corrigir_url | Prohardver | Prohardver | https://prohardver.hu/hirfolyam/anyagok/rss.xml |  |
| 292 | substituir | Svět hardware | SmartLife | https://smartlife.mondo.rs/rss/1/Naslovna | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 301 | substituir | 36Kr | KoreaTechDesk | https://koreatechdesk.com/sitemap.rss | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 306 | corrigir_url | beSUCCESS | beSUCCESS | https://besuccess.com/feed/atom/ |  |
| 308 | substituir | BRIDGE | RobotStart | https://robotstart.info/rss20/index.rdf | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 309 | substituir | cnBeta | Techbang | https://feeds.feedburner.com/techbang/daily | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 313 | substituir | DealStreetAsia | Tech Edition (antigo TechEDT) | https://www.techedt.com/feed | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 316 | substituir | DoNews | Digital Daily | https://www.ddaily.co.kr/rss.xml | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 318 | substituir | Droidsans | Wiser.my | https://wiser.my/feed | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 322 | substituir | Gadgetren | Gadget Pilipinas | https://www.gadgetpilipinas.net/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 329 | substituir | Huxiu | Bloter | https://cdn.bloter.net/rss/gns_allArticle.xml | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 347 | substituir | PingWest | Mogura VR | https://www.moguravr.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 348 | corrigir_url | Pokde.Net | Pokde.Net | https://pokde.net/feed/atom |  |
| 354 | substituir | Tech in Asia | The Tech Revolutionist | https://thetechrevolutionist.com/feed.xml | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 355 | substituir | Tech Jio | Gizguide | https://www.gizguide.com/feeds/posts/default?alt=rss | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 356 | corrigir_url | TechNave | TechNave | https://technave.com/feed/ |  |
| 358 | manter_revalidado | TechNode | TechNode | https://technode.com/feed/ | Feed de cerca de 11,6 MB e 2.000 itens. Ajustar leitura incremental e limite por fonte; manter limite global e proteções de rede. |
| 363 | substituir | TechWeb | Pinoy Techno Guide | https://www.pinoytechnoguide.com/feed | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 377 | corrigir_url | Arab News — Science & Technology | Arab News — feed geral | https://www.arabnews.com/rss.xml | Feed passou a geral: aplicar filtro temático de tecnologia e negócios digitais. Filtragem temática necessária. |
| 378 | substituir | Arabian Business | Economy Middle East | https://economymiddleeast.com/feed/atom/ |  |
| 379 | substituir | Arabian ICT | Mena Tech | https://menatech.net/feed/ |  |
| 385 | corrigir_url | Click | Click | https://www.click.ir/feeds |  |
| 386 | substituir | CTech | Entrepreneur Middle East | https://mena.entrepreneur.com/feed | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 394 | substituir | Enterprise Channels MEA | Intelligent CIO Middle East | https://www.intelligentcio.com/me/feed/ |  |
| 400 | substituir | Gulf Business | Fintech News Middle East | https://fintechnews.ae/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 404 | substituir | Israel21c | TechInside | https://www.techinside.com/feed/atom/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 407 | substituir | ITP.net | Telecom Review | https://www.telecomreview.com/feed/ |  |
| 409 | substituir | Jordan News — Technology | Doha News | https://dohanews.co/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 413 | corrigir_url | MediaCat | MediaCat | https://mediacat.com/feed/ |  |
| 419 | substituir | Pazarlamasyon | Turk Internet | https://turk-internet.com/feed/ |  |
| 423 | substituir | Saudi Android | Tamindir | https://feeds.feedburner.com/tamindir/stream | Reposição da mesma região; países anterior e novo indicados na tabela. |
| 432 | corrigir_url | Technopat | Technopat | https://feedpress.me/technopat |  |
| 436 | substituir | Teknoloji Günlüğü | Technotoday | https://technotoday.com.tr/feed/atom/ |  |
| 437 | substituir | Teknolojioku | Donanım Arşivi | https://www.donanimarsivi.com/feed/ |  |
| 440 | corrigir_url | Times of Israel — Tech Israel | Times of Israel — feed geral | https://www.timesofisrael.com/feed/ | Feed passou a geral: aplicar filtro temático de tecnologia e negócios digitais. Filtragem temática necessária. |
| 447 | corrigir_url | WIRED Middle East | WIRED Middle East | https://www.wired.me/feed/rss |  |
| 453 | substituir | BiztechAfrica | ITWeb Africa | https://itweb.africa/rss |  |
| 456 | corrigir_url | Daba | Condia (antigo Daba) | https://thecondia.com/feed/atom/ |  |
| 459 | substituir | Dignited | iAfrikan | https://iafrikan.com/rss/ | Reposição da mesma região; países anterior e novo indicados na tabela. Cadência baixa: o XML recente não comprova publicação diária. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 463 | substituir | Gadgets Africa | TechnoMag | https://technomag.co.zw/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 466 | substituir | Innovation Village | Tech In Africa | https://www.techinafrica.com/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. |
| 467 | substituir | IT Edge News | TechDigest Nigeria | https://techdigest.ng/feed/ |  |
| 473 | substituir | Maroc Numeric | Punch — feed geral | https://rss.punchng.com/v1/category/latest_news | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 478 | substituir | MyBroadband | Connecting Africa | https://www.connectingafrica.com/rss.xml | Reposição da mesma região; países anterior e novo indicados na tabela. |
| 479 | substituir | N'TIC Magazine | Algerie360 — High Tech | https://www.algerie360.com/category/high-tech/feed/ |  |
| 483 | substituir | Nigeria CommunicationsWeek | BusinessDay Nigeria — Technology | https://businessday.ng/category/technology/feed/ |  |
| 484 | manter_revalidado | PC Tech Magazine | PC Tech Magazine | https://pctechmag.com/feed/ |  |
| 485 | corrigir_url | Shega | Shega | https://shega.co/rss |  |
| 494 | manter_revalidado | Techawk | Techawk | https://www.techawkng.com/feed/ |  |
| 497 | manter_revalidado | TechCabal | TechCabal | https://techcabal.com/feed/ |  |
| 500 | corrigir_url | TechEconomy | TechEconomy | https://techeconomy.ng/feed.xml |  |
| 502 | substituir | Techgh24 | MyJoyOnline — feed geral | https://www.myjoyonline.com/feed/ | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 509 | substituir | TechSmart | Nigerian Tribune — Technology | https://tribuneonlineng.com/category/technology/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 513 | substituir | TechWeez | Ecofin Agency — feed geral | https://www.ecofinagency.com/component/obrss/agency-rss | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 519 | corrigir_url | TSA — Tecnologia | TSA — feed geral | https://www.tsa-algerie.com/feed/ | Feed passou a geral: aplicar filtro temático de tecnologia e negócios digitais. Filtragem temática necessária. |
| 520 | substituir | Tunisie Numérique — Technologie | Managers.tn | https://managers.tn/feed/ |  |
| 524 | substituir | Webmanagercenter — Technologie | Entreprises Magazine | https://www.entreprises-magazine.com/feed/ |  |
| 525 | substituir | WeeTracker | We Are Tech | https://www.wearetech.africa/en/fils-uk/news?format=feed&type=rss | Reposição da mesma região; países anterior e novo indicados na tabela. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 526 | corrigir_url | ABC Australia — Technology | ABC Australia — feed geral | https://www.abc.net.au/news/feed/46182/rss.xml | Filtragem temática necessária. |
| 527 | manter_revalidado | APDR | APDR | https://asiapacificdefencereporter.com/feed/ | Filtragem temática necessária. |
| 528 | substituir | Ausdroid | New Atlas | https://newatlas.com/index.rss | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 539 | manter_revalidado | Cook Islands News | Cook Islands News | https://www.cookislandsnews.com/feed/ | Filtragem temática necessária. |
| 541 | substituir | Cyber Daily | Risky Business Media | https://news.risky.biz/rss/ |  |
| 546 | manter_revalidado | EFTM | EFTM | https://eftm.com/feed |  |
| 549 | substituir | FinTech Business | Mediaweek | https://www.mediaweek.com.au/rss.xml | Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 556 | substituir | Information Age — Austrália | ScienceAlert | https://www.sciencealert.com/feed | Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |
| 557 | substituir | InnovationAus | Small Business Connections | https://smallbusinessconnections.com.au/feed/ | Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 566 | substituir | Manufacturers' Monthly | Process Online | https://www.processonline.com.au/feed.rss |  |
| 571 | substituir | PACE Today | Electrical Comms Data | https://www.ecdonline.com.au/feed.rss |  |
| 573 | manter_revalidado | PowerUp! | PowerUp! | https://powerup-gaming.com/feed/ |  |
| 597 | substituir | The National PNG | Autotalk New Zealand | https://autotalk.co.nz/feed/ | Reposição da mesma região; países anterior e novo indicados na tabela. Mudança de foco: substituto tem cobertura mais ampla ou diferente; equivalência editorial estrita não comprovada. País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. Filtragem temática necessária. |
| 599 | substituir | Utility Magazine | Sustainability Matters | https://www.sustainabilitymatters.net.au/feed.rss | País ou foco editorial alterado; não é equivalência auditada de audiência ou cobertura. |

