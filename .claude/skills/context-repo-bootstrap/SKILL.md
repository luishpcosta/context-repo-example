---
name: context-repo-bootstrap
description: >
  Cria do zero um "context-repo": um repositório só de documentação que mapeia um
  produto multi-repo em dois eixos correlacionados — o domínio de produto (DDD:
  CONTEXT-MAP.md + CONTEXT.md por contexto) e os repositórios de código que o
  realizam (um markdown por componente, com remote, revisão e caminho) — mais a
  automação que responde perguntas de negócio direto do código-fonte. Use sempre que
  alguém quiser "documentar a arquitetura de um produto com vários repositórios",
  "criar um repo de contexto", "mapear domínios e subdomínios de um sistema
  existente", "montar um catálogo a partir dos repos que eu já tenho clonados", ou
  disser que precisa de um lugar único que correlacione linguagem de negócio com
  onde o código correspondente mora. Também cobre estender um context-repo já
  existente com um componente ou contexto novo. Dispara mesmo sem as palavras "DDD"
  ou "context-repo" — se a intenção é sair de "vários repos soltos" para "um mapa
  navegável de produto→código", esta skill se aplica.
metadata:
  language: python
  tags: [ddd, catalog, graphify, bootstrap, scaffolding, context-repo]
---

# context-repo-bootstrap

Monta o esqueleto completo de um context-repo e conduz o preenchimento até ele estar
funcionando de ponta a ponta. O trabalho manual que sobra é só o que exige conhecimento
de negócio (descrever componentes, nomear contextos, validar glossário) — todo o
encanamento vem pronto.

**Por que este padrão existe:** um produto espalhado em N repositórios não tem onde
guardar a resposta de "onde mora o código que implementa esse conceito de negócio?". O
context-repo é esse lugar: descreve a linguagem de domínio (`CONTEXT-MAP.md` +
`CONTEXT.md`), descreve os repositórios de código (`docs/componentes/*.md`), e
correlaciona os dois com `realizado_por`. Com essa correlação, uma pergunta em
linguagem de negócio vira um grafo de código sob demanda, escopado só na fatia
relevante — sem indexar o produto inteiro.

**Tudo é front matter de markdown.** Não existe arquivo gerado, nem arquivo de config
separado. Isso é deliberado: um artefato derivado e versionado cria uma segunda verdade
para manter em dia, e um hook que existe só para detectar quando ela divergiu. Sem ele,
drift é impossível por construção em vez de detectável. Se você sentir vontade de
"materializar um índice consolidado", não faça — uma view em memória, montada na hora e
descartada, é o padrão certo (é o que o `graph_query.py` faz).

## Antes de começar

Confirme (e resolva) três coisas:

1. **Onde o context-repo vai viver.** Convenção que funciona bem: uma pasta irmã dos
   repositórios técnicos, ex.: `~/projetos/<produto>/context-repo/` com os repos do
   produto em `~/projetos/<produto>/`. Isso faz `repos_root: ..` funcionar direto.
2. **Quais repositórios entram.** Idealmente já clonados (o scaffold lê remote/ref/
   commit deles automaticamente). Se não estiverem, dá para adicionar depois.
3. **Skills disponíveis.** `blueprintfy` é **obrigatória**, não opcional: os scripts
   importam dela o parser de front matter e o resolvedor de código (`graph_query.py`,
   `repo_cache.py`). `graphify` e `ask` são para a Fase 5.

Pergunte ao usuário o nome do produto, o time dono (`owner`) e o slug do sistema apenas
se não der para inferir do contexto — não faça um questionário longo, essas três
respostas cabem em uma pergunta só.

## Fase 1 — Scaffold do esqueleto

```bash
mkdir -p <destino>/scripts <destino>/docs/dominio <destino>/docs/componentes
cd <destino>
git init  # se ainda não for um repo

# scripts genéricos (copiar da skill, sem editar)
cp <skill>/scripts/context_config.py  scripts/
cp <skill>/scripts/scan_repos.py      scripts/
cp <skill>/scripts/validate.py        scripts/
cp <skill>/scripts/install_hooks.py   scripts/
```

