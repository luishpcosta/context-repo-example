---
name: context-repo-bootstrap
description: >
  Cria do zero um "context-repo": um repositório só de documentação que mapeia um
  produto multi-repo em dois eixos correlacionados — arquitetura técnica as-is
  (catalog-info.yaml estilo Backstage) e domínio de produto DDD (CONTEXT-MAP.md +
  CONTEXT.md por subdomínio) — mais a automação que responde perguntas de negócio
  direto do código via /graphify. Use sempre que alguém quiser "documentar a
  arquitetura de um produto com vários repositórios", "criar um repo de contexto",
  "mapear domínios e subdomínios de um sistema existente", "montar um catálogo
  Backstage a partir dos repos que eu já tenho clonados", ou disser que precisa de
  um lugar único que correlacione linguagem de negócio com onde o código
  correspondente mora. Também cobre estender um context-repo já existente com um
  componente ou subdomínio novo. Dispara mesmo sem as palavras "Backstage", "DDD"
  ou "context-repo" — se a intenção é sair de "vários repos soltos" para "um mapa
  navegável de produto→código", esta skill se aplica.
metadata:
  language: python
  tags: [ddd, backstage, catalog, graphify, bootstrap, scaffolding]
---

# context-repo-bootstrap

Monta o esqueleto completo de um context-repo e conduz o preenchimento até ele estar
funcionando de ponta a ponta. O trabalho manual que sobra é só o que exige
conhecimento de negócio (descrever componentes, nomear subdomínios, validar
glossário) — todo o encanamento vem pronto.

**Por que este padrão existe:** um produto espalhado em N repositórios não tem onde
guardar a resposta de "onde mora o código que implementa esse conceito de negócio?".
O context-repo é esse lugar: descreve os repositórios técnicos (`catalog-info.yaml`)
e a linguagem de domínio (`CONTEXT-MAP.md` + `CONTEXT.md`), e correlaciona os dois
via `Component.spec.subdomain` ↔ `Domain.spec.realizedBy`. Com essa correlação, uma
pergunta em linguagem de negócio vira um grafo de código sob demanda, escopado só
na fatia relevante — sem indexar o produto inteiro.

## Antes de começar

Confirme (e resolva) três coisas:

1. **Onde o context-repo vai viver.** Convenção que funciona bem: uma pasta irmã dos
   repositórios técnicos, ex.: `~/projetos/<produto>/context-repo/` com os repos do
   produto em `~/projetos/<produto>/`. Isso faz `repos_root: ..` funcionar direto.
2. **Quais repositórios entram.** Idealmente já clonados (o scaffold lê remote/ref/
   commit deles automaticamente). Se não estiverem, dá para adicionar depois.
3. **Skills disponíveis.** `blueprintfy` (modelagem de domínio) e `graphify`
   (grafo de código) — a Fase 2 e a Fase 5 dependem delas. Sem elas o resto ainda
   funciona, só perde a parte de domínio/consulta.

Pergunte ao usuário o nome do produto, o time dono (`owner`) e o slug do sistema
apenas se não der para inferir do contexto — não faça um questionário longo, essas
três respostas cabem em uma pergunta só.

## Fase 1 — Scaffold do esqueleto

Crie a estrutura e copie os scripts genéricos que acompanham esta skill. Eles são
config-driven: nenhum nome de produto hardcoded, tudo vem do `.context-repo.yml`.

```bash
mkdir -p <destino>/scripts <destino>/docs/dominio
cd <destino>
git init  # se ainda não for um repo

# scripts genéricos (copiar da skill, sem editar)
cp <skill>/scripts/catalog_config.py  scripts/
cp <skill>/scripts/build_catalog.py   scripts/
cp <skill>/scripts/query_catalog.py   scripts/
cp <skill>/scripts/scan_repos.py      scripts/
cp <skill>/scripts/install_hooks.py   scripts/
```

Depois materialize os templates de `assets/`, substituindo os placeholders
`{{PRODUCT_NAME}}`, `{{OWNER}}`, `{{SYSTEM_SLUG}}`, `{{REPOS_ROOT}}`,
`{{DOMAIN_DOCS}}`, `{{REPO_NAME}}` pelos valores reais:

