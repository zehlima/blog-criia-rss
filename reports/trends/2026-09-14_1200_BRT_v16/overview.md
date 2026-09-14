# BLOG CRIIA — coleta e tendências — janela 12h BRT — v16

Gerado em 14/09/2026 após o fechamento retomado às 16h10 BRT.

## Estado da coleta

- Estado: `complete_with_gaps` (encerramento parcial; não equivale a cobertura integral).
- Inventário ativo derivado de `data/feeds.json`: 675 URLs.
- Tentados: 675/675 (100,0%); 649 OK (96,1%); 26 com erro (3,9%); 0 ainda não tentados.
- Notícias únicas: 24.419.
- `content_key`: 23.181; corpos válidos: 23.176. A presença de `content_key` não prova integralidade.
- Texto de página extraído: 22.305; conteúdo fornecido pelo publisher no RSS: 871; título/resumo sem corpo: 0.
- Extração: 0 pendentes, 1.236 indisponíveis e 7 referências inválidas.
- Desde o fechamento anterior: +1 corpo válido e -1 indisponível; feeds sem mudança.

Os 26 feeds com erro permanecem separados no relatório da coleta: 20 bloqueios/acesso (19 HTTP 403 e 1 destino não público), 2 XML/feed inválido, 1 HTTP 429 temporário, 1 TLS, 1 feed vazio e 1 HTTP 404. Nenhum `AttributeError` foi usado como prova de feed inválido e nenhuma substituição definitiva foi recomendada sem validação.

## Análise v16

- Execução: `34886483304`; estado técnico `ready`.
- Snapshots persistidos: 113 — 105 países editoriais, 7 continentes e 1 globo.
- Janela de 24h: 6.640 matérias — 6.050 com texto de página, 217 com conteúdo do publisher no RSS e 373 apenas com título/resumo.
- Corpus ativo: 24.412 matérias; 5.723 matérias da janela ficaram sem grupo, sem serem forçadas em temas.
- Cobertura editorial observada: matérias em 94 dos 105 países/territórios do snapshot; todos os continentes presentes. Isto não significa cobertura integral de todos os países ou feeds.
- Revisão editorial: amostra passou após verificar os padrões já reprovados e os 65 maiores grupos. É uma amostra direcionada, não benchmark geral nem validação de produção.

## Correções aplicadas e validadas

- Corpus restrito às 675 URLs ativas.
- Embeddings baseados no contexto do evento do título, reduzindo o peso de marcas/produtos genéricos.
- Grupos de diários, calendários, eventos/listagens, versões diferentes, comparações entre marcas, vendas versus testes, atualização de segurança versus proibição e ofertas com preços distintos foram separados.
- Metadados editoriais são pré-calculados uma vez por título; não são recalculados dentro da matriz de pares.
- Testes locais: 81 aprovados.

## Horários relativos ao fechamento

- País, alvo +15 min: iniciou com 350,256 s de atraso porque a preparação terminou depois do alvo.
- Continente, alvo +20 min: iniciou com 46,544 s de atraso.
- Globo, alvo +25 min: iniciou no alvo (0,000 s de atraso).

## Temas líderes

### Globo

1. Dez anos da Link4 e expansão dos serviços digitais — 6 matérias, 6 veículos, Austrália e Nova Zelândia (uma família estimada de republicação).
2. Xiaomi Pad 9/Pad 9 Pro — 6 matérias, 6 veículos, Irã, Rússia e Turquia.
3. Opinião sobre IA e empregos — 6 matérias, 6 veículos, Austrália e Nova Zelândia (uma família estimada de republicação).
4. Premiação SonicWall/CybersecAsia — 6 matérias, 6 veículos, Austrália e Nova Zelândia (uma família estimada de republicação).
5. Roborock: limpador de piscina e robô cortador — 5 matérias, 5 veículos, Austrália e Nova Zelândia (uma família estimada de republicação).

### Continentes

- América do Norte: início dos voos da Iberojet entre Espanha e El Salvador — 4 matérias, 3 veículos.
- América do Sul: apelo da ONU por regulação urgente da IA — 2 matérias, 2 veículos.
- Europa: novo StarCraft como shooter de mundo aberto — 3 matérias, 3 veículos.
- Europa/Ásia transcontinental: Huawei Watch GT 7 à venda na Turquia — 3 matérias, 3 veículos.
- Oceania: dez anos da Link4 — 6 matérias, 6 veículos.
- África: investimento de R2 bilhões da DNI na economia digital — 2 matérias, 3 veículos.
- Ásia: Xiaomi Pad 9/Pad 9 Pro — 3 matérias, 3 veículos.

### Países editoriais — destaques

- Brasil: Xiaomi Pad 9 Pro — 2 matérias, 2 veículos; 205 matérias no país, 166 sem grupo.
- Estados Unidos: agenda de Obama/Trump sobre IA — 2 matérias, 2 veículos; 472 matérias no país.
- China: Honor Magic 9 Super Edition com bateria de 11.000 mAh — 3 matérias, 2 veículos; 286 matérias no país.
- Reino Unido: violação de dados da Revolut por pedidos governamentais falsos — 2 matérias, 2 veículos.
- Argentina: apelo da ONU por regulação urgente da IA — 2 matérias, 2 veículos.
- Chile: 18 matérias, todas sem grupo; nenhum tema foi forçado.

## Assuntos compartilhados entre países

- Honor Magic 9 Super Edition: Brasil, Hong Kong (China), Itália e Turquia — 5 matérias, 5 veículos.
- Honor Play 11: Brasil, Indonésia, Irã e Polônia — 5 matérias, 5 veículos.
- NVIDIA RTX Pro 5500 Blackwell: Alemanha, Estados Unidos, Grécia, Itália e Turquia — 5 matérias, 5 veículos.
- Oppo Find X10: China, Romênia, Rússia e Turquia — 4 matérias, 4 veículos.
- 700º voo da família Falcon: Bulgária, França e Rússia — 4 matérias, 4 veículos.

País significa a origem editorial do veículo, não o local do acontecimento. Títulos são rótulos/evidências dos grupos e não foram apresentados como textos completos.

## Referências

- GitHub Actions: https://github.com/zehlima/blog-criia-rss/actions/runs/34886483304
- Correção v16: https://github.com/zehlima/blog-criia-rss/commit/9b8f33174ff57e877bf3bee5f0c5e2bd1012dc9c
- Relatório de erros da coleta: ../../monitoring/2026-09-14_1200_BRT_resume_151414_BRT/

