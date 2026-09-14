# BLOG CRIIA — análise v19 concluída tecnicamente

Execução: [34905786511](https://github.com/zehlima/blog-criia-rss/actions/runs/34905786511). Correção: [a247d0a](https://github.com/zehlima/blog-criia-rss/commit/a247d0a5ea728e6a5dd5f99e12da9c9445fccd54).

Snapshot ready, 113 recortes persistidos (105 country, 7 continent, 1 globe). Modelo paraphrase-multilingual-MiniLM-L12-v2 e revisão e8f8c211226b894fcb81acc59f3b34ba3efd5f42 preservados. Limiar 0,72; calibração em amostra pequena.

Corte: 14/09/2026 19h44m56s BRT. Janela de 24 horas. 8.696 matérias únicas, 568 veículos por domínio; 610 grupos e 7.238 matérias mantidas sem agrupamento. Leitura de 7.875 textos extraídos de páginas na janela. Corpus total processado: 26.889 matérias elegíveis, 24.501 textos extraídos de páginas e 914 conteúdos fornecidos em RSS. Não equiparar conteúdo RSS a artigo integral, nem título/resumo a texto completo.

Brasil: 378 matérias em 32 veículos. Persistem 97 rótulos editoriais com matérias entre 105 rótulos cadastrados, com variantes como Nicaragua/Nicarágua e qualificadores de Suíça/África do Sul. Portanto, esses números não devem ser anunciados como países distintos. Rótulos originais preservados para auditoria. País significa origem editorial da fonte; 7 recortes continentais incluem o recorte transcontinental Europa/Ásia.

## Correção validada e limites

A v18 misturava uma lista de melhores filmes Paramount+ com uma comparação de bitrate de streaming (IDs 4659 e 56667). A v19 exclui listas numeradas diferentes do agrupamento, mantendo títulos exatamente iguais elegíveis à sindicação. 113 testes locais e 113 no GitHub aprovados. O cluster-audit da execução real contém 610 grupos; ambos os IDs não aparecem em nenhum grupo, confirmando separação efetiva. Não foram forçados a outros temas.

**Estado editorial geral: automatic_groups_require_editorial_review.** A correção desse par não valida todo o agrupamento nem toda a cobertura. A v18 permanece registrada como issues_found_requires_review. Evidência nominal preservada em editorial_validation.json. Títulos representativos não foram verificados como afirmações factuais sobre o mundo. O ranking mede frequência observada, não previsão nem independência editorial.

A execução 34905632800 foi cancelada para a nova versão e corretamente marcada failed com github_prepare_cancelled, sem snapshot entregue. A análise reprovada v2 não foi promovida nem reutilizada como validação.

## Horários encadeados

| Escopo | Recortes | Alvo UTC | Início UTC | Atraso (s) |
|---|---:|---|---|---:|
| continent | 7 | 2026-09-14 23:04:56.665893+00 | 2026-09-14 23:04:56.666043+00 | 0.0002 |
| country | 105 | 2026-09-14 22:59:56.665893+00 | 2026-09-14 22:59:56.66604+00 | 0.0001 |
| globe | 1 | 2026-09-14 23:09:56.665893+00 | 2026-09-14 23:09:56.666034+00 | 0.0001 |

Alvos +15/+20/+25 preservados. Atraso inferior a 0,001 s nos registros. Na v18 anterior os atrasos foram 677,04 s (país), 376,72 s (continente) e 89,26 s (globo), preservados no relatório anterior.

## Cobertura e tema líder

| Escopo | Local | Matérias | Veículos | Sem grupo | Tema líder | Matérias no tema | Veículos no tema |
|---|---|---:|---:|---:|---|---:|---:|
| continent | África | 486 | 50 | 427 | SA Investment Firm DNI Invests R2 Billion In Digital Economy | 2 | 3 |
| continent | América do Norte | 2217 | 130 | 1839 | Trump dice que la IA no necesita más control que tenerlo a él como presidente de Estados Unidos | 4 | 4 |
| continent | América do Sul | 596 | 63 | 487 | Samsung amplia portfólio premium de TVs no Brasil com novas Micro RGB, OLED, Neo QLED e The Frame Pro | 3 | 3 |
| continent | Ásia | 1815 | 107 | 1643 | Xiaomi представила Pad 9 и Pad 9 Pro — относительно доступные планшеты на Snapdragon | 3 | 3 |
| continent | Europa | 2450 | 128 | 2042 | NVIDIA RTX PRO 5500 Blackwell oficjalnie. Na pokładzie 84 GB pamięci | 4 | 4 |
| continent | Europa/Ásia (transcontinental) | 634 | 30 | 496 | WhatsApp'ta Durum Videolarını 2x Hızda İzleyebileceksiniz | 3 | 3 |
| continent | Oceania | 498 | 60 | 304 | Airrived launches observability for enterprise AI agents | 6 | 6 |
| country | África do Sul | 108 | 13 | 93 | SA Investment Firm DNI Invests R2 Billion In Digital Economy | 2 | 3 |
| country | África do Sul (redação; grupo Informa britânico) | 1 | 1 | 1 | Sem grupo | 0 | 0 |
| country | Albânia | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Alemanha | 566 | 12 | 463 | BYD legt vor: Erste E-Autos mit Feststoffbatterie schon nächstes Jahr | 2 | 2 |
| country | Angola | 2 | 1 | 1 | IA está cada vez mais difícil de controlar? Agentes levantam preocupação no sector | 1 | 1 |
| country | Arábia Saudita | 24 | 2 | 18 | سامسونج تستعد لإطلاق Galaxy Tab S12+ وTab S12 Ultra في 7 أكتوبر | 1 | 1 |
| country | Argélia | 11 | 1 | 11 | Sem grupo | 0 | 0 |
| country | Argentina | 87 | 11 | 73 | "Estamos al borde de un cambio irreversible": la ONU reclamó acciones urgentes de los gobiernos para regular la Inteligencia Artificial | 2 | 2 |
| country | Austrália | 235 | 41 | 147 | University of Sydney gives campus-wide ChatGPT Edu access | 4 | 4 |
| country | Áustria | 33 | 3 | 16 | fiskaly ernennt David Feichter zum neuen Co-CEO | 2 | 2 |
| country | Bahamas | 12 | 2 | 12 | Sem grupo | 0 | 0 |
| country | Barbados | 7 | 1 | 7 | Sem grupo | 0 | 0 |
| country | Belarus | 27 | 2 | 23 | Honor تكشف تصميم وألوان سلسلة Magic9.. وإصدار Super Edition ببطارية ضخمة 11,000 مللي أمبير | 1 | 1 |
| country | Bélgica | 10 | 1 | 8 | Brussels-based Chift raises €10.5 million Series A to become Europe’s financial connectivity layer | 1 | 1 |
| country | Belize | 20 | 1 | 20 | Sem grupo | 0 | 0 |
| country | Bolívia | 1 | 1 | 0 | Microsoft elabora código de conduta para manter sua IA sob controle humano | 1 | 1 |
| country | Brasil | 378 | 32 | 304 | Samsung amplia portfólio premium de TVs no Brasil com novas Micro RGB, OLED, Neo QLED e The Frame Pro | 3 | 3 |
| country | Bulgária | 90 | 4 | 66 | HUAWEI WATCH GT 7 Series пристигна в България и разширява възможностите за спорт на открито с карти на над 3000 ски курорта | 2 | 2 |
| country | Camarões | 3 | 1 | 3 | Sem grupo | 0 | 0 |
| country | Canadá | 27 | 3 | 21 | Apple working on game controller under Beats brand: report | 1 | 1 |
| country | Catar | 3 | 1 | 3 | Sem grupo | 0 | 0 |
| country | Chéquia | 102 | 11 | 86 | Tim Cook odešel na důchod k Samsungu. Nějak se mu ale změnil přízvuk | 2 | 3 |
| country | Chile | 27 | 5 | 23 | Zelda: Ocarina of Time no Switch 2 traz 1080P e 60 FPS, mas com ausência importante | 1 | 1 |
| country | China | 322 | 8 | 297 | 荣耀Magic9超能版首发11000mAh电池：史上电量最大的Magic旗舰 | 3 | 2 |
| country | Colômbia | 72 | 6 | 67 | Sam Altman (OpenAI) advierte de que se puede perder el «control del futuro» ante la IA | 1 | 1 |
| country | Coreia do Sul | 270 | 6 | 256 | 삼성디스플레이, '2K·165Hz' 스마트폰 OLED 개발…비보 'iQOO16' 탑재 | 2 | 2 |
| country | Costa Rica | 242 | 12 | 204 | Laura Fernández reduce recorte al Poder Judicial a ¢11 mil millones, pero eleva tono y pone condiciones a magistrados | 3 | 3 |
| country | Croácia | 23 | 2 | 21 | EU KIDS Act: Europska komisija ovog tjedna predstavlja dobno stupnjevani pristup mrežama | 1 | 1 |
| country | Cuba | 51 | 4 | 46 | Rusia apoya las aspiraciones de Cuba de ingresar como miembro pleno en los BRICS, dice Moscú | 2 | 2 |
| country | Dominica | 13 | 1 | 13 | Sem grupo | 0 | 0 |
| country | Egito | 11 | 2 | 9 | Yemen's Houthi rebels seize more key islands in southern Red Sea, tighten grip on shipping routes | 1 | 1 |
| country | El Salvador | 108 | 6 | 91 | Iberojet inicia operaciones con vuelos directos entre El Salvador y España | 5 | 3 |
| country | Emirados Árabes Unidos | 68 | 13 | 56 | Mannai Information Technology and Oracle expand collaboration in Saudi Arabia | 3 | 3 |
| country | Equador | 5 | 2 | 3 | La ONU advierte que todos los derechos humanos “están en riesgo” ante el avance de la IA | 1 | 1 |
| country | Eslováquia | 29 | 3 | 27 | This one feature convinced me to use the Pixel 11 | 1 | 1 |
| country | Eslovênia | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Espanha | 131 | 8 | 117 | Así puedes saber, en un solo vistazo, si un televisor es compatible con la nueva TDT en DVB-T2 y sirve para ver los nuevos canales en UHD 4K | 2 | 1 |
| country | Estados Unidos | 788 | 57 | 656 | Apple releases iOS 27 with Siri AI and these new iPhone features | 3 | 3 |
| country | Etiópia | 1 | 1 | 1 | Sem grupo | 0 | 0 |
| country | Fiji | 28 | 2 | 28 | Sem grupo | 0 | 0 |
| country | Filipinas | 37 | 7 | 30 | Xiaomi TV S Mini LED 2026 Series and New Mijia Washers Now Available in the Philippines | 2 | 2 |
| country | Finlândia | 8 | 3 | 8 | Sem grupo | 0 | 0 |
| country | França | 254 | 10 | 211 | Interdiction des réseaux sociaux aux moins de 15 ans : la France soumet une nouvelle version de son projet à Bruxelles | 3 | 3 |
| country | Gana | 113 | 1 | 108 | Africa must remove visa restrictions to unlock jobs, opportunities – Gabby Otchere-Darko | 2 | 1 |
| country | Granada | 1 | 1 | 1 | Sem grupo | 0 | 0 |
| country | Grécia | 24 | 2 | 18 | NVIDIA RTX PRO 5500 Blackwell oficjalnie. Na pokładzie 84 GB pamięci | 1 | 1 |
| country | Guatemala | 118 | 5 | 96 | Así estará el clima en Guatemala el 15 de septiembre y durante el resto de la semana | 2 | 2 |
| country | Haiti | 7 | 1 | 5 | Haïti - Économie : Cadre comptable des collectivités territoriales | 2 | 1 |
| country | Honduras | 116 | 3 | 93 | Marathón vence por la mínima al Olimpia y es líder del Apertura hondureño | 2 | 2 |
| country | Hong Kong (China) | 30 | 3 | 26 | Honor Magic 9 Super Edition tem especificações vazadas com chip Snapdragon e bateria gigante | 1 | 1 |
| country | Hungria | 45 | 5 | 42 | A Cyberpunk 2077 a Battle.netre költözik, Geralt pedig a Diablo IV-be | 1 | 1 |
| country | Ilhas Cayman | 9 | 1 | 9 | Sem grupo | 0 | 0 |
| country | Ilhas Cook | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Ilhas Virgens Britânicas | 5 | 1 | 5 | Sem grupo | 0 | 0 |
| country | Indonésia | 48 | 4 | 42 | Zelda-Remake: Offizielle Hyrule-Karte zeigt, was Spieler Neues erwartet | 1 | 1 |
| country | Irã | 281 | 15 | 249 | Xiaomi представила Pad 9 и Pad 9 Pro — относительно доступные планшеты на Snapdragon | 3 | 3 |
| country | Irlanda | 7 | 1 | 7 | Sem grupo | 0 | 0 |
| country | Israel | 55 | 7 | 53 | Nowy iOS 27 już jest. Wielka fala aktualizacji od Apple dostępna | 1 | 1 |
| country | Itália | 215 | 6 | 178 | Ecobonus, novità in arrivo: Governo valuta aumento della detrazione al 65% | 3 | 3 |
| country | Jamaica | 32 | 3 | 26 | Monday, September 14, 2026 | 2 | 1 |
| country | Japão | 249 | 14 | 229 | SBI証券、「こどもNISA」事前受付は10月から | 3 | 2 |
| country | Letônia | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Líbano | 1 | 1 | 1 | Sem grupo | 0 | 0 |
| country | Malásia | 52 | 6 | 43 | Yes AI 30: RM30 postpaid with uncapped 5G, no FUP and free ILMUchat Pro | 3 | 3 |
| country | Marrocos | 1 | 1 | 0 | ChatGPTが本日もリセット。OpenAIがGPT-6 Astraの不具合3件を修正 | 1 | 1 |
| country | México | 55 | 6 | 44 | Las pequeñas empresas mexicanas ya encontraron un aliado para vender más que en sus propias tiendas en línea: Mercado Libre | 2 | 1 |
| country | Nicaragua | 5 | 1 | 4 | ICE detiene en Florida al periodista nicaragüense exiliado Luis Galeano | 1 | 1 |
| country | Nicarágua | 2 | 1 | 1 | ICE detiene en Florida al periodista nicaragüense exiliado Luis Galeano | 1 | 1 |
| country | Nigéria | 154 | 13 | 133 | Dangote Thanks Tinubu for Fuel Subsidy, Forex Reforms as Refinery IPO Opens | 2 | 2 |
| country | Nova Zelândia | 235 | 17 | 129 | Reso launches AI dispute platform for New Zealand HR | 5 | 5 |
| country | Países Baixos | 4 | 1 | 4 | Sem grupo | 0 | 0 |
| country | Panamá | 169 | 7 | 135 | Thomas Christiansen apuesta al relevo generacional de Panamá rumbo al 2030 | 2 | 2 |
| country | Papua-Nova Guiné | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Paraguai | 2 | 1 | 1 | Trump dice que la IA no necesita más control que tenerlo a él como presidente de Estados Unidos | 1 | 1 |
| country | Peru | 15 | 1 | 10 | La ONU advierte que todos los derechos humanos “están en riesgo” ante el avance de la IA | 1 | 1 |
| country | Polônia | 283 | 15 | 236 | Allegro otwiera biuro w Chinach. To ważniejsze niż myślisz | 3 | 3 |
| country | Porto Rico | 57 | 3 | 47 | Gobierno crea grupo especial para atender atrasos en pagos bajo nuevo sistema ERP | 2 | 2 |
| country | Portugal | 75 | 4 | 66 | Nova Renault Trafic elétrica: 470 km de autonomia e carregamento ultrarrápido | 1 | 1 |
| country | Quênia | 21 | 5 | 14 | Meta and This Is Digital launch AI Academy Kenya with startup pitchathon and practical training | 2 | 2 |
| country | Reino Unido | 224 | 16 | 194 | OpenAI Agent Swarm Hacks RubyGems Package Manager | 2 | 2 |
| country | República Dominicana | 371 | 9 | 301 | DGII ampliará Scoring Tributario a más de 200,000 pymes | 3 | 3 |
| country | Romênia | 122 | 8 | 108 | Comunicat oficial: Apple TV este acum disponibil în România | 3 | 3 |
| country | Rússia | 281 | 10 | 227 | Nvidia выпустила профессиональную видеокарту RTX Pro 5500 Blackwell Workstation Edition с 84 Гбайт GDDR7 | 2 | 2 |
| country | São Cristóvão e Névis | 2 | 1 | 2 | Sem grupo | 0 | 0 |
| country | São Vicente e Granadinas | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Senegal | 4 | 1 | 2 | Washington : Cybastion annonce un engagement de 300 millions de dollars pour la transformation numérique du Sénégal | 2 | 1 |
| country | Sérvia | 26 | 3 | 21 | Apple releases iPadOS 27, here’s what’s new for iPad | 1 | 1 |
| country | Singapura | 36 | 5 | 34 | Z.ai completes around US$5 billion financing for next-generation GLM models | 1 | 1 |
| country | Suécia | 35 | 1 | 32 | Renaults nya pickup Niagara presenterad | 1 | 1 |
| country | Suíça | 25 | 3 | 11 | Ausgaben für digitale Aussenwerbung steigen um 12 Prozent | 2 | 2 |
| country | Suíça (edição africana) | 6 | 1 | 6 | Sem grupo | 0 | 0 |
| country | Suíça (edição Oriente Médio) | 3 | 1 | 2 | QNB Syria Brings Mastercard Payments to Global Reach | 1 | 1 |
| country | Tailândia | 21 | 4 | 19 | Salesforce เปิดตัว Trusted Enterprise AI Harness รากฐานใหม่สำหรับการใช้งาน AI ในองค์กร [PR] | 2 | 1 |
| country | Taiwan | 175 | 7 | 167 | Wiz警告3個JFrog Artifactory嚴重漏洞遭積極利用，部分漏洞被串連形成攻擊鏈 | 2 | 1 |
| country | Tanzânia | 1 | 1 | 1 | Sem grupo | 0 | 0 |
| country | Trinidad e Tobago | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Tunísia | 32 | 4 | 30 | Centenaire de l’Hôtel Carlton Tunis (1926–2026) : Une célébration mémorable au cœur de l’histoire, de l’art et du patrimoine sur l’Avenue Habib Bourguiba | 2 | 2 |
| country | Turquia | 353 | 20 | 269 | WhatsApp'ta Durum Videolarını 2x Hızda İzleyebileceksiniz | 3 | 3 |
| country | Ucrânia | 92 | 4 | 79 | Valve's Steam Frame VR headset starts at $1,059 and ships with Half Life: Alyx | 1 | 1 |
| country | Uganda | 0 | 0 | 0 | Sem grupo | 0 | 0 |
| country | Uruguai | 5 | 2 | 4 | Η Microsoft ενσωματώνει το Grok στο Copilot για Word, Excel και PowerPoint | 1 | 1 |
| country | Venezuela | 4 | 2 | 2 | La urgencia de ralentizar la IA y perder contra China divide a EEUU tras alarma del sector | 1 | 1 |
| country | Vietnã | 140 | 3 | 118 | Quá hot: Giá tăng nhưng người Việt vẫn chi ra 300 tỷ để cọc iPhone mới | 3 | 2 |
| country | Zâmbia | 5 | 1 | 4 | Pan-African Payment and Settlement System (PAPSS) Targets Accelerated Adoption and Transaction Growth as Network Expands Across Africa | 1 | 1 |
| country | Zimbábue | 12 | 2 | 10 | Zimbabwe’s Internet Penetration Rate Rises to 87.39% in Q1 2026 | 2 | 1 |
| globe | Globo | 8696 | 568 | 7238 | NVIDIA RTX PRO 5500 Blackwell oficjalnie. Na pokładzie 84 GB pamięci | 7 | 7 |

## Assuntos compartilhados

| Tema | Matérias | Veículos | Origens editoriais |
|---|---:|---:|---|
| NVIDIA RTX PRO 5500 Blackwell oficjalnie. Na pokładzie 84 GB pamięci | 7 | 7 | Alemanha, Estados Unidos, Grécia, Itália, Polônia, Turquia |
| Airrived launches observability for enterprise AI agents | 6 | 6 | Austrália, Nova Zelândia |
| Apple rilascia iOS 27, iPadOS 27, watchOS 27 e macOS 27: ecco tutte le novità | 6 | 6 | Alemanha, Chile, Chéquia, Itália, Romênia, Rússia |
| Firewalla launches Gold Plus SFP security appliance | 6 | 6 | Austrália, Nova Zelândia |
| Link4 marks 10 years as digital trade services grow | 6 | 6 | Austrália, Nova Zelândia |
| Xiaomi представила Pad 9 и Pad 9 Pro — относительно доступные планшеты на Snapdragon | 6 | 6 | Irã, Rússia, Turquia |
| Trump dice que la IA no necesita más control que tenerlo a él como presidente de Estados Unidos | 6 | 6 | Costa Rica, Guatemala, Honduras, Panamá, Paraguai, Peru |
| Donald Trump señala una “conspiración enfermiza” contra la IA | 6 | 6 | Argentina, El Salvador, Equador, Panamá, Peru, Porto Rico |
| SonicWall wins two CybersecAsia awards, joins Hall of Fame | 6 | 6 | Austrália, Nova Zelândia |
| watchOS 27 now available for Apple Watch, here’s what’s new | 6 | 6 | Canadá, Chéquia, Estados Unidos, França, Rússia, Turquia |
| Opinion: Yes, AI is coming for your job | 6 | 6 | Austrália, Nova Zelândia |
| TiVo launches Agent TiVo for AI entertainment discovery | 5 | 5 | Austrália, Nova Zelândia |
| Apple releases iPadOS 27, here’s what’s new for iPad | 5 | 5 | Canadá, Estados Unidos, Rússia, Sérvia |
| Honor Play 11 Diumumkan dengan Baterai 8300mAh | 5 | 5 | Brasil, Indonésia, Irã, Polônia |
| Roborock unveils first pool cleaner & new robot mower | 5 | 5 | Austrália, Nova Zelândia |

Não somar recortes: matérias e veículos podem estar presentes em mais de um. Evidências do tema líder de cada recorte estão em leaders_by_scope.json. Auditoria integral dos 610 grupos em cluster-audit.json.gz. Artefatos completos de rankings disponíveis no GitHub Actions acima.

Coleta correspondente: [34904308547](https://github.com/zehlima/blog-criia-rss/actions/runs/34904308547), complete_with_gaps; 675/675 tentados, 646 OK, 29 erros, 0 não tentados. 26.896 notícias ativas, 25.420 content_key, 25.415 corpos classificados válidos, 1.474 falhas de extração, 7 referências inválidas e 0 pendências. Nenhum deploy Cloudflare ou serviço contratado.
