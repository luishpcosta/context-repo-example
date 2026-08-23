---
name: blueprintfy
description: "Constrói e afia o modelo de domínio de um projeto: entrevista implacável para estressar um plano/design, glossário de linguagem onipresente (CONTEXT.md/CONTEXT-MAP.md) e ADRs de decisões arquiteturais, tudo em um fluxo contínuo. Use sempre que o usuário quiser definir/discutir terminologia de domínio, apertar um plano antes de construir, mapear bounded contexts, ou disser algo como 'grilar isso comigo', 'vamos estressar essa decisão', 'preciso alinhar a linguagem do domínio', 'isso é uma Order ou uma Invoice mesmo?'. Também cobre o setup inicial de repositório sem CONTEXT-MAP.md: rode o checklist de bootstrap sempre que o usuário pedir para 'começar a modelagem de domínio', 'criar o glossário do zero' ou 'mapear os contextos do sistema' — pergunte primeiro se já existem documentos de negócio e ADRs no repo. Acione mesmo sem o usuário citar 'DDD', 'ADR' ou 'CONTEXT.md' — se a intenção é sair de um entendimento vago para um modelo de domínio preciso e registrado, esta skill se aplica."
metadata:
  language: agnostic
  tags: [domain-modeling, ddd, glossary, adr, architecture, interview, bounded-context]
---

# Blueprintfy

Constrói e afia o modelo de domínio de um projeto **enquanto** se discute o design —
não é uma skill de leitura passiva de glossário, é a disciplina ativa de questionar
termos, inventar cenários de borda e registrar linguagem/decisões no instante em que
elas se cristalizam. Combina três coisas que sempre andaram juntas: entrevistar sem
descanso (`grilling`), manter o glossário e as ADRs de domínio em dia
(`domain-modeling`), e um modo de bootstrap para quando o repositório ainda não tem
nada disso.

Ler `CONTEXT.md` só para consultar um termo não é isso — qualquer skill pode fazer
isso em uma linha. Esta skill entra em cena quando o modelo está mudando, não quando
está só sendo consumido.

## Como decidir o modo

- **Repositório sem `CONTEXT-MAP.md` na raiz e sem sessão em andamento** → comece
  pelo **Modo 1 (Setup inicial)** — é sempre a **primeira configuração** da skill no
  repo; não assuma nenhum uso anterior. Só existem dois cenários, e o roteiro cobre
  ambos: repo **já documentado** (docs de negócio, glossários, ADRs — em qualquer
  formato, nome ou pasta) e repo **sem documentação**. No primeiro, o Modo 1
  questiona o usuário para criar o `CONTEXT-MAP.md` na raiz a partir do que já
  existe.
- **Já existe `CONTEXT-MAP.md` na raiz, ou o usuário quer discutir/estressar um
  plano agora** → vá direto para o **Modo 2 (Sessão contínua)**.
- Nunca se force a rodar o Modo 1 se o usuário só quer bater um papo rápido sobre um
  termo — o setup completo é para quando o objetivo é estabelecer a base do modelo.

## Modo 1 — Setup inicial (bootstrap)

Antes de propor qualquer estrutura, rode o checklist com o usuário — não assuma nada
sobre o que já existe:

1. **"Já existem documentos de negócio no repositório?"** (PRDs, briefings, specs,
   RFCs, tickets longos). Se sim, peça o caminho.
2. **"Já existem ADRs registradas?"** Se sim, peça o caminho (a convenção deste
   catálogo é `adr/ADR-<id>-titulo.md` — ver `references/adr-template.md`; mas
   respeite a convenção que o repo já usa se for outra).
