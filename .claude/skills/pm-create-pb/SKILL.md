---
name: pm-create-pb
description: "Transforma uma ideia, demanda ou ticket solto em um Product Brief (PB) ancorado no modelo de domínio existente: lê o CONTEXT-MAP.md ANTES de qualquer pergunta, cruza a ideia com bounded contexts, contratos e ADRs vigentes (via grafo de dependências ou travessia manual), roda uma entrevista de impacto uma pergunta por vez e — se a ideia atravessar domínios ou conflitar com decisão registrada — argumenta e exige checkpoint humano antes de fechar o brief. Use sempre que o usuário chegar com 'tive uma ideia', 'chegou essa demanda', 'quero tirar esse ticket do papel', 'escreve um briefing disso', 'formaliza esse pedido do cliente' — mesmo sem citar 'PB' ou 'product brief'. Se a intenção é sair de uma demanda vaga para um briefing de produto registrado e rastreável no mapa do repositório, esta skill se aplica."
metadata:
  language: agnostic
  tags: [product, product-brief, discovery, sdd, ddd, interview]
---

# PM: Ideia → Product Brief

Recebe uma ideia crua (texto livre, transcrição de conversa, ticket) e a transforma em
um Product Brief (PB) que nasce **dentro** do modelo de domínio existente — não ao lado
dele. A diferença para escrever um briefing direto é a ordem: primeiro o território
(contextos, contratos, decisões já tomadas), depois a entrevista, e só então o
documento. Um PB escrito sem esse reconhecimento tende a redescobrir conflitos com ADRs
na fase de arquitetura, quando desfazer custa caro.

Esta skill complementa o `blueprintfy` (que funda e afia o modelo de domínio) — aqui o
modelo já existe e a pergunta é outra: **qual o impacto desta ideia sobre ele?** O
próximo elo da cadeia é o `pm-create-prd` (PB → PRDs) e, depois, o `prd-to-adr`.

## Fase 0 — Reconhecimento do território (antes de qualquer pergunta)

Leia o `CONTEXT-MAP.md` da raiz do repositório **antes de entrevistar** — ele é o único
ponto de entrada de navegação (documentos fora do mapa não existem para o modelo). A
partir dele:

1. Identifique os **contextos candidatos** que a ideia parece tocar (leia o
   `CONTEXT.md` de cada um, em especial a seção `## Linguagem`).
2. Levante as **ADRs vigentes** que restringem ou habilitam a ideia.
3. Verifique se a ideia **esbarra em algo já decidido** — reafirma uma premissa
   superada, contradiz uma fronteira de contexto, mexe em contrato publicado.

Para os passos 2 e 3, consulte o grafo de dependências em vez de reler todas as ADRs à
mão (ver "Consultando o grafo" abaixo):

```
python3 <graph_query.py> --map ./CONTEXT-MAP.md vigentes contexto:<Nome>
python3 <graph_query.py> --map ./CONTEXT-MAP.md impacto contexto:<Nome>
```

O resultado desta fase é um resumo curto apresentado ao usuário antes da primeira
pergunta: "a ideia parece tocar o contexto X; encontrei as ADRs A e B vigentes sobre
isso; a ADR C foi superada — vou considerar isso na entrevista".

### Conflito direto → argumente agora, não espere a entrevista terminar

Se o passo 3 revelar que a ideia **reafirma uma premissa já superada** ou **contradiz
diretamente uma ADR vigente** — não é uma tensão sutil que a entrevista ainda vai
revelar, é um conflito visível já no reconhecimento —, não abra a Fase 1. Vá direto
para a Fase 3 (argumentação + checkpoint humano, com pelo menos duas opções concretas)
antes de fazer qualquer pergunta de entrevista. A razão é prática: a resposta do
usuário a esse conflito redefine o escopo de tudo o que a entrevista perguntaria a
seguir — perguntar antes é gastar a atenção do usuário em perguntas que talvez nem se
apliquem ao recorte que ele vai escolher.

Depois do checkpoint, a entrevista (Fase 1) roda normalmente, mas já dentro do recorte
que o usuário decidiu — a pergunta "existe ADR que precisaria ser superada?" some da
lista, porque já foi respondida aqui.

Se o conflito só aparecer **durante** a entrevista (a pergunta 5 de
`entrevista-de-impacto.md` é que o revela), aí sim ele dispara a Fase 3 no ponto em que
foi descoberto — o curto-circuito acima é só para quando o conflito já é óbvio desde a
Fase 0.

**Se não existir `CONTEXT-MAP.md` na raiz**: avise que o repositório ainda não tem o
mapa. Se a skill `blueprintfy` estiver disponível, ofereça rodar o bootstrap dela
primeiro (o PB fica muito melhor ancorado). Se não estiver, pergunte ao usuário onde
vivem os documentos de negócio e ADRs, siga sem grafo e sinalize a limitação no PB.

## Consultando o grafo

O script `graph_query.py` é distribuído com a skill `blueprintfy` — não é duplicado
aqui, para não divergir. Procure-o nesta ordem, a partir da raiz do repo-alvo:

1. `.claude/skills/blueprintfy/scripts/graph_query.py`
2. `.agents/skills/blueprintfy/scripts/graph_query.py`
3. Pasta irmã desta skill: `../blueprintfy/scripts/graph_query.py`