| template | vira | papel |
|---|---|---|
| `assets/context-repo.yml.template` | `.context-repo.yml` | config lida por todos os scripts |
| `assets/catalog-info.seed.yaml` | `catalog-info.yaml` | semente com só o bloco `System` |
| `assets/gitignore.template` | `.gitignore` | ignora `.graphs/`, `.repo-cache/`, pycache de skills |
| `assets/CLAUDE.md.template` | `CLAUDE.md` | manual de operação do repo para agentes |

**O `.gitignore` tem que existir antes do primeiro commit.** `.graphs/` e
`.repo-cache/` são lixo descartável que aparece assim que alguém roda uma consulta;
se escaparem para o histórico, limpar depois é bem mais chato.

## Fase 2 — Popular os componentes técnicos (automático)

```bash
python3 scripts/scan_repos.py                # dry-run: mostra o que encontrou
python3 scripts/scan_repos.py --write        # grava os blocos Component
```

O script varre `repos_root`, acha toda pasta que é um repositório git, e preenche
`repository.remote` (normalizando SSH→HTTPS), `repository.local` (**relativo** à raiz
do context-repo, ex.: `../core`), `repository.ref` (tag mais próxima, ou branch) e
`repository.commit` (SHA exato do HEAD). Esses quatro campos são exatamente o que a
consulta da Fase 5 vai ler — é por isso que vale preenchê-los por script em vez de à
mão: `commit` digitado errado quebra o fallback remoto silenciosamente, e `local`
absoluto quebra o catálogo em qualquer outra máquina além de expor a estrutura de
diretórios de quem o gerou (catálogo tende a ser publicado). Os scripts resolvem o
relativo contra a raiz do repo na hora de usar, então funciona de qualquer diretório.

Num catálogo antigo, gravado com caminhos absolutos, `--update-refs` normaliza os
`local` existentes para relativo junto com ref/commit.

Sobram três campos que **só um humano sabe** e nascem como `TODO`:
`metadata.description`, `spec.scope` e `spec.subdomain`. Preencha description e scope
agora (uma linha cada, em linguagem de produto — o `scope` é lido pelo funil de foco);
`subdomain` fica para a Fase 4, quando os subdomínios existirem.

Mais tarde, quando os repositórios avançarem de versão:
`python3 scripts/scan_repos.py --update-refs` reatualiza `ref`/`commit` de todos.

## Fase 3 — Modelar o domínio (skill `blueprintfy`)

Invoque a skill `blueprintfy` em modo bootstrap. Ela conduz a entrevista e escreve
`CONTEXT-MAP.md` (índice) + um `CONTEXT.md` por subdomínio em `docs/dominio/<slug>/`.

Dois pontos que o `build_catalog.py` depende e vale reforçar durante a entrevista:

- **Todo `CONTEXT.md` precisa estar listado na seção `## Contextos` do
  `CONTEXT-MAP.md`**, no formato `- [Nome](./docs/dominio/<slug>/CONTEXT.md) — descrição`.
  O gerador só enxerga o que está nessa lista; um `CONTEXT.md` órfão é invisível.
- **O front matter de relação é estrutural.** `depende_de` e
  `compartilha_contrato_com` viram `spec.dependsOn`/`spec.sharesContractWith` no
  catálogo. `dominio_pai` (opcional) vira `spec.parent` — use quando o produto tiver
  hierarquia real Domínio→Subdomínio; para poucos subdomínios, o modelo plano é mais
  simples de manter e a hierarquia pode ser adicionada depois sem quebrar nada.

O glossário vive na seção `## Linguagem`, um termo por bloco:

```markdown
**Termo**:
Definição em uma ou mais linhas.
_Evitar_: sinônimo legado que não deve ser usado
```

## Fase 4 — Fechar a correlação e gerar o catálogo

Agora que os subdomínios existem, volte ao `catalog-info.yaml` e preencha
`spec.subdomain: [<slug>, ...]` em cada `Component`. É esse campo que faz o
`realizedBy` do lado do domínio existir — a correlação é declarada uma vez só, do
lado técnico, e o gerador deriva o outro sentido.