Depois materialize os templates de `assets/`, substituindo `{{PRODUCT_NAME}}`,
`{{OWNER}}`, `{{SYSTEM_SLUG}}`, `{{REPOS_ROOT}}`, `{{DOMAIN_DOCS}}` e
`{{COMPONENT_DOCS}}` pelos valores reais:

| template | vira | papel |
|---|---|---|
| `assets/CONTEXT-MAP.md.template` | `CONTEXT-MAP.md` | marcador, config e índice |
| `assets/gitignore.template` | `.gitignore` | ignora `.graphs/`, `.repo-cache/`, skills instaladas |
| `assets/CLAUDE.md.template` | `CLAUDE.md` | manual de operação do repo para agentes |

**O `CONTEXT-MAP.md` tem que existir antes de qualquer script rodar** — ele é o
marcador do repositório (é assim que `context_config.repo_root()` acha a raiz) e a
config. E **o `.gitignore` tem que existir antes do primeiro commit**: `.graphs/` e
`.repo-cache/` aparecem assim que alguém roda uma consulta, e limpá-los do histórico
depois é bem mais chato.

## Fase 2 — Popular os componentes técnicos (automático)

```bash
python3 scripts/scan_repos.py                # dry-run: mostra o que encontrou
python3 scripts/scan_repos.py --write        # cria docs/componentes/<nome>.md
```

O script varre `repos_root`, acha toda pasta que é um repositório git, e preenche
`remote` (normalizando SSH→HTTPS), `local` (**relativo** à raiz do context-repo, com o
case do diretório preservado), `ref` (tag mais próxima, ou branch), `commit` e
`ultimo_visto`.

Vale preencher isso por script em vez de à mão porque `commit` digitado errado quebra a
resolução de código em silêncio, e `local` absoluto quebra o repo em qualquer outra
máquina além de expor a estrutura de diretórios de quem o gerou.

Sobram dois campos que **só um humano sabe** e nascem como `TODO`: o `titulo` do front
matter e o corpo do documento (o escopo do componente, em uma frase, em linguagem de
produto). Preencha agora, e referencie cada arquivo novo na seção "Componentes
técnicos" do `CONTEXT-MAP.md` — sem isso, o documento é órfão e o `validate.py` falha.

### Pin e marca d'água

```yaml
commit: <sha>        # PIN: só um humano move, com --pin
ultimo_visto: <sha>  # MARCA D'ÁGUA: --update-refs atualiza sozinho
```

O pin descreve o código que a documentação afirma descrever, e é o que um PB/PRD/ADR
cita. `--update-refs` nunca o toca. `commit != ultimo_visto` não é erro a consertar: é
o sinal de que alguém precisa conferir a documentação contra o código novo. Promover o
pin (`--pin`) é o ato deliberado que registra "conferi".

## Fase 3 — Modelar o domínio (skill `blueprintfy`)

Invoque a `blueprintfy` em modo bootstrap. Ela conduz a entrevista e escreve o
`CONTEXT-MAP.md` (seção `## Contextos`) + um `CONTEXT.md` por contexto em
`docs/dominio/<slug>/`.

Dois pontos que vale reforçar durante a entrevista:

- **Todo `CONTEXT.md` precisa estar referenciado no `CONTEXT-MAP.md`.** O mapa é o
  único ponto de entrada: um documento que ele não alcança é invisível para o grafo e
  para as consultas, e o `validate.py` trata isso como erro.
- **Front matter de relação é estrutural, não decorativo.** `depende_de`,
  `compartilha_contrato_com` e `dominio_pai` são as arestas do grafo. Hierarquia de
  contextos é por `dominio_pai`, com a profundidade que a modelagem DDD pedir.

## Fase 4 — Fechar a correlação

Agora que contextos e componentes existem, declare o elo no front matter de cada
`CONTEXT.md` folha:

```yaml
realizado_por:
  - componente: <nome>
    caminho: <subpasta>   # opcional
```

Três regras:

- **A direção é domínio → código, e só ela.** Não declare o inverso no doc do
  componente: seriam duas verdades para sincronizar.
- **Ancore na folha.** Perguntar por um contexto pai alcança o código dos filhos
  sozinho, descendo por `dominio_pai`.
