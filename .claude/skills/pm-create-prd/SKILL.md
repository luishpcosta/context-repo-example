---
name: pm-create-prd
description: "Converte um Product Brief (PB) em um ou mais PRDs completos (10 seções: de identificação e contexto a riscos e premissas), decidindo a quebra pelo tamanho real do impacto: consulta o CONTEXT-MAP.md e o grafo de dependências para medir quantos contextos o PB toca, avalia atores/personas, dependências entre capacidades e reversibilidade — e, se o PB for grande, argumenta a divisão em N PRDs encadeados por depende_de com checkpoint humano ANTES de gerar qualquer arquivo. Detecta e confronta PB superado em vez de detalhá-lo. Use sempre que o usuário pedir 'gera o PRD', 'detalha esse brief', 'quebra isso em PRDs', ou apontar um PRODUCT_BRIEF.md pedindo o próximo passo — mesmo sem citar 'PRD'. Se a intenção é ir do briefing aprovado para requisitos prontos para arquitetura (prd-to-adr), esta skill se aplica."
metadata:
  language: agnostic
  tags: [product, prd, requirements, sdd, ddd]
---

# PM: Product Brief → PRD(s)

Recebe um Product Brief (PB) e o converte em requisitos detalhados — um PRD, ou vários
encadeados por dependência. A pergunta central da skill não é "como escrever um PRD?",
é **"quantos PRDs este PB realmente pede?"**: um PB multi-contexto detalhado em um
documento único vira um monólito de requisitos que ninguém consegue entregar
incrementalmente; um PB atômico quebrado em três PRDs vira burocracia. A decisão de
quebra é argumentada com o usuário antes de qualquer arquivo existir.

Esta skill é o elo entre o `pm-create-pb` (que gera o PB) e o `prd-to-adr` (que
transforma cada PRD em arquitetura + ADR + acceptance criteria).

## Fase 0 — Localizar e validar o PB

1. Leia o PB indicado pelo usuário e o `CONTEXT-MAP.md` da raiz (único ponto de
   entrada de navegação). Se o usuário não apontou o arquivo, localize-o pela seção
   `## Planejamento (to-be)` do mapa — não escaneie pastas fora do mapa.
2. Consulte o grafo (ver "Consultando o grafo"): rode `vigentes contexto:<Nome>` para
   os contextos do PB. **Se o PB estiver superado** (outro PB declara `supera:` sobre
   ele), confronte antes de detalhar: "o PB-X foi superado pelo PB-Y — detalhar o
   superado vai gerar requisitos de uma aposta abandonada. Sigo com o PB-Y?". Não
   gere PRD de PB superado sem decisão explícita do usuário.
3. **PB sem front matter** (escrito à mão, fora do `pm-create-pb`): ofereça o
   backfill (`id`, `contextos`, `afeta`, `supera`, `depende_de` — formato em
   `references/prd-template.md`) antes de seguir, para o PB e os PRDs entrarem no
   grafo. Se o usuário recusar, siga mesmo assim e sinalize a limitação.

## Consultando o grafo

O script `graph_query.py` é distribuído com a skill `blueprintfy`. Procure-o nesta
ordem, a partir da raiz do repo-alvo:

1. `.claude/skills/blueprintfy/scripts/graph_query.py`
2. `.agents/skills/blueprintfy/scripts/graph_query.py`
3. Pasta irmã desta skill: `../blueprintfy/scripts/graph_query.py`

Sem o script (ou sem `python3`), faça a travessia manual: links do `CONTEXT-MAP.md` →
front matter dos docs alcançáveis (`contextos`, `afeta`, `supera`, `depende_de`).
**Grafo vazio ≠ "sem tensões"** — em repo cujos docs não têm front matter, leia os
documentos diretamente antes de concluir qualquer coisa.

## Fase 1 — Análise de escala

Avalie os quatro critérios de `references/criterios-de-escala.md` e **mostre a
avaliação ao usuário** (é ela que justifica a decisão de quebra):

