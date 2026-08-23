# context-repo

Repositório documental da POC Home Assistant. Não contém código executável — descreve,
em dois eixos que se correlacionam, os 7 repositórios do produto clonados em `../`:

- **domínio de produto (DDD)** — quais capacidades existem e com que linguagem se fala
  delas;
- **arquitetura técnica as-is** — quais repositórios de código realizam cada capacidade,
  e em que ponto do código.

O elo entre os dois é o que dá valor ao repositório: a partir de uma pergunta em
linguagem de negócio, chegar ao código que a responde.

## O formato: front matter, e só

Não existe arquivo gerado, nem arquivo de configuração separado. **Todo dado
estrutural mora no front matter de um markdown**, e o markdown continua legível sem
nenhuma ferramenta.

```
CONTEXT-MAP.md              ← ponto de entrada, marcador do repo e config
docs/dominio/<slug>/CONTEXT.md   ← um contexto de domínio: glossário e relações
docs/componentes/<nome>.md       ← um repositório de código: onde está, em que revisão
```

O `CONTEXT-MAP.md` é o único ponto de entrada: **o que ele não alcança não existe**
para as ferramentas. Um documento fora do mapa é invisível, e é por isso que
`scripts/validate.py` trata órfão como erro.

A configuração do repo é o front matter do próprio mapa:

```yaml
product: POC Home Assistant
owner: home-assistant
system: home-assistant
repos_root: ..
domain_docs: docs/dominio
component_docs: docs/componentes
```

### Por que não um catálogo gerado

Este repositório já teve um `catalog-info.yaml` no formato Backstage, gerado a partir
dos mesmos markdowns por um build step, com um hook de pre-commit que existia só para
detectar quando o gerado divergia da fonte. O arquivo foi removido: um artefato
derivado e versionado só cria uma segunda verdade para manter em dia. O que se perde é
compatibilidade com um Backstage real; o que se ganha é que drift entre fonte e
catálogo passa a ser impossível por construção, em vez de detectável.

## A correlação domínio → código

Declarada uma vez só, no front matter do `CONTEXT.md`, na direção da consulta:

```yaml
realizado_por:
  - componente: core
    caminho: homeassistant/components/automation
  - componente: core
    caminho: homeassistant/components/script
```

`caminho` é opcional — omitido, vale o repositório inteiro. Ele existe para que o
escopo de leitura do código seja **dado**, não heurística: sem ele, uma pergunta sobre
automação obrigaria a varrer os 619MB do `core`. Vale declará-lo quando o componente é
grande demais para ser lido inteiro com qualidade; nos outros (o maior depois do `core`
tem 222MB) ele só adiciona uma chance de apontar para o lugar errado.

| Contexto | Componentes |
|---|---|
| [Automation & State Engine](./docs/dominio/automation-state-engine/CONTEXT.md) | `core` (5 caminhos) |
| [Integration Platform](./docs/dominio/integration-platform/CONTEXT.md) | `core` (3 caminhos) |
| [Add-on & System Management](./docs/dominio/addon-system-management/CONTEXT.md) | `supervisor`, `operating-system` |
| [Client Experience](./docs/dominio/client-experience/CONTEXT.md) | `frontend`, `android`, `ios` |
| [Build & Distribution](./docs/dominio/build-distribution/CONTEXT.md) | `docker` |

Os 5 contextos **não mapeiam 1:1** com os 7 repositórios: `core` realiza dois contextos,
e três repositórios realizam juntos o `Client Experience`.

## Duas revisões por componente, com donos diferentes

Cada doc em `docs/componentes/` carrega:

```yaml
commit: 3fb456fa1fe4abbe6b89367b98f282043e9b02dd        # o pin
ultimo_visto: 3fb456fa1fe4abbe6b89367b98f282043e9b02dd  # a marca d'água
```

- **`commit` é o pin.** Descreve o código que esta documentação afirma descrever. Só
  um humano o move, com `--pin`. É o que um PB/PRD/ADR cita quando diz "conforme o
  commit X" — e é por isso que ele não pode ser um alvo móvel.
- **`ultimo_visto` é a marca d'água.** `--update-refs` a atualiza sozinho. É o "como
  está hoje", que uma pergunta sobre o comportamento atual do produto quer.

`commit != ultimo_visto` é, literalmente, o sinal de que o componente está descasado: o
código andou e a documentação ainda não foi conferida contra ele.

## Scripts

Stdlib-only, sem dependências externas. Nada de nome de produto hardcoded: tudo vem do
front matter do `CONTEXT-MAP.md`.

- **`scripts/validate.py`** — integridade referencial. Roda no pre-commit e nunca
  escreve: falha com a instrução do que rodar.
  ```bash
  python3 scripts/validate.py             # valida tudo
  python3 scripts/validate.py --offline    # não baixa nada; o que faltar vira aviso
  ```
  Pega link quebrado no mapa, documento órfão, `realizado_por` citando componente
  inexistente, relação apontando para contexto que não existe, e `caminho` que o
  upstream moveu — este último conferido contra o código real.

- **`scripts/scan_repos.py`** — descobre os repositórios clonados em `../` e mantém os
  docs de componente em dia.
  ```bash
  python3 scripts/scan_repos.py                # dry-run: o que encontrou e o que divergiu
  python3 scripts/scan_repos.py --write        # cria os docs dos componentes novos
  python3 scripts/scan_repos.py --update-refs  # atualiza ultimo_visto (nunca o pin)
  python3 scripts/scan_repos.py --pin          # promove o pin para o ultimo_visto
  ```

- **`scripts/install_hooks.py`** — instala o pre-commit que roda o `validate.py`.
  ```bash
  python3 scripts/install_hooks.py
  ```

- **`scripts/context_config.py`** — módulo compartilhado: acha a raiz do repo, lê a
  config do mapa e itera contextos/componentes. Não reimplementa o parser de front
  matter: importa o da skill `blueprintfy`, que é a fonte única do formato.

## Como atualizar

Quando um dos repositórios em `../` mudar de tag/commit:

```bash
python3 scripts/scan_repos.py                # o que divergiu?
python3 scripts/scan_repos.py --update-refs  # atualiza a marca d'água
```

O pin fica onde está de propósito. Depois de conferir que a documentação ainda descreve
o código novo:

```bash
python3 scripts/scan_repos.py --pin
```

## Consultar o código a partir de uma pergunta de negócio

Esta parte está sendo reconstruída. A skill `ask` ainda aponta para scripts que este
repositório não tem mais (`query_catalog.py`), e volta a funcionar quando o eixo de
componente entrar no grafo da `blueprintfy` — junto com a extração dela para o catálogo
de skills. Até lá, `docs/como-perguntar-por-subdominio.md` descreve o fluxo antigo.

## Ferramentas

As skills que este repositório carrega (`blueprintfy`, `graphify`) são instaladas
localmente e não versionadas aqui — ver `.gitignore`. O que elas escrevem
(`CONTEXT-MAP.md`, `CONTEXT.md`) é versionado normalmente e continua legível sem elas.
