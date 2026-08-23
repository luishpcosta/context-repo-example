# Formato de Product Brief (PB)

O PB vive no planejamento to-be do repositório, por padrão em
`docs/refinamento/<contexto>/<slug-da-funcionalidade>/PRODUCT_BRIEF.md` (respeite a
convenção que o `CONTEXT-MAP.md` do repo já registrar, se for outra). Todo PB criado
passa pelo gate do CONTEXT-MAP (ver SKILL.md, Fase 5).

## Gerando o ID

Mesma convenção das ADRs do catálogo: `PB-<data:YYYYMMDD>-<hora:HHMM>-<sufixo
aleatório de 4 caracteres>` (ex.: `PB-20260708-1542-3f0a`).

```bash
date +%Y%m%d-%H%M
printf '%04x' $((RANDOM % 65536))
```

Não depende de histórico nem de perguntar ao usuário. Antes de usar, confira se algum
PB existente já usa o mesmo ID; se houver colisão, gere um novo sufixo. O prefixo
`PB-` importa: é por ele que o `graph_query.py` classifica o documento como nó `pb:`
no grafo.

## Front matter de relação (obrigatório)

Todo PB abre com um front matter YAML — é o metadado que alimenta o grafo de
dependências; o corpo continua markdown/prosa. Os valores de `contextos`/`afeta` usam
**o nome exato da entrada no `CONTEXT-MAP.md`**.

```yaml
---
id: PB-<id>
titulo: <nome do produto/funcionalidade>
status: rascunho            # rascunho | aprovado | superado
contextos: [<contexto principal>]
afeta: [<contexto(s) impactado(s)>]
supera: []                  # PB-id que este brief substitui; [] se nenhum
depende_de: []              # opcional: PB-id/ADR-id de que este brief depende
---
```

Regras:
- **`supera` é declarado no PB novo**, não no antigo. O `graph_query.py` deriva
  `status: superado` para o alvo — **não** edite o PB antigo à mão.
- `contextos[0]` é o contexto principal — é ele que define onde o arquivo mora.
- Se a entrevista concluiu que uma ADR precisa ser superada, isso **não** entra no
  `supera:` do PB (PB não supera ADR): o PB registra a tensão na seção Escopo e a
  superação acontece na ADR nova, quando a discussão de arquitetura chegar lá.

## Template

```md
---
id: PB-<id>
titulo: <nome>
status: rascunho
contextos: [<contexto>]
afeta: []
supera: []
depende_de: []
---

# Briefing de produto: <nome>

## Resumo executivo

<3-5 frases: o que é, para quem, por que agora. Quem lê só isto deve entender a aposta.>

## O Problema

<O problema real observado, com evidência quando houver (ticket, métrica, reclamação).
Não descreva a solução aqui.>

## A Solução

<O que se propõe construir, em linguagem de produto. Cite os termos do glossário do
contexto; se a ideia introduz um termo novo, defina-o aqui explicitamente.>

## O que torna Isto Diferente

<Por que esta abordagem e não a alternativa óbvia. Se a entrevista revelou tensão com
uma ADR ou contrato, o recorte escolhido é explicado aqui.>

## Quem Isto Serve

<Personas/atores afetados — inclua os que o grafo apontou como impactados, não só o
usuário final.>

## Critérios de Sucesso

<Como saberemos que funcionou. Métricas ou sinais observáveis, não intenções.>

## Escopo

**No escopo:**
- <capacidade 1>

**Fora do escopo:**
- <o que deliberadamente fica de fora — os "nãos" explícitos valem tanto quanto os
  "sins"; recortes negociados no checkpoint entram aqui>

## Visão

<Para onde isso pode evoluir depois desta entrega. Curto — é direção, não roadmap.>
```

As seções são todas curtas — um PB cabe em uma ou duas telas. Profundidade de
requisito (RF/RNF, jornadas, riscos) é papel do PRD (`pm-create-prd`), não do brief.