Se não encontrar o script (ou não houver `python3`), faça a **travessia manual**: leia
os links do `CONTEXT-MAP.md`, o front matter dos docs alcançáveis (`contextos`,
`afeta`, `supera`, `depende_de`) e siga as relações à mão. **Grafo vazio ≠ "sem
tensões"**: num repo cujos docs ainda não têm front matter, o grafo nasce vazio — nunca
conclua "nenhum conflito" a partir daí; leia as ADRs diretamente.

## Fase 1 — Entrevista de impacto

Rode a entrevista seguindo a disciplina em `references/entrevista-de-impacto.md`. O
essencial: **uma pergunta por vez, sempre com resposta recomendada**, e toda pergunta
que o código ou o grafo podem responder é respondida por eles, não pelo usuário. As
perguntas centrais:

- A ideia **estende um contexto existente ou sugere um novo**?
- Ela **consome ou modifica um contrato já publicado** entre contextos?
- **Quem mais é afetado** se isso for pra frente? — apresente os candidatos que o grafo
  (`impacto`) já apontou, em vez de perguntar às cegas.
- Precisa de **termo novo na linguagem onipresente** (glossário do contexto)?
- Existe **ADR que precisaria ser superada** para a ideia valer?

## Fase 2 — Avaliação de impacto

Antes de fechar o PB, classifique o impacto com base no que a entrevista revelou:

- **Contido**: cabe em um único bounded context, não conflita com ADR vigente, não
  mexe em contrato compartilhado. → Siga direto para a Fase 4.
- **Amplo ou conflitante**: atravessa dois ou mais contextos, exige superar uma ADR
  vigente, ou altera um contrato publicado. → Passe pela Fase 3 obrigatoriamente.

## Fase 3 — Argumentação + checkpoint humano (obrigatório quando amplo/conflitante)

Pode ser disparada em dois momentos: aqui, depois da Fase 2, quando é a entrevista que
revela o impacto amplo/conflitante; ou **antes da Fase 1**, quando a Fase 0 já
encontrou um conflito direto com ADR vigente (ver "Conflito direto" acima). Em
qualquer um dos dois casos, argumente **antes** de fechar o PB — o objetivo é que a
decisão de escopo seja do usuário, tomada com o mapa na mesa, e não uma surpresa
embutida no documento. Formato:

> "Essa ideia toca os contextos X e Y, e Y já tem a ADR-012 que estabelece Z.
> Prosseguir aqui exigiria revisar essa ADR. Sugiro:
> - tratar como uma extensão do contexto X apenas, ou
> - abrir uma discussão de superação da ADR-012 antes de formalizar o PB."

Espere a resposta. **Nunca grave o PRODUCT_BRIEF.md antes do checkpoint** nesses casos
— um brief gravado com escopo errado vira fonte de verdade errada. Se o usuário aceitar
um recorte, o PB reflete o recorte; se decidir enfrentar a ADR, o PB declara `supera:`
e isso fica explícito no front matter.

## Fase 4 — Geração do PB

Use `references/pb-template.md` (front matter + corpo com as 8 seções). Pontos que não
são opcionais:

- **ID**: `PB-<YYYYMMDD>-<HHMM>-<hex4>` — mesmo gerador das ADRs do catálogo (ver
  template). Confira colisão antes de usar.
- **Front matter de relação** (`contextos`, `afeta`, `supera`, `depende_de`) com os
  nomes **exatos** das entradas do `CONTEXT-MAP.md` — é o que faz o PB entrar no grafo
  de dependências. `status: rascunho` no nascimento.
- **Caminho**: por padrão `docs/refinamento/<contexto>/<slug-da-funcionalidade>/PRODUCT_BRIEF.md`,
  onde `<contexto>` é `contextos[0]`. Se o `CONTEXT-MAP.md` do repo já registrar outra
  convenção de planejamento (to-be), respeite a do repo. PB multi-contexto vive sob o
  contexto principal; os demais entram em `afeta`. Se o contexto principal for ambíguo,
  pergunte — não adivinhe onde o documento vai morar.

## Fase 5 — Gate do CONTEXT-MAP

O PB só está entregue quando passa pelo gate de criação de documento (a mesma
disciplina do `blueprintfy`/`prd-to-adr`: quem cria, registra e valida):

1. **Alcance** — o novo arquivo (ou a pasta que o contém) é alcançável a partir do
   `CONTEXT-MAP.md`?
2. **Registro** — se não for, adicione a referência na seção `## Planejamento (to-be)`
   do mapa (crie a seção se não existir; se a seção certa for ambígua, pergunte).
3. **Validação** — releia o mapa, confirme que o caminho existe no disco e que nenhum
   link quebrou, e reporte o resultado ao usuário.

Se o PB declarou `supera:`, rode `graph_query.py vigentes contexto:<Nome>` (ou a
travessia manual) e reporte qual PB passou a superado — o doc antigo **não** é editado.

## Próximo passo

Com o PB aprovado pelo usuário (`status: aprovado`), o caminho natural é a skill
`pm-create-prd`, que avalia a escala do PB e o converte em um ou mais PRDs. Mencione
isso ao entregar.

## Arquivos de referência

- `references/entrevista-de-impacto.md` — disciplina da entrevista (uma pergunta por
  vez, resposta recomendada, grafo antes de pergunta) adaptada a impacto sobre domínio
  existente.
- `references/pb-template.md` — geração de ID, front matter de relação e corpo do
  Product Brief.
