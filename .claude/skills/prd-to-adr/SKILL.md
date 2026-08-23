---
name: prd-to-adr
description: "Use sempre que o usuário fornecer/referenciar um PRD e pedir a arquitetura de solução que o atende, ou para 'criar ADR a partir do PRD', 'quebrar em atividades por componente' ou 'gerar acceptance criteria ligadas à arquitetura'. A skill extrai os requisitos do PRD, propõe arquitetura, elicita o contrato de payload (REST/mensageria) antes de escrever Acceptance Criteria, e decompõe em atividades por componente com checkpoint humano antes de fechar o ADR. Garante ADR registrado e ACs rastreáveis ao PRD. Use mesmo sem o usuário citar 'ADR' ou 'acceptance criteria' literalmente — se a intenção é ir do requisito de produto às atividades técnicas com rastreabilidade, esta skill se aplica."
metadata:
  language: agnostic
  tags: [meta, sdd, spec-driven, adr]
---

# PRD → Arquitetura → ADR + ACs

Transforma um PRD em uma proposta de arquitetura registrada como ADR, decomposta em
atividades por componente com Acceptance Criteria (AC) rastreável.

## Quando usar

- O usuário cola ou referencia um PRD e pede a arquitetura que o atende.
- O usuário já tem um PRD e quer "as atividades por componente".
- O usuário pede para formalizar uma decisão arquitetural já discutida em ADR.

## Fluxo (siga as fases em ordem; não pule o checkpoint da Fase 5)

### Fase 1 — Extrair o essencial do PRD

Extraia, de forma explícita (mostre ao usuário antes de seguir):
- **Objetivo de negócio** (1-2 frases)
- **Requisitos funcionais** (RF-01, RF-02...)
- **Requisitos não-funcionais** (performance, disponibilidade, segurança)
- **Restrições conhecidas**
- **Fora de escopo**

Se o PRD for vago em requisitos não-funcionais, pergunte antes de prosseguir.

### Fase 2 — Propor arquitetura

1. Proponha a arquitetura que atende ao PRD (1-3 opções com trade-offs, se
   houver decisão relevante a ser tomada).
2. Para a opção escolhida (ou única), apresente os componentes e conexões
   envolvidos ao usuário como uma lista curta antes de seguir para o ADR.

### Fase 3 — Escrever o ADR

Use `references/adr-template.md`. Pontos obrigatórios:
- **Status sempre "Proposto"** até confirmação do usuário.
- A seção **Decisão** linka aos RF-/RNF- da Fase 1.
- Liste os componentes afetados.
- Inclua **Alternativas consideradas**.
- Gere o identificador como `ADR-<data:YYYYMMDD>-<hora:HHMM>-<sufixo
  aleatório de 4 caracteres>` (ex.: `ADR-20260620-1542-3f0a`) — via Bash:
  `date +%Y%m%d-%H%M` para a data/hora e `printf '%04x' $((RANDOM % 65536))`
  para o sufixo. Não depende de histórico nem de perguntar ao usuário.
  Antes de usar, confira se já existe `adr/ADR-<id>-*.md` no projeto; se
  existir (colisão), gere um novo sufixo e tente de novo.
- Preencha o **front matter de relação** do template
  (`id`/`titulo`/`status`/`contextos`/`afeta`/`supera`/`depende_de`), usando os nomes
  exatos das entradas do `CONTEXT-MAP.md` quando ele existir — é o que registra a ADR no
  grafo de dependências mantido pela skill `blueprintfy`. Se esta decisão substitui uma
  anterior, declare `supera: [<ADR-id>]` aqui, na ADR **nova** (a antiga não é editada).
  Se o PRD de origem tiver front matter com `id: PRD-...` (gerado pela skill
  `pm-create-prd`), inclua esse id em `depende_de: [PRD-<id>]` e parta dos
  `contextos`/`afeta` do PRD ao preencher os da ADR — é o que fecha a cadeia
  PB → PRD → ADR no grafo.

**Diagrama da arquitetura (assim que o ADR for criado):** se a skill
`make-diagram` estiver disponível no ambiente (instalada como skill do
agente), acione-a logo após gravar o arquivo do ADR para gerar o diagrama
da arquitetura decidida como imagem, salvando ao lado do ADR
(`adr/ADR-<id>-diagrama.png`) e referenciando-o na seção **Decisão**
(`![Arquitetura](./ADR-<id>-diagrama.png)`). Se `make-diagram` não estiver
disponível, use o diagrama Mermaid inline do template como fallback.

### Fase 3.5 — Elicitar o contrato de payload (antes das ACs)

