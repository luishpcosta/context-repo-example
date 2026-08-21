# Como criar um "context-repo" do zero

Playbook reproduzível, agnóstico de projeto, para montar o padrão usado neste
repositório em qualquer produto novo. Este documento usa o `context-repo` da
POC Home Assistant como exemplo ilustrativo em cada passo, mas nada aqui é
específico dele — troque os nomes de subdomínio/componente pelos do seu
produto e o padrão se replica.

> **Caminho rápido:** a skill `context-repo-bootstrap`
> (`.claude/skills/context-repo-bootstrap/`) automatiza as Fases 0, 2, 3 e 5
> descritas abaixo — ela traz os scripts já genéricos (config-driven via
> `.context-repo.yml`), os templates de scaffold e o hook de validação. Este
> documento continua valendo como explicação do **porquê** de cada peça, e como
> guia para quem preferir montar à mão ou precisar entender o que a skill fez.

## 1. O que é esse padrão

Um "context-repo" documenta um produto em **dois eixos correlacionados**, sem
conter nenhum código executável do produto em si:

1. **Arquitetura técnica as-is** — um catálogo (`catalog-info.yaml`, formato
   Backstage) que lista os repositórios técnicos reais que compõem o produto:
   onde ficam, em que commit, o que cada um faz.
2. **Domínio de produto (DDD)** — um glossário vivo por subdomínio de negócio
   (`CONTEXT-MAP.md` + um `CONTEXT.md` por subdomínio), mantido por entrevista
   contínua em vez de escrito de uma vez e esquecido.

A correlação entre os dois eixos — "este termo de domínio é implementado por
qual repositório, em qual pasta?" — é o que permite uma terceira camada, uma
automação de consulta em linguagem natural (`/ask` neste repo) que traduz uma
pergunta de produto ("como uma automação reage a um evento?") num grafo de
código construído **sob demanda**, só para aquele pedaço do código, sem
precisar indexar o produto inteiro permanentemente.

O context-repo em si é **só documentação/manifesto** — os repositórios
técnicos-fonte ficam fora dele (neste repo, clonados em `../`).

## 2. Pré-requisitos

- Skill `graphify` instalada — ferramenta genérica que transforma qualquer
  pasta local ou URL do GitHub num grafo de conhecimento navegável
  (`/graphify <path>`, `/graphify query "<pergunta>"`). Não sabe nada sobre
  "subdomínio", "componente" ou "catálogo" — é um motor de grafo puro.
- Skill `blueprintfy` instalada — conduz a entrevista de modelagem de domínio
  e mantém `CONTEXT-MAP.md`/`CONTEXT.md`.
- (Opcional) skill `skill-creator` — só necessária se, na Fase 4, você quiser
  empacotar a automação final numa skill reutilizável em linguagem natural
  (como foi feito aqui com `/ask`).
- Os repositórios técnicos-fonte do produto já clonados localmente, **ou** ao
  menos suas URLs remotas + o commit/ref exato que você quer documentar (a
  Fase 3 cobre como funcionar mesmo sem o clone local presente).

## 3. Roadmap em fases

A ordem abaixo reflete uma dependência real entre os artefatos — cada fase
consome o que a anterior produziu. Pular a ordem (por exemplo, escrever o
script de unificação antes de ter `CONTEXT.md` nenhum) não funciona.

### Fase 0 — Catálogo técnico as-is

100% manual, nenhuma skill envolvida ainda. Crie `catalog-info.yaml` no
formato Backstage (`apiVersion: backstage.io/v1alpha1`) com um bloco
`kind: System` (o produto como um todo) e um bloco `kind: Component` por
repositório técnico-fonte. Estenda o formato padrão do Backstage com estes
campos não-nativos — eles são a fundação de tudo que vem depois:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: core
  description: Backend Python — integrações, motor de automação
spec:
  type: service
  lifecycle: production
  owner: <time-dono>
  system: <nome-do-system>
  scope: Descrição livre do que esse componente faz no produto.
  subdomain: []   # preenchido na Fase 2, não agora
  repository:
    remote: https://github.com/<org>/<repo>.git
    local: /caminho/absoluto/local/do/clone
    ref: <tag-ou-branch-documentada>
    commit: <sha-completo-pinado>
