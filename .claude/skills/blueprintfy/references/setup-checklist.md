# Checklist de setup inicial (Modo 1)

Este roteiro só roda quando o repositório ainda não tem `CONTEXT-MAP.md` na raiz e o
usuário quer estabelecer a base do modelo de domínio — não em toda conversa. Se o mapa
já existe, vá direto para o Modo 2 do `SKILL.md`.

Este roteiro é sempre a **primeira configuração** da skill no repositório — não
assuma nenhum uso anterior dela, nem estrutura deixada por ela. Só existem dois
cenários: **repo sem documentação** (nada escrito ainda) e **repo já documentado**
(código em produção e documentos de negócio espalhados — em qualquer formato, nome ou
pasta). O roteiro é o mesmo nos dois, com uma diferença de postura no repo
documentado: há mais coisa para inventariar nas Perguntas 1-3, e o resultado do setup
é sempre **criar o `CONTEXT-MAP.md` na raiz** registrando o que o usuário confirmar —
questione, não imponha: cada documento/pasta encontrado é uma proposta a validar,
nunca uma entrada automática do mapa.

## 1. Pergunte, não assuma

Faça as três perguntas do checklist **uma de cada vez**, na ordem abaixo — a ordem
importa porque cada resposta muda o que fazer na próxima etapa.

### Pergunta 1 — Documentos de negócio

"Já existem documentos de negócio escritos sobre este projeto? (PRDs, briefings,
specs, RFCs, atas de decisão, tickets longos)"

- **Sim** → peça o(s) caminho(s) ("onde eles estão? uma pasta, um link, arquivos
  soltos?").
- **Não** → não force a busca. Pule para o Modo 2 e deixe o glossário nascer da
  conversa.

### Pergunta 2 — ADRs existentes

"Já existem decisões arquiteturais registradas (ADRs) neste repositório?"

- **Sim** → peça o caminho. Se o repo já usa uma convenção própria (pasta e formato
  diferentes de `adr/ADR-<id>-titulo.md`), **respeite a convenção existente** em vez
  de forçar a deste catálogo — o objetivo é não fragmentar o histórico de decisões do
  projeto.
- **Não** → nenhuma ação; a primeira ADR será criada organicamente quando (e se)
  surgir uma decisão que qualifique, seguindo `adr-template.md`.

### Pergunta 3 — Múltiplos contextos

Antes de perguntar, dê uma primeira leitura na estrutura do repo (pastas de topo em
`src/`, múltiplos serviços num monorepo, múltiplos `package.json`/`go.mod` etc.) para
chegar com uma hipótese, não uma pergunta em branco:

"Percebi [sinais concretos, ex.: `src/ordering` e `src/billing` com times/deploys
separados] — isso sugere contextos separados. Isso está certo, ou é tudo um domínio
só?"

Se os sinais estruturais forem fracos ou ambíguos, pergunte diretamente sem propor
hipótese. A estrutura é sempre `CONTEXT-MAP.md` na raiz — o que está em jogo aqui é
**quantos contextos entram no mapa e onde o `CONTEXT.md` de cada um vai viver**.
**Nunca decida isso sozinho** — essa escolha define onde tudo vai morar dali em
diante e é cara de desfazer depois. Se a Pergunta 1 tiver identificado um glossário
já escrito (qualquer nome ou local), inclua-o na proposta: pergunte se ele vira o
`CONTEXT.md` de um contexto (referenciado pelo mapa onde está, ou movido para a pasta
do contexto) ou se os termos precisam ser divididos entre contextos.

## 2. Se houver documentos de negócio: escaneie e proponha rascunho

1. Leia os documentos indicados.
2. Extraia candidatos a termos de domínio — substantivos que aparecem repetidamente e
   carregam significado específico do negócio (não conceitos técnicos genéricos; ver
   regra em `context-format.md`).
3. Para cada termo candidato, monte uma definição curta (1-2 frases) baseada no que o
   documento diz — não invente comportamento que o texto não sustenta.
4. Apresente o rascunho **termo a termo** ao usuário antes de gravar qualquer arquivo:
   ```
   Rascunho da seção de linguagem (CONTEXT.md) a partir de <documento>:

   **Order**: <definição extraída>
   **Invoice**: <definição extraída>

   Isso bate com o que vocês usam? Algum termo faltando, errado ou que deveria virar
   "Evitar" de outro?
   ```
5. Só grave o `CONTEXT-MAP.md` e o(s) `CONTEXT.md` de contexto depois
   da confirmação. Nunca escreva o arquivo direto a partir da extração automática —
   documentos de negócio usam a linguagem de quem escreveu, que nem sempre é a
   linguagem que o time quer canonizar no código.

## 3. Se houver ADRs existentes: leia e resuma

1. Leia as ADRs indicadas.
2. Resuma as decisões já tomadas que têm relação com fronteiras de contexto ou
   linguagem onipresente (não precisa resumir toda ADR técnica que não toca em
   modelagem de domínio).
3. Se alguma decisão já registrada conflita com a estrutura de contexto que está sendo
   proposta na Pergunta 3, traga isso à tona antes de seguir — é o mesmo tipo de
   contradição que o Modo 2 aponta ao cruzar glossário com código.
4. **Proponha o backfill do front matter de relação** (opcional, mas é o que liga o
   grafo). ADRs e `CONTEXT.md` de um repo brownfield vêm **sem** front matter, então
   `scripts/graph_query.py` enxerga um grafo vazio e avisa que está vazio — ele não
   inventa as relações. Ao resumir cada ADR relevante, ofereça preencher seu front
   matter (`id`/`titulo`/`status`/`contextos`/`afeta`/`supera`) a partir do que a ADR já
   diz — em especial, **detecte supersessões implícitas** (uma ADR nova que abandonou a
   premissa de uma antiga) e proponha declarar `supera:` na nova. É preguiçoso e
   validado: proponha ADR a ADR, não grave sem a confirmação do usuário, e comece pelas
   que tocam fronteiras de contexto. Sem esse backfill, o repo funciona, mas as
   consultas de grafo continuam no fallback manual.

## 4. Decida a estrutura e crie os arquivos

- **Sempre crie o `CONTEXT-MAP.md` na raiz** (esqueleto em
  `assets/CONTEXT-MAP.md.template`, formato em `context-format.md`) listando os
  contextos confirmados e como se relacionam — mesmo que seja um único contexto (o
  mapa terá uma entrada só). Não existe a variante "só `CONTEXT.md` na raiz".
- **Um `CONTEXT.md` por contexto**, vivendo onde o repo preferir (`src/<contexto>/`,
  `docs/<dominio>/<contexto>/`...) — pergunte ao usuário onde cada um deve morar; é o
  mapa que registra o caminho. O conteúdo do arquivo é do repo (visão geral de
  negócio, BPM...); a skill não impõe esqueleto — ela cria/mantém apenas a seção
  `## Linguagem` com os termos confirmados (formato em `context-format.md`).
- **Glossário já escrito no repo** → proponha incorporá-lo: pergunte se o arquivo
  vira o `CONTEXT.md` de um contexto (referenciado pelo mapa onde está, ou movido
  para a pasta do contexto) ou se os termos são divididos entre contextos. Questione
  antes de mover ou gravar qualquer coisa.
- **Front matter de relação nos `CONTEXT.md`** → ao criar/incorporar cada contexto,
  ofereça declarar no topo do `CONTEXT.md` as relações já conhecidas
  (`depende_de`, `compartilha_contrato_com`) — é o que alimenta o grafo. Só declare o
  que o usuário confirmar; relação não declarada é tratada como violação por
  `valida-aresta`. Formato em `context-format.md` ("Front matter de relação").
- **Registre no mapa os documentos que já existem** → se as Perguntas 1 e 2
  identificaram documentos de negócio (as-is) e/ou pastas de planejamento to-be
  (PRDs/ADRs/SPECs de SDD), adicione-os às seções opcionais **Documentos de negócio
  (as-is)** e **Planejamento (to-be)** do `CONTEXT-MAP.md`. A partir daí valem as
  regras de navegação de `context-format.md`: o mapa é o único ponto de entrada, e
  documentos fora do mapa são ignorados nas sessões seguintes — por isso, confirme
  com o usuário o que entra e o que fica de fora.

Se nenhum documento de negócio nem ADR existia, não crie nada ainda neste passo —
os arquivos nascem no Modo 2, no momento em que o primeiro termo/decisão for
resolvido em conversa.

## 5. Transição para o Modo 2

Depois do setup (com ou sem documentos existentes), a sessão continua no Modo 2:
entrevista implacável + manutenção ativa do glossário/ADRs conforme a conversa avança.