3. **"O sistema tem mais de um bounded context/domínio?"** Não assuma a partir da
   estrutura de pastas sozinho — proponha sua leitura ("percebi múltiplos serviços em
   `src/ordering` e `src/billing`, parece que são contextos separados — confere?") e
   confirme com o usuário. A estrutura é **sempre** `CONTEXT-MAP.md` na raiz — mesmo
   com um único contexto o mapa existe (com uma entrada só); o que se decide aqui com
   o usuário é **quantos contextos entram no mapa e onde o `CONTEXT.md` de cada um
   vive**.

Depois de coletar essas três respostas, siga o roteiro completo em
`references/setup-checklist.md` — ele detalha como escanear os documentos existentes,
propor um rascunho de glossário termo a termo (nunca grave direto sem validar com o
usuário) e como decidir quantos contextos entram no `CONTEXT-MAP.md` e onde o
`CONTEXT.md` de cada um vive. Se não houver nada documentado ainda, pule o
escaneamento e vá direto para o Modo 2 — o glossário nasce organicamente durante a
conversa.

Crie os arquivos de forma preguiçosa: só grave o `CONTEXT-MAP.md` (na raiz) e o
primeiro `CONTEXT.md` de contexto quando o primeiro termo estiver de fato validado,
só crie `docs/adr/` (ou a pasta de ADR do repo) quando a primeira decisão realmente
merecer uma. Os dois nascem juntos: nunca grave um `CONTEXT.md` sem que o
`CONTEXT-MAP.md` da raiz o referencie.

## Modo 2 — Sessão contínua (entrevista + modelagem ativa)

Leia o `CONTEXT-MAP.md` da raiz antes de explorar qualquer pasta de documentação —
ele é o índice de navegação do repo (contextos, docs as-is, docs to-be) e delimita o
que entra na sessão (ver "Estrutura de arquivos" e as regras de navegação em
`references/context-format.md`). Se não existir `CONTEXT-MAP.md` na raiz, não siga
sem mapa: rode o Modo 1 (primeira configuração) antes de continuar — a documentação
que já existir no repo entra como insumo do setup, não como estrutura pronta.

### Entreviste sem descanso

Faça perguntas sobre cada aspecto do plano/design até chegar a um entendimento
compartilhado. Percorra cada ramo da árvore de decisão, resolvendo as dependências
entre decisões uma de cada vez. Para cada pergunta, ofereça sua resposta recomendada —
isso dá ao usuário algo concreto para confirmar ou corrigir, em vez de uma folha em
branco.

Pergunte **uma coisa de cada vez**, esperando o retorno antes de continuar. Várias
perguntas empilhadas de uma vez só deixam o usuário perdido sobre o que responder
primeiro.

Se uma pergunta pode ser respondida explorando o código em vez de perguntar ao
usuário, explore o código.

### Desafie contra o glossário existente

Quando o usuário usar um termo que conflita com o `CONTEXT.md` atual, aponte na hora:
"Seu glossário define 'cancelamento' como X, mas parece que você quer dizer Y — qual
dos dois é?"

### Afie linguagem vaga

Quando o termo usado for genérico ou sobrecarregado, proponha um termo canônico
preciso: "Você está dizendo 'conta' — quer dizer o Customer ou o User? São coisas
diferentes."

### Discuta cenários concretos

Quando uma relação de domínio estiver em discussão, estresse-a com cenários
específicos. Invente cenários que testem casos de borda e forcem o usuário a ser
preciso sobre onde termina um conceito e começa outro.

### Cruze com o código

Quando o usuário descrever como algo funciona, confira se o código concorda. Se
encontrar contradição, traga à tona: "Seu código cancela o Order inteiro, mas você
acabou de dizer que cancelamento parcial é possível — qual dos dois está certo?"

### Consulte o grafo antes de reafirmar uma garantia

Quando o plano tocar um contexto que já tem ADRs, não releia todas à mão para achar
tensões: o mapa + o front matter de relação dos docs formam um grafo, e
`scripts/graph_query.py` (stdlib-only) faz a travessia por você, devolvendo markdown
já-digerido. Aponte `--map` para o `CONTEXT-MAP.md` da raiz do projeto:

```
python3 <skill>/scripts/graph_query.py --map ./CONTEXT-MAP.md vigentes contexto:<Nome>
python3 <skill>/scripts/graph_query.py --map ./CONTEXT-MAP.md impacto contexto:<Nome>
python3 <skill>/scripts/graph_query.py --map ./CONTEXT-MAP.md valida-aresta contexto:A contexto:B
```

Use `vigentes` **antes de aceitar uma garantia que o usuário reafirma**: se ela vier de
uma ADR que já foi superada por outra (a ferramenta deriva isso do `supera:` da ADR
nova, sem editar a antiga), aponte a tensão em vez de implementar o plano como descrito
— é o mesmo tipo de contradição que "Cruze com o código" levanta, só que ADR↔ADR. Use
`valida-aresta` para checar se uma integração proposta fura o bounded context.

**Repo brownfield (docs sem front matter)**: se os `CONTEXT.md`/ADRs ainda não têm
front matter de relação, o grafo nasce vazio e a ferramenta **avisa** — não leia esse
vazio como "sem tensões". Faça a travessia à mão lendo as ADRs, e ofereça o backfill do
front matter (ver Modo 1 / `references/setup-checklist.md`) para as próximas consultas
funcionarem. **Sem Python** vale o mesmo fallback manual — o script só acelera; a skill
continua `agnostic`. Detalhes em `references/context-format.md` ("Grafo de dependências").

### Atualize `CONTEXT.md` inline

Quando um termo for resolvido, atualize o `CONTEXT.md` do contexto certo (localize-o
pelo `CONTEXT-MAP.md` da raiz) ali mesmo, na hora — não acumule para depois. Use o
formato em `references/context-format.md`.

O conteúdo do `CONTEXT.md` pertence ao repositório (visão geral de negócio, BPM,
processos) — a skill não impõe formato ao arquivo; ela cria e mantém apenas a seção
`## Linguagem` dentro dele. Essa seção deve ser totalmente livre de detalhes de
implementação: não a trate como spec, rascunho ou repositório de decisões técnicas —
é glossário e nada mais.

### Ofereça ADR com moderação

Só ofereça criar uma ADR quando as três condições forem verdadeiras ao mesmo tempo:

1. **Difícil de reverter** — o custo de mudar de ideia depois é relevante.
2. **Surpreendente sem contexto** — um leitor futuro vai se perguntar "por que
   fizeram assim?".
3. **Resultado de um trade-off real** — havia alternativas genuínas e uma foi
   escolhida por razões específicas.

Se faltar qualquer uma das três, não ofereça ADR — o rascunho de decisão fica só no
histórico da conversa. Use o template e o gerador de ID em
`references/adr-template.md`. Preencha o **front matter de relação** da ADR
(`contextos`/`afeta`/`supera`/`depende_de`, com os nomes exatos das entradas do
`CONTEXT-MAP.md`) — é o que faz a ADR entrar no grafo de dependências. Se a decisão
substitui uma anterior, declare `supera:` na ADR **nova**; nunca edite a antiga à mão.

Assim que uma ADR for criada, se a skill `make-diagram` estiver disponível no
ambiente, acione-a para gerar o diagrama da decisão (relação entre contextos,
integração, fronteira) como imagem ao lado da ADR (`adr/ADR-<id>-diagrama.png`),
referenciando-o na seção **Decisão**. Sem `make-diagram`, use Mermaid inline como
fallback. A ADR criada passa pelo gate de criação de documento (ver "Mapa sempre em
dia"): confirme que ela é alcançável a partir do `CONTEXT-MAP.md` e valide o
registro. Se a ADR declarou `supera:`, rode `scripts/graph_query.py vigentes
contexto:<Nome>` (ou a travessia manual no fallback) e reporte ao usuário qual ADR
passou a superada.

## Estrutura de arquivos

A estrutura é **sempre `CONTEXT-MAP.md` na raiz** — mesmo em repositório de contexto
único, o mapa existe (com uma entrada só) e aponta onde o `CONTEXT.md` daquele
contexto vive. **Nunca deixe um `CONTEXT.md` sem mapa como estrutura final.**
Glossários que já existirem no repo (qualquer nome ou local) são documentação
existente como outra qualquer: entram no inventário do Modo 1 e só viram o
`CONTEXT.md` de um contexto com a confirmação do usuário.

Contexto único:

```
/
├── CONTEXT-MAP.md                     ← na raiz, sempre
├── docs/dominio/loja/CONTEXT.md       ← onde o usuário preferir; o mapa aponta
├── adr/
│   ├── ADR-20260615-0930-a1f2-nome-da-decisao.md
│   └── ADR-20260620-1542-3f0a-outra-decisao.md
└── src/
```

O `CONTEXT-MAP.md` é o **índice de navegação do repositório**: antes de explorar
qualquer pasta, leia o mapa e siga apenas os caminhos que ele referencia. O mapa diz onde vive cada contexto, onde estão
os documentos de negócio já produtivos (as-is) e onde está o planejamento to-be
(PRDs/ADRs/SPECs de Spec-Driven Development). **Documentos que existem na árvore mas
não estão referenciados no mapa são ignorados** — não os escaneie nem os trate como
fonte do modelo; se um deles parecer relevante, pergunte ao usuário se deve entrar no
mapa em vez de usá-lo por conta própria.

A forma mais simples de multi-contexto aponta para `CONTEXT.md` dentro do código:

```
/
├── CONTEXT-MAP.md
├── adr/                               ← decisões de todo o sistema
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── adr/                       ← decisões específicas do contexto
│   └── billing/
│       ├── CONTEXT.md
│       └── adr/
```

Mas o mapa não é restrito a `src/` — os contextos e documentos podem viver em
qualquer lugar que o mapa apontar. Um cenário frequente combina domínios de negócio
documentados (as-is) com planejamento to-be em `docs/`:

```
/
├── CONTEXT-MAP.md                     ← na raiz, sempre
├── docs/refinamento/                  ← to-be (SDD): o que está sendo planejado
│   ├── ordering/
│   │   └── {funcionalidade}/
│   │       ├── PRODUCT_BRIEF.md
│   │       ├── NNN-slug-{funcionalidade}-PRD.md
│   │       ├── NNN-slug-{funcionalidade}-ADR.md
│   │       └── {especificacao}/
│   │           └── NNN-slug-{atividade-componente}-SPEC.md
│   └── payment/
│       └── ...mesma estrutura...
├── docs/dominio/                      ← as-is: negócio já produtivo
│   └── {bounded-context}/
│       ├── CONTEXT.md                 ← visão geral de negócio (com BPM)
│       └── {area-do-dominio}/
│           ├── {dominio-1}.md         ← detalhamento e regras do domínio
│           └── {dominio-2}.md
```

Os nomes das pastas acima são ilustrativos — cada repo usa os seus; é o
`CONTEXT-MAP.md` que registra os caminhos reais (formato e regras de navegação em
`references/context-format.md`).

Quando existirem múltiplos contextos, infira a qual o assunto atual pertence — e, ao
estressar um plano, considere tanto as regras as-is do domínio quanto os documentos
to-be referenciados no mapa. Se não estiver claro a que contexto o assunto pertence,
pergunte — não adivinhe uma decisão que muda onde tudo é gravado.

## Mapa sempre em dia (gate de criação de documento)

Se o mapa é o único ponto de entrada, um documento fora do mapa é invisível — por
isso a criação de qualquer documento na estrutura mapeada (`CONTEXT.md` de contexto,
doc de domínio, PRODUCT_BRIEF, PRD, ADR, SPEC) carrega um gate obrigatório para quem
criou o arquivo:

1. **Verifique o alcance**: o novo arquivo é alcançável a partir do `CONTEXT-MAP.md`?
   (o próprio arquivo, ou a pasta que o contém, está referenciado no mapa).
2. **Registre se não for**: adicione a referência na seção certa do mapa (Contextos /
   Documentos de negócio as-is / Planejamento to-be). Se a seção for ambígua,
   pergunte ao usuário.
3. **Valide**: releia o `CONTEXT-MAP.md`, confirme que o caminho referenciado existe
   no disco (sem link quebrado) e que o novo arquivo está alcançável, e reporte o
   resultado da validação ao usuário.

Um documento só está entregue quando passa por esse gate — criar o arquivo sem
registrá-lo no mapa é entrega incompleta. O detalhamento está em
`references/context-format.md` ("Gate de criação de documento").

## Arquivos de referência

- `references/context-format.md` — formato da seção de linguagem do `CONTEXT.md` (o
  restante do arquivo é do repo) e do `CONTEXT-MAP.md`, regras de linguagem (ser
  opinativo, definições curtas, o que entra e o que não entra) e regras de navegação
  (mapa como ponto de entrada, docs as-is vs. to-be, ignorar o que não está no mapa).
- `references/adr-template.md` — template de ADR e como gerar o ID (mesma convenção de
  `prd-to-adr`/`issue-to-adr` deste catálogo), e o critério de quando vale a pena
  registrar uma.
- `references/setup-checklist.md` — roteiro completo do Modo 1 (repo já documentado
  ou sem documentação): como escanear docs de negócio/ADRs existentes, propor
  rascunho de glossário e montar o `CONTEXT-MAP.md` da raiz (quantos contextos, onde
  cada `CONTEXT.md` vive).
- `scripts/graph_query.py` — grafo de dependências derivado do front matter (view
  descartável, stdlib-only): consultas `vigentes`/`impacto`/`valida-aresta`/`ciclos`
  com saída já-digerida. Opcional; sem Python, a travessia é feita à mão.