"Descrever o contrato explicitamente" na AC (Fase 4) não acontece por conta
própria — alguém precisa elicitar campos, tipos e regras de erro antes de
escrever a AC. Essa elicitação é diferente para REST e para mensageria,
porque o risco é diferente: em REST, quem sofre o erro é quem chama, na
hora; em mensageria, quem sofre não é quem publica, são os consumidores
desacoplados — que podem nem estar no radar da demanda atual.

Aplique esta fase a toda conexão que troca payload estruturado como parte
da arquitetura proposta (pule conexões sem payload estruturado, ex.:
leitura direta de banco). Ver `references/contrato-payload.md` para o
roteiro completo; resumo:

**REST (síncrono)** — pergunte e registre: campos do payload (request e
response), tipo de cada campo, obrigatoriedade, contrato de erro (status
codes + formato do corpo de erro por cenário de negócio) e idempotência em
escrita (como uma repetição/retry é tratada).

**Mensageria (assíncrono)** — pergunte e registre: versionamento do schema
do evento, compatibilidade (campo novo é **sempre opcional**; remover ou
renomear campo é breaking change), idempotência do consumidor (chave de
deduplicação para entrega at-least-once) e política de DLQ. Antes de propor
qualquer mudança em payload de evento/tópico já existente, **pergunte
diretamente ao usuário** quem consome esse tópico/evento hoje (mesmo que
nenhum apareça no PRD/demanda atual) e se a mudança é compatível com cada
um.

Se alguma resposta ficar pendente após uma rodada de perguntas, registre
como assunção explícita (mesmo critério das demais fases) e leve isso para
o ADR.

### Fase 4 — Decompor em atividades por componente

Cada **atividade** representa o recorte completo a ser implementado por um
componente para atender ao ADR — não um passo minúsculo. Por isso, é normal
que uma atividade seja extensa (várias ACs, múltiplos endpoints/casos de
contrato). Não force atividades artificialmente pequenas.

Use IDs `ADR-XXX-AT-NN`, ACs com `ADR-XXX-AC-NN` (ver `references/ac-template.md`).
Toda atividade que envolve uma conexão com contrato (REST ou mensageria)
precisa de AC descrevendo esse contrato explicitamente — usando o que foi
elicitado na Fase 3.5 (campos/tipos/erros/idempotência para REST;
versionamento/compatibilidade/idempotência do consumidor/DLQ para
mensageria), não só "deve funcionar".

**Oferecer quebra quando a atividade for extensa**: depois de listar uma
atividade com várias ACs, se ela parecer grande (muitos cenários, mistura
responsabilidades distintas, ou o usuário comentar que está extensa),
pergunte explicitamente se o usuário quer quebrá-la em duas ou mais
atividades (ex.: `ADR-XXX-AT-01a` e `ADR-XXX-AT-01b`, ou `AT-01`/`AT-02`
separando por sub-responsabilidade). Nunca quebre sem perguntar — a decisão
de granularidade é do usuário, a skill só sinaliza quando o recorte parece
grande demais para uma entrega só.

### Fase 5 — Checkpoint humano (obrigatório, não pule)

Antes de finalizar:
1. Apresente a lista de atividades por componente.
2. Pergunte se alguma atividade deve virar um ADR separado (múltiplos times,
   risco técnico alto, entrega independente).

### Fase 6 — Entregáveis do PRD

Gere como arquivos (sempre arquivo, nunca só inline):
- `adr/ADR-XXX-titulo.md`
- `adr/ADR-XXX-acs.md`
- `adr/ADR-XXX-diagrama.png` (somente se `make-diagram` estiver disponível — ver Fase 3)

**Gate do CONTEXT-MAP (se existir `CONTEXT-MAP.md` na raiz do projeto):** o mapa é o
índice de navegação do repo, e documento fora do mapa é invisível. Depois de gravar
os arquivos, (1) verifique se cada um é alcançável a partir do `CONTEXT-MAP.md` (o
arquivo ou a pasta que o contém está referenciado — tipicamente na seção
*Planejamento (to-be)* do contexto certo); (2) se não for, adicione a referência na
seção adequada, perguntando ao usuário se o contexto/seção for ambíguo; (3) valide:
releia o mapa, confira que o caminho referenciado existe no disco e reporte o
resultado ao usuário. Se a ADR declarou `supera:`, confira que o `<ADR-id>` alvo
existe e avise o usuário que aquela decisão passou a superada. Os entregáveis só estão
completos depois desse gate.

## Arquivos de referência

- `references/adr-template.md` — template de ADR.
- `references/ac-template.md` — template de Atividade + Acceptance Criteria.
- `references/contrato-payload.md` — roteiro de elicitação do contrato de
  payload (REST vs. mensageria), usado na Fase 3.5.