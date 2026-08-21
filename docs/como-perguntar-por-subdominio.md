# Como perguntar algo específico de um subdomínio (grafo temporário + graphify)

Guia passo a passo para fazer uma pergunta sobre o código de um componente,
já sabendo a qual subdomínio de produto ela pertence — sem poluir o repositório
da aplicação com `graphify-out/`, e usando o glossário do subdomínio como âncora
da pergunta.

## Por que isso funciona

O `/graphify` sempre escreve `graphify-out/` **relativo ao diretório onde o comando
roda**, não ao caminho que você aponta como corpus. Então: se você cria uma pasta
dentro do `context-repo`, entra nela, e só então aponta o `/graphify` para o
caminho do componente (em outro repositório), o grafo nasce isolado dentro do
`context-repo` — descartável, sem tocar o repo da aplicação.

`scripts/query_catalog.py ask` automatiza a parte de resolução: dado um
subdomínio (e opcionalmente um componente, quando o subdomínio tem mais de um) e
uma pergunta, ele cria a pasta e imprime os comandos prontos.

## Passo a passo (reprodutível)

Pré-requisitos: estar em `context-repo/`, `catalog-info.yaml` em dia (rode
`python3 scripts/build_catalog.py --check` se tiver mexido nos `CONTEXT.md`).

### 1. Resolva o subdomínio → componente → pasta temporária

```bash
cd context-repo
python3 scripts/query_catalog.py ask automation-state-engine \
  "como uma Automation reage a um Trigger e executa uma Action?" \
  core --path homeassistant/components/automation
```

Saída (comandos prontos para copiar):

```
# Pergunta ancorada em 'automation-state-engine' / componente 'core'

Pergunta: como uma Automation reage a um Trigger e executa uma Action?
Termos de glossário relevantes: Trigger, Action, Automation

Grafo temporário — nasce dentro do context-repo, não no repo da app:
1. `cd context-repo/.graphs/automation-state-engine/core`
2. `/graphify /root/.../core/homeassistant/components/automation`
3. `/graphify query "como uma Automation reage a um Trigger e executa uma Action?"`

(pasta criada em `.graphs/automation-state-engine/core` — descartável, `rm -rf .graphs/` para limpar tudo)
```

`--path` é opcional: escopa o `/graphify` a uma subpasta do componente (aqui,
`homeassistant/components/automation` dentro do repo `core`) em vez do repositório
inteiro — importante quando o componente é grande (o `core` sozinho tem 600MB+):
escanear só a fatia do código relevante ao subdomínio deixa a extração rápida e o
grafo focado, em vez de arrastar milhares de arquivos de integrações que nada têm
a ver com a pergunta.

Sem `--path`, o comando usa `spec.repository.local` do componente inteiro (ver
`catalog-info.yaml`).

### Fallback remoto (quando `repository.local` não existe)

Se você clonou só o `context-repo` (sem os 7 repos-fonte em `../`), `ask` e
`next-step` detectam que `repository.local` não existe nesta máquina e caem
para `repository.remote`: clonam o repo (fetch raso, pinado no
`repository.commit` exato documentado no catalog) para `.repo-cache/<componente>/`
e usam esse caminho no lugar do `local`. Isso acontece só na primeira vez por
componente — chamadas seguintes reaproveitam o clone já em `.repo-cache/`, sem
baixar de novo. `.repo-cache/` é git-ignorado, igual `.graphs/` — descartável,
`rm -rf .repo-cache/` a qualquer momento.

### 2. Rode os comandos

```bash
cd .graphs/automation-state-engine/core
/graphify /root/development/repositories/poc-home-assistant/core/homeassistant/components/automation
```

O `/graphify` detecta o corpus, extrai (AST para código + subagente semântico para
os poucos arquivos de doc/config), constrói o grafo, faz clustering e gera:

```
.graphs/automation-state-engine/core/graphify-out/
├── graph.html        # visualização interativa
├── GRAPH_REPORT.md   # relatório em linguagem natural (god nodes, comunidades, perguntas sugeridas)
├── graph.json        # dados brutos do grafo
└── ...
```

### 3. Pergunte

```bash
/graphify query "como uma Automation reage a um Trigger e executa uma Action?"
```

Responde a partir do grafo já construído, citando `source_location` (arquivo/linha
real do `core`).

### 4. Limpe quando terminar (opcional)

```bash
cd context-repo
rm -rf .graphs/    # todo grafo temporário criado por 'ask' até agora
```

`.graphs/` já está no `.gitignore` do `context-repo` — nunca é versionado.

## Prova de execução (rodada real, 2026-08-20)

Rodei os 4 passos acima de ponta a ponta contra o subdomínio
**Automation & State Engine** → componente **core**, escopado em
`homeassistant/components/automation` (13 arquivos, ~5.7k palavras — a pasta real
do código de automação do Home Assistant).

Corpus detectado:

```
Corpus: 13 files · ~5718 words
  code:     10 files (.py)
  document: 3 files (.yaml)
```

Extração:

```
AST:      229 nodes, 466 edges     (extração estrutural de código, sem custo de LLM)
Semantic:  19 nodes,  17 edges     (1 subagente, 3 arquivos: services.yaml + 2 blueprints)
Merge:    248 nodes, 483 edges
Grafo:    248 nodes, 397 edges, 14 comunidades  (depois de deduplicação no build)
Custo:    38.929 tokens de entrada, 0 de saída (só o chunk semântico usa LLM)
```

Saída gerada em `.graphs/automation-state-engine/core/graphify-out/`:
`graph.html`, `graph.json`, `GRAPH_REPORT.md`, `manifest.json`, `cost.json`.

**Aviso de integridade (Step 4.5, honesto por design):** o gate reportou 64 arestas
com ponta "dangling" e 22 colapsadas. Isso é esperado ao escopar com `--path` a uma
subpasta (`homeassistant/components/automation`) em vez do repositório inteiro — o
AST encontra `imports`/referências para símbolos como `homeassistant.core.HomeAssistant`
ou `homeassistant.helpers.trigger`, que existem no `core` mas ficaram fora do corpus
escaneado. Não é corrupção: é o preço de escopar deliberadamente. Se a pergunta
precisar desses símbolos externos, rode sem `--path` (repositório inteiro) ou aponte
para uma pasta maior que inclua os dois lados da referência.

**Comunidades detectadas** (nomeadas na Step 5): Automation Entity Lifecycle,
Automation Entity Constants, Automation Config Processing, Config Validation Types,
Automation Config Validator, Motion Light Blueprint, Automation Execution Trace,
Integration Manifest, State Reproduction, Automation Setup & Websocket API,
Automation Logbook Integration, Reload/Toggle/Turn Off Service.

**God Nodes** (do `GRAPH_REPORT.md`):

```
1. AutomationEntity            - 30 edges
2. BaseAutomationEntity        - 22 edges
3. UnavailableAutomationEntity - 18 edges
4. _create_automation_entities() - 13 edges
5. AutomationConfig            - 12 edges
```

**Resposta real de `graphify query "como uma Automation reage a um Trigger e
executa uma Action?"`** (BFS, 134 nós encontrados, primeiros resultados — citando
`source_location` real do `core`):

```
NODE AutomationEntity              [src=__init__.py loc=L477 community=1]
NODE .async_trigger()              [src=__init__.py loc=L677 community=1]
NODE ._async_trigger_if_enabled()  [src=__init__.py loc=L886 community=1]
NODE ._handle_not_triggered()      [src=__init__.py loc=L903 community=1]
NODE ._async_attach_triggers()     [src=__init__.py loc=L947 community=1]
NODE trace_automation()            [src=trace.py loc=L53   community=6]
NODE AutomationTrace               [src=trace.py loc=L18   community=6]
NODE Turn on the light action      [src=blueprints/motion_light.yaml community=5]
NODE automation.trigger service    [src=services.yaml      community=5]
```

O grafo confirma o fluxo do glossário: `AutomationEntity` (comunidade 1, "Automation
Entity Lifecycle") concentra os métodos `.async_trigger()` /
`._async_trigger_if_enabled()` / `._async_attach_triggers()` que implementam o
Trigger → Action do glossário de domínio, e `AutomationTrace` (comunidade 6)
registra a execução — a Action de fato disparando (ex.: "Turn on the light action"
no blueprint, chamando o serviço externo `light.turn_on`, extraído pela semântica).
