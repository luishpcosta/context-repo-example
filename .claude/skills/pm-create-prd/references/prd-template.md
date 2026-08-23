# Formato de PRD

O PRD vive na mesma pasta do PB de origem, como `NNN-<slug-da-capacidade>-PRD.md`
(`NNN` sequencial dentro da pasta: 001, 002...). Todo PRD criado passa pelo gate do
CONTEXT-MAP (ver SKILL.md, Fase 4).

## Gerando o ID

Mesma convenção das ADRs/PBs do catálogo: `PRD-<data:YYYYMMDD>-<hora:HHMM>-<sufixo
aleatório de 4 caracteres>` (ex.: `PRD-20260708-1610-9c2b`).

```bash
date +%Y%m%d-%H%M
printf '%04x' $((RANDOM % 65536))
```

Antes de usar, confira colisão com PRDs existentes; se houver, gere outro sufixo. O
prefixo `PRD-` importa: é por ele que o `graph_query.py` classifica o documento como
nó `prd:` no grafo. O `NNN-` do nome do arquivo é ordem de leitura dentro da pasta —
a dependência real fica no front matter, não no número.

## Front matter de relação (obrigatório)

Os valores de `contextos`/`afeta` usam **o nome exato da entrada no
`CONTEXT-MAP.md`**. `depende_de` sempre inclui o PB de origem; PRDs da mesma quebra
que dependem entre si listam também os `PRD-id` precedentes — é essa cadeia que
responde "posso entregar este isolado?" no grafo.

```yaml
---
id: PRD-<id>
titulo: <funcionalidade/capacidade>
status: rascunho            # rascunho | aprovado | superado
contextos: [<contexto principal>]
afeta: [<contexto(s) impactado(s)>]
supera: []                  # PRD-id que este substitui; [] se nenhum
depende_de: [<PB-id>]       # o PB de origem sempre entra; some PRD-id precedentes
---
```

`supera` é declarado no PRD novo, nunca editando o antigo — o `graph_query.py` deriva
o `status: superado` do alvo.

## Template

```md
---
id: PRD-<id>
titulo: <capacidade>
status: rascunho
contextos: [<contexto>]
afeta: []
supera: []
depende_de: [<PB-id>]
---

# PRD: <capacidade>

## 1. Identificação

- **Produto**: <produto/área>
- **Funcionalidade**: <capacidade deste PRD>
- **Responsável**: <quem responde por este PRD>
- **Data**: <AAAA-MM-DD>
- **Status**: Rascunho

## 2. Contexto e Problema

### 2.1 Cenário atual (as-is)

<Como funciona hoje. Cite os termos do glossário do contexto (CONTEXT.md) — não
invente sinônimos para conceitos que já têm nome.>

### 2.2 Problema

<O problema que esta capacidade resolve — herdado do PB, mas recortado para o escopo
deste PRD.>

### 2.3 Oportunidade / Valor

<O que se ganha resolvendo. Se o PB tem métrica, referencie-a.>

## 3. Objetivo

### 3.1 Objetivo principal

<Uma frase. Se precisar de "e", provavelmente são dois PRDs.>

### 3.2 Métricas de sucesso

<Sinais observáveis, com baseline quando existir.>

## 4. Escopo

### 4.1 No escopo

- <capacidade/comportamento coberto por este PRD>

### 4.2 Fora do escopo (não faz)

- <o que fica de fora — inclua o que foi parar em OUTRO PRD da mesma quebra, com o
  id: "concessão de crédito → PRD-...">

## 5. Usuários / Personas

- **Personas**: <perfis deste PRD>
- **JTBD**: <job to be done de cada persona>
- **Jornada (happy path)**: <passo a passo do fluxo principal>
- **Cenário alternativo**: <variação legítima do fluxo>
- **Cenário de erro**: <o que acontece quando dá errado — e o que o usuário vê>

## 6. Requisitos Funcionais

- **RF-01**: <requisito testável>
- **RF-02**: ...

## 7. Requisitos Não Funcionais

- **RNF-01**: <performance, disponibilidade, segurança, auditoria...>

## 8. Dependências e Restrições

- <ADRs vigentes que restringem a solução, com id — ex.: "ADR-... estabelece estorno
  assíncrono; este PRD não pode assumir confirmação síncrona">
- <dependências de outros PRDs/sistemas, espelhando o `depende_de` do front matter>

## 9. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| <risco> | <impacto> | <mitigação> |

## 10. Premissas

- <o que se assume verdadeiro sem verificação — se uma premissa cair, o PRD precisa
  ser revisto>
```

Os IDs `RF-`/`RNF-` são obrigatórios: a skill `prd-to-adr` extrai exatamente esses
identificadores para rastrear acceptance criteria até o requisito de origem.