```

Os quatro campos de `repository` (`remote`, `local`, `ref`, `commit`) são
exatamente o que a automação de consulta da Fase 3 vai ler para resolver
"componente → caminho de código" — não esqueça nenhum deles, mesmo que pareça
redundante agora.

Na prática, não digite esses quatro campos à mão: `scripts/scan_repos.py`
(incluído na skill de bootstrap) varre os repositórios já clonados, lê remote,
tag e commit de cada um, e gera os blocos `Component` sozinho — o que evita o
erro mais caro dessa fase, um `commit` digitado errado que quebra o fallback
remoto silenciosamente. Sobram só os campos que exigem conhecimento de negócio
(`description`, `scope`, `subdomain`), que nascem como `TODO`.

Exemplo real: `catalog-info.yaml` (blocos `kind: Component` de `core`,
`frontend`, `supervisor`, etc.) e `README.md` deste repo.

### Fase 1 — Modelo de domínio (skill `blueprintfy`, modo bootstrap)

Invoque a skill de modelagem de domínio no modo de bootstrap. De fábrica, ela:

- Faz 3 perguntas antes de escrever qualquer coisa: existem documentos de
  negócio já escritos? existem ADRs? há mais de um bounded context?
- Cria/mantém `CONTEXT-MAP.md` na raiz (índice de subdomínios + relações) e um
  `CONTEXT.md` por subdomínio (local à sua escolha — aqui,
  `docs/dominio/<slug>/CONTEXT.md`). A skill só é dona da seção
  `## Linguagem` dentro de cada `CONTEXT.md`; o resto do arquivo é seu.
- Aceita front matter opcional em cada `CONTEXT.md` — `depende_de` e
  `compartilha_contrato_com` — que alimenta um grafo de dependências entre
  subdomínios (em memória, nunca uma segunda fonte de verdade).
- Cria ADRs sob demanda (`adr/ADR-<timestamp>-titulo.md`) quando uma decisão é
  difícil de reverter, surpreendente, e envolve trade-off real — não é
  obrigatório usar; este repo, em estágio inicial de POC, não tem nenhum ADR
  ainda.

**Decisão a tomar imediatamente aqui, antes do primeiro commit**: a
*instalação* da skill (`.claude/skills/blueprintfy/`) não deve ser
versionada — só o markdown que ela produz (`CONTEXT-MAP.md`, `CONTEXT.md`).
Adicione a pasta da skill ao `.gitignore` (ou simplesmente nunca dê `git add`
nela) desde o início.

> **Armadilha real vivida neste repo**: a instalação da skill foi commitada
> por engano (`376c6cf`) e revertida um minuto depois (`7b5c0d2`). Evite
> repetir isso decidindo a regra antes de começar, não depois de errar.

Exemplo real: `CONTEXT-MAP.md`, `docs/dominio/automation-state-engine/CONTEXT.md`.

### Fase 2 — Unificação (script bespoke, você escreve)

Nenhuma skill entrega isso de fábrica — é um script pequeno (~150-200 linhas)
que você escreve uma vez. Ele:

1. Lê a seção `## Contextos` de `CONTEXT-MAP.md` para descobrir a lista de
   subdomínios e o caminho do `CONTEXT.md` de cada um.
2. Lê o front matter (`depende_de`, `compartilha_contrato_com`) e a seção
   `## Linguagem` (termos no formato `**Termo**: definição`, com `_Evitar_:`
   opcional) de cada `CONTEXT.md`.
3. Lê o `catalog-info.yaml` já existente (Fase 0) e calcula, por subdomínio,
   quais `Component`s o realizam — varrendo `Component.spec.subdomain` (que
   você preenche manualmente nos componentes técnicos nesta fase, fechando o
   vínculo Domain↔Component nos dois sentidos).
4. Reescreve `catalog-info.yaml` como múltiplos documentos YAML:
   `kind: Domain` (um por subdomínio, **gerado**) seguido de `kind: System` e
   `kind: Component` (preservados intocados da Fase 0).
5. Suporta um modo `--check`: valida se o YAML está em dia com o markdown sem
   reescrever nada, e sai com código de erro se estiver desatualizado —
   plugável em CI ou pre-commit.

Esqueleto do bloco `Domain` gerado, como ponto de partida:

```python
def build_domain_block(slug, description, ctx_md_path, front_matter, glossary, realized_by):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Domain",
        "metadata": {"name": slug, "description": description},
        "spec": {
            "owner": "<time-dono>",
            "dependsOn": front_matter.get("depende_de", []),
            "sharesContractWith": front_matter.get("compartilha_contrato_com", []),
            "realizedBy": realized_by,
            "source": str(ctx_md_path),
            "glossary": glossary,  # [{"term": ..., "definition": ..., "avoid": ...}, ...]
        },
    }
```

**Regra de governança que nasce aqui e vale para sempre**: o bloco `Domain`
gerado nunca é editado à mão — quem quiser mudar o glossário edita o
`CONTEXT.md` fonte e roda o script de novo. Um `Domain` editado manualmente é
sobrescrito na próxima regeneração sem aviso.