1. **Contextos tocados** — `contextos` + `afeta` do PB, conferidos com
   `impacto contexto:<Nome>` no grafo (o PB pode ter subestimado o alcance).
2. **Atores/personas** — quantos perfis distintos a seção "Quem Isto Serve" descreve.
3. **Dependência entre capacidades** — as capacidades do escopo dependem umas das
   outras ou são entregáveis de forma independente?
4. **Risco/reversibilidade** — é fácil desfazer depois? Decisões difíceis de reverter
   pedem PRDs menores, com fronteiras que permitam parar no meio.

Regra de decisão: **1 contexto + capacidades acopladas + poucos atores → 1 PRD
direto** (siga para a Fase 3). Qualquer outro arranjo → proponha a quebra (Fase 2).

## Fase 2 — Proposta de quebra + checkpoint humano (obrigatório quando N > 1)

Argumente a quebra **antes** de gerar qualquer arquivo, nomeando capacidades,
contextos e a cadeia de dependência:

> "Esse PB toca os contextos X, Y e Z e tem 3 capacidades que não dependem entre si.
> Sugiro dividir em:
> - PRD-1 (capacidade A, contexto X) — pode entregar isolado
> - PRD-2 (capacidade B, contexto Y) — depende do PRD-1
> - PRD-3 (capacidade C, contexto Z) — independente"

Espere a resposta. **Nenhum arquivo de PRD é criado antes do checkpoint** — a quebra
define fronteiras de entrega e de arquitetura; errar aqui propaga para todos os ADRs
seguintes. Se o usuário ajustar a quebra, a versão dele vence.

## Fase 3 — Geração dos PRDs

Use `references/prd-template.md` (front matter + corpo com as 10 seções). Pontos que
não são opcionais:

- **ID**: `PRD-<YYYYMMDD>-<HHMM>-<hex4>` (mesmo gerador das ADRs/PBs; confira
  colisão). O prefixo `PRD-` é o que classifica o nó no grafo.
- **Arquivo**: `NNN-<slug-da-capacidade>-PRD.md` na mesma pasta do PB de origem, com
  `NNN` sequencial dentro da pasta (001, 002...). Respeite a convenção do repo se o
  mapa registrar outra.
- **Front matter**: `depende_de` sempre inclui o `id` do PB de origem; PRDs que
  dependem de outros PRDs da mesma quebra os listam também
  (`depende_de: [PB-..., PRD-...]`). É essa cadeia que o grafo consulta depois.
- **Requisitos com ID**: `RF-01`, `RNF-01`... — o `prd-to-adr` extrai exatamente esses
  IDs para rastrear acceptance criteria; sem eles a rastreabilidade quebra.
- **Seção 8 (Dependências e Restrições)** cita as ADRs **vigentes** que restringem a
  solução (achadas na Fase 0/1) — não repita premissas de ADR superada.

## Fase 4 — Gate do CONTEXT-MAP

Cada PRD criado passa pelo gate de criação de documento (mesma disciplina do
`blueprintfy`/`prd-to-adr`):

1. **Alcance** — o arquivo (ou a pasta do PB, que normalmente já cobre) é alcançável
   a partir do `CONTEXT-MAP.md`?
2. **Registro** — se não for, adicione a referência em `## Planejamento (to-be)`.
3. **Validação** — releia o mapa, confirme caminhos no disco e reporte ao usuário.

Se algum PRD declarou `supera:`, rode `graph_query.py vigentes` (ou travessia manual)
e reporte qual doc passou a superado.

## Próximo passo

Cada PRD gerado é insumo direto da skill `prd-to-adr` (arquitetura + ADR + acceptance
criteria rastreáveis). Se houver cadeia de dependência, recomende começar pelo PRD sem
dependências. Mencione isso ao entregar.

## Arquivos de referência

- `references/criterios-de-escala.md` — os 4 critérios da análise de escala e a regra
  de decisão 1 PRD vs N PRDs, com exemplos.
- `references/prd-template.md` — geração de ID, front matter de relação e corpo do PRD
  (10 seções).