```bash
python3 scripts/build_catalog.py     # gera os blocos kind: Domain
python3 scripts/build_catalog.py --check   # confirma que ficou em dia
```

A partir daqui vale a regra permanente: **bloco `Domain` é gerado, nunca editado à
mão.** Quem quiser mudar glossário ou relação edita o `CONTEXT.md` e regenera.

Instale o hook que protege essa regra:

```bash
python3 scripts/install_hooks.py
```

## Fase 5 — Consulta em linguagem natural (opcional, alto valor)

Com catálogo e domínio prontos, `query_catalog.py ask` já resolve
subdomínio→componente→caminho e imprime os comandos do `/graphify`:

```bash
python3 scripts/query_catalog.py ask <slug> "<pergunta>" [componente] [--path <subpasta>]
```

Para que um usuário leigo não precise saber nem isso, instale a skill wrapper: copie
`assets/ask-skill.md.template` para `.claude/skills/ask/SKILL.md` no repo destino,
substituindo os placeholders. Ela recebe a pergunta em linguagem natural, escolhe o
subdomínio pelo significado, resolve o componente, decide sozinha se precisa escopar
com `--path`, executa o `/graphify` e traduz a resposta de volta para linguagem de
produto.

## Fase 6 — README e primeiro commit

Escreva um `README.md` curto explicando: o que o repo é, o formato adotado (Backstage
adaptado + quais campos custom), e a seção "Como atualizar" (o que é gerado vs.
editado à mão). O `CLAUDE.md` já cobre a operação por agente; o README é para humanos.

Antes do primeiro commit, rode a tríade completa:

```bash
python3 scripts/build_catalog.py --check
python3 -c "import yaml; list(yaml.safe_load_all(open('catalog-info.yaml')))"
python3 scripts/query_catalog.py list-domains
```

Commit sugerido (Conventional Commits): `feat(catalog): estrutura inicial do
context-repo de <produto>`.

## Estendendo um context-repo existente

**Componente técnico novo:** clone em `repos_root`, rode
`scan_repos.py --write`, preencha os `TODO` e o `spec.subdomain`, rode
`build_catalog.py`, valide.

**Subdomínio novo:** crie `docs/dominio/<slug>/CONTEXT.md` (via `blueprintfy`),
referencie em `CONTEXT-MAP.md`, adicione `spec.subdomain: [<slug>]` no(s) componente(s)
que o realizam, rode `build_catalog.py`, valide.

## Armadilhas que custaram tempo na primeira implementação deste padrão

- **Versionar a instalação de uma skill de terceiro por engano.** A saída dela
  (markdown) é produto do trabalho e é versionada; a instalação não. Decida isso antes
  do primeiro commit — no repo original isso foi commitado e revertido um minuto depois.
- **Editar um bloco `Domain` à mão para "consertar" um `--check` que falhou.** Isso
  inverte a fonte da verdade e a próxima regeneração descarta a edição. Se o `--check`
  falha, rode sem `--check`.
- **Escopar com `--path` num componente grande gera arestas "soltas"** no grafo (código
  que referencia símbolos fora da pasta escaneada). É o preço esperado de escopar
  deliberadamente, não corrupção — documente em vez de esconder. Se a resposta depender
  desses símbolos, rode sem `--path`.
- **Esquecer de rodar `build_catalog.py --check` antes do commit** deixa o YAML
  dessincronizado do markdown sem nenhum aviso. É exatamente o que o hook resolve.

## Custo

Todo o scaffold, a navegação de catálogo e a resolução subdomínio→componente são
script Python puro — zero tokens, independente do tamanho do produto ou da
profundidade da hierarquia de domínios. Custo de LLM só aparece na Fase 3 (entrevista
de domínio) e na Fase 5, e nesta última só para arquivos que **não** são código:
código é extraído por AST, determinístico e gratuito. Corpus com muita documentação
por perto (Javadoc, specs, YAML de config) é o que pesa — nesses casos vale
configurar `GEMINI_API_KEY`, que o `graphify` usa para a extração semântica em vez de
despachar um subagente completo por lote.