Exemplo real: `scripts/build_catalog.py`.

### Fase 3 — Automação de consulta (script bespoke + convenções de pasta)

Também 100% bespoke — outro script (~250-350 linhas) que faz a ponte entre o
catálogo unificado (Fase 2) e o `/graphify` genérico. Comandos mínimos:

- `list-domains` / `domain <slug>` / `component <nome>` — navegação read-only
  sobre o catálogo (recarregado do YAML a cada chamada; o YAML continua sendo
  a única fonte de verdade).
- `ask <slug> "<pergunta>" [componente] [--path <subpasta>]` — o comando
  principal. Resolve subdomínio → componente (pede desambiguação se o
  subdomínio tiver mais de um componente realizador), monta um caminho de
  código-fonte, e imprime os comandos prontos para rodar `/graphify`.

O truque central que faz o `/graphify` genérico virar uma ferramenta de
domínio: **`/graphify` escreve sua saída (`graphify-out/`) relativa ao
diretório de trabalho onde é executado, não ao caminho do corpus apontado**.
Então: `ask` cria uma pasta descartável `.graphs/<slug>/<componente>/` dentro
do context-repo, você entra nela, e só então aponta `/graphify` para o
caminho do componente (que fica em outro repositório) — o grafo nasce
isolado dentro do context-repo, nunca suja o repo da aplicação.

```bash
python3 scripts/query_catalog.py ask <slug> "<pergunta>" [componente] [--path <subpasta>]
# imprime:
#   cd .graphs/<slug>/<componente>
#   /graphify <caminho-resolvido-do-componente>
#   /graphify query "<pergunta>"
```

`--path` escopa `/graphify` a uma subpasta do componente em vez do
repositório inteiro — importante quando o componente é grande (evita
extração lenta e um grafo poluído com código irrelevante à pergunta). Efeito
colateral esperado, não um bug: arestas "soltas" (dangling) para símbolos que
existem no repo mas ficaram fora da pasta escaneada — documente essa
troca deliberada em vez de escondê-la.

**Fallback remoto** (necessário se alguém for clonar só o context-repo, sem
os repositórios-fonte, em outra máquina): se `repository.local` do componente
não existir no disco, clone `repository.remote` pinado exatamente em
`repository.commit` para uma pasta de cache (`.repo-cache/<componente>/`,
reaproveitada entre chamadas). Tente primeiro um fetch raso direto pelo SHA
(`git fetch --depth 1 origin <commit>`) — a maioria dos hosts git aceita; se o
servidor recusar fetch por SHA solto, caia para um fetch mais largo
(`--depth 50`) seguido de `checkout <commit>`.

Duas entradas de `.gitignore` que nascem junto com esta fase e nunca devem
faltar:

```gitignore
.graphs/
.repo-cache/
```

Ambas são lixo descartável — seguro apagar com `rm -rf` a qualquer momento,
o script recria na próxima pergunta.

Exemplo real: `scripts/query_catalog.py`, `.gitignore`,
`docs/como-perguntar-por-subdominio.md` (exemplo ponta a ponta com números
reais de extração).

### Fase 4 — Skill de linguagem natural (opcional, recomendado)

Empacota as Fases 2+3 num fluxo que alguém que só conhece o domínio do
produto consegue usar sem decorar nenhum comando — só faz a pergunta em
português (ou a língua do seu time) e recebe a resposta. Pode ser construída
com a skill `skill-creator`.

Regras centrais a codificar nessa skill wrapper:

- **Regra de ouro**: toda decisão técnica (qual componente, qual subpasta,
  se precisa de `--path`) é resolvida pela própria skill, olhando os dados
  disponíveis. Só volta pro usuário quando a ambiguidade é de **produto**
  (ex.: "isso é sobre o app mobile ou o painel web?"), nunca de implementação
  (nunca "quer que eu use `--path homeassistant/components/automation`?").
- Antes de reconstruir um grafo, checar se já existe um em
  `.graphs/<slug>/<componente>/graphify-out/graph.json` — reaproveitar em vez
  de recriar.
- Para pedidos de atualização, usar `/graphify <path> --update` (que usa o
  `manifest.json` do próprio `graphify` para reprocessar só o que mudou) em
  vez de apagar e reconstruir do zero.
- Traduzir a resposta do grafo (nós/arestas/comunidades) de volta para
  linguagem de produto antes de repassar ao usuário — jargão de grafo fica
  em segundo plano, só como referência (arquivo/linha).