- **`caminho` é opcional e não é obrigação.** Omitido, vale o repositório inteiro.
  Declare-o quando o componente for grande demais para ser lido inteiro com qualidade
  (na prática, centenas de MB). Um caminho errado é pior que caminho nenhum — e um
  caminho declarado é o que substitui a heurística de adivinhar subpasta.

Instale o hook e valide:

```bash
python3 scripts/install_hooks.py
python3 scripts/validate.py
```

O `validate.py` confere integridade referencial: link quebrado no mapa, documento
órfão, `realizado_por` citando componente inexistente, relação apontando para contexto
que não existe, e cada `caminho` contra o código real. Ele **nunca escreve** — falha
com a instrução do que rodar. Não o transforme em corretor automático: um hook que
altera o conteúdo do commit produz commits diferentes em máquinas diferentes a partir
do mesmo `git commit`.

## Fase 5 — Consulta em linguagem natural

Com o modelo fechado, `graph_query.py` já responde que código realiza um contexto:

```bash
python3 <pasta-de-skills>/blueprintfy/scripts/graph_query.py realiza "<Contexto>"
```

Para que quem pergunta não precise saber nem isso, instale a skill **`ask`** do
catálogo (`lup-skills add ask`, ou o instalador que acompanha a própria `ask`). Ela
recebe a pergunta em linguagem natural, escolhe o contexto pelo significado, resolve
componente e caminho, baixa o código se preciso, roda o `/graphify` e traduz a resposta
de volta para linguagem de produto — sem nunca escrever nada.

Não estampe uma cópia da `ask` dentro do repo destino: instale-a. Uma cópia por
repositório é uma cópia por repositório para manter em dia.

## Fase 6 — README e primeiro commit

Escreva um `README.md` curto para humanos: o que o repo é, o formato (front matter como
fonte única), a correlação, e a seção "Como atualizar". O `CLAUDE.md` já cobre a
operação por agente.

Antes do primeiro commit:

```bash
python3 scripts/validate.py
```

Commit sugerido (Conventional Commits): `feat(contexto): estrutura inicial do
context-repo de <produto>`.

## Estendendo um context-repo existente

**Componente novo:** clone em `repos_root`, `scan_repos.py --write`, preencha `titulo`
e corpo, referencie na seção "Componentes técnicos" do mapa, declare `realizado_por` no
`CONTEXT.md` do contexto que ele realiza, valide.

**Contexto novo:** crie `docs/dominio/<slug>/CONTEXT.md` (via `blueprintfy`),
referencie no mapa, declare `realizado_por` apontando para o(s) componente(s) que o
realizam, valide.

## Armadilhas que custaram tempo

- **Versionar a instalação de uma skill por engano.** A saída dela (markdown) é produto
  do trabalho e é versionada; a instalação, não. Decida antes do primeiro commit.
- **Recriar um artefato gerado.** Este padrão já teve um catálogo YAML derivado, com um
  hook que existia só para detectar divergência. Ele foi removido de propósito; não o
  reintroduza com outro nome.
- **Declarar a correlação nos dois sentidos.** Tentador para "facilitar a consulta", e
  é como o de-para acaba divergindo. Uma direção só, sempre.
- **Confundir o dono do pin com o dono da marca d'água.** Atualizar o `commit` só
  porque o upstream andou apaga a âncora de todo documento que o citou.
- **Documento fora do mapa.** É o modo de falha mais silencioso do padrão: nada quebra,
  o documento só deixa de existir para as ferramentas. Por isso é erro no `validate.py`,
  não aviso.

## Custo

Todo o scaffold, a navegação do modelo e a resolução contexto→componente→caminho são
script Python puro, stdlib-only — zero tokens, independente do tamanho do produto ou da
profundidade da hierarquia. Custo de LLM só aparece na Fase 3 (entrevista de domínio) e
na Fase 5, e nesta última só para arquivos que **não** são código: código é extraído por
AST, determinístico e gratuito. Corpus com muita documentação por perto (Javadoc,
specs, YAML de config) é o que pesa — nesses casos vale configurar `GEMINI_API_KEY`,
que o `graphify` usa para a extração semântica em vez de despachar um subagente
completo por lote.