Exemplo real: `.claude/skills/ask/SKILL.md`.

### Fase 5 — Governança (`CLAUDE.md`)

Escreva por último, depois que as regras já emergiram organicamente das
Fases 0-4 — é mais fácil documentar uma convenção depois de tê-la seguido
algumas vezes do que prescrever de antemão. Conteúdo mínimo:

- Qual bloco do catálogo é gerado (nunca editar à mão) vs. editável.
- Que `.graphs/`/`.repo-cache/`/instalação de skills são descartáveis, nunca
  versionados.
- A tríade de validação a rodar antes de todo commit:

```bash
python3 scripts/build_catalog.py --check   # catálogo em dia com o markdown?
python3 -c "import yaml; list(yaml.safe_load_all(open('catalog-info.yaml')))"  # YAML íntegro?
python3 scripts/query_catalog.py list-domains  # os subdomínios ainda resolvem?
```

- Convenção de commit do time (aqui: Conventional Commits, PT-BR, imperativo).

## 4. De fábrica vs. bespoke, por skill

### `blueprintfy`

| De fábrica | Bespoke construído neste repo |
|---|---|
| `CONTEXT-MAP.md` + um `CONTEXT.md` por bounded context | `catalog-info.yaml` com `kind: Domain` — conceito que não existe nativamente no Backstage nem em blueprintfy |
| Seção `## Linguagem` com formato `**Termo**: definição` + `_Evitar_` | `scripts/build_catalog.py`, o gerador que compila esse markdown pro YAML |
| Front matter `depende_de`/`compartilha_contrato_com` → grafo em memória | Tabela de correlação subdomínio↔componente dentro do próprio `CONTEXT-MAP.md` (seção adicional, não faz parte do template padrão da skill) |
| ADRs sob demanda (`adr/ADR-*.md`) | (não usado neste repo — POC em estágio inicial) |
| Entrevista/gate de criação de documento (todo `CONTEXT.md` tem que estar referenciado no mapa) | Decisão explícita de nunca versionar a instalação da skill, só sua saída em markdown |

### `graphify`

| De fábrica | Bespoke construído neste repo |
|---|---|
| `/graphify <path\|url>` genérico — grafo de qualquer pasta/repo | Todo o roteamento subdomínio→componente→caminho (`scripts/query_catalog.py`) |
| `graphify-out/` escrito relativo ao diretório de trabalho (não ao corpus) | A convenção `.graphs/<slug>/<componente>/` que explora esse comportamento pra manter o grafo fora do repo da aplicação |
| `--update` incremental via `manifest.json` próprio | O fallback remoto pinado em commit (`_resolve_source`, `.repo-cache/`) — graphify não sabe nada sobre "onde clonar isso" |
| `query`/`path`/`explain` sobre um grafo já construído | A skill `/ask` de linguagem natural, que decide sozinha quando reconstruir, quando reaproveitar, e traduz a resposta de volta pra linguagem de produto |

## 5. Checklist reproduzível

1. `catalog-info.yaml` com `System` + `Component`s, campos `repository.{remote,local,ref,commit}` preenchidos (Fase 0).
2. Rodar `blueprintfy` em modo bootstrap → `CONTEXT-MAP.md` + `CONTEXT.md` por subdomínio (Fase 1). Já de saída, garantir que a pasta da skill não entra no primeiro commit.
3. Escrever o gerador de unificação, preencher `Component.spec.subdomain`, rodar e conferir o `catalog-info.yaml` resultante (Fase 2).
4. Escrever o script de consulta (`ask`/`next-step`), criar `.gitignore` com `.graphs/` e `.repo-cache/` (Fase 3).
5. (Opcional) empacotar numa skill de linguagem natural (Fase 4).
6. Escrever `CLAUDE.md` com as regras que emergiram + tríade de validação pré-commit (Fase 5).
7. Testar a tríade de validação de ponta a ponta antes do primeiro push.

## 6. Armadilhas conhecidas

- **Versionar a instalação da skill por engano.** Aconteceu neste repo,
  revertido em um commit. Decida a regra antes de começar (Fase 1).
- **Escopar `--path` num componente grande gera arestas "dangling".** É
  esperado, não é corrupção — documente a troca em vez de esconder ou tratar
  como bug.
- **Fetch por SHA solto pode ser recusado por alguns hosts git.** Sempre ter
  o fallback de fetch mais largo + checkout explícito (Fase 3).
- **Esquecer de rodar o `--check` do gerador antes de commitar** deixa o YAML
  dessincronizado do markdown sem nenhum aviso visível até alguém notar a
  divergência manualmente.
