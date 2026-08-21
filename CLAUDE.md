# CLAUDE.md — context-repo

Este repositório é **só documentação/manifesto** da POC Home Assistant — nenhum
código executável do produto vive aqui. Ele descreve, em dois eixos que se
correlacionam, os 7 repositórios clonados em `../` (`core`, `frontend`,
`supervisor`, `operating-system`, `docker`, `android`, `iOS`):

- **Arquitetura técnica as-is** — `catalog-info.yaml` (Backstage catalog-info
  adaptado).
- **Domínio de produto (DDD)** — `CONTEXT-MAP.md` + `docs/dominio/*/CONTEXT.md`
  (mantido pela skill `blueprintfy`).

Antes de editar qualquer coisa aqui, leia `README.md` — ele documenta o formato,
as adaptações e os scripts. Este arquivo é sobre **como um agente deve operar**
neste repo para não corromper a correlação entre os dois eixos.

## Fonte da verdade — não edite o gerado

- **`catalog-info.yaml` tem duas origens no mesmo arquivo.** Os blocos
  `kind: Domain` são **gerados** por `scripts/build_catalog.py` a partir de
  `CONTEXT-MAP.md` + `docs/dominio/*/CONTEXT.md` — **nunca edite um bloco
  `Domain` diretamente**, a próxima regeneração sobrescreve. Para mudar
  glossário/relações de domínio, edite o `CONTEXT.md` do subdomínio e rode:
  ```bash
  python3 scripts/build_catalog.py
  ```
- Os blocos `kind: System` e `kind: Component` **são** editados à mão (scope,
  subdomain, description). Os campos `repository.*` (remote, local, ref, commit)
  não precisam ser digitados: `python3 scripts/scan_repos.py --write` cria os
  blocos dos repositórios clonados em `../`, e `--update-refs` reatualiza
  ref/commit quando eles avançam de versão — ver "Como atualizar" no `README.md`.
- Depois de qualquer mudança em `CONTEXT.md`/`CONTEXT-MAP.md`, rode
  `python3 scripts/build_catalog.py --check` antes de commitar. Se falhar, o
  YAML está desatualizado em relação ao markdown — rode sem `--check` para
  regravar, não edite o YAML na mão para "consertar".

## Mudar o modelo de domínio — siga o protocolo da skill blueprintfy

`CONTEXT-MAP.md`/`docs/dominio/*/CONTEXT.md` não são markdown livre — são
mantidos pela skill `blueprintfy` (`.claude/skills/blueprintfy/SKILL.md`, local,
fora do versionamento — ver abaixo). Regras que valem mesmo sem invocar a skill
explicitamente:

- **Nunca grave um termo de glossário sem validar com o usuário primeiro.** Um
  termo errado aqui se propaga pro `catalog-info.yaml` na próxima regeneração.
- **Todo `CONTEXT.md` precisa estar referenciado em `CONTEXT-MAP.md`.** Um
  `CONTEXT.md` órfão é invisível para `build_catalog.py` (ele só lê os caminhos
  listados na seção `## Contextos` do mapa) e para o gate de criação de
  documento da skill.
- **Front matter de relação é estrutural, não decorativo.** `depende_de` e
  `compartilha_contrato_com` no topo de cada `CONTEXT.md` viram
  `spec.dependsOn`/`spec.sharesContractWith` no `Domain` gerado — se a relação
  não existe lá, não existe no catálogo.
- Ao adicionar um subdomínio novo: crie `docs/dominio/<slug>/CONTEXT.md`,
  referencie-o em `CONTEXT-MAP.md`, rode `build_catalog.py`, e adicione
  `spec.subdomain: [<slug>]` no(s) `Component` técnico(s) que o realizam.

## `.graphs/` é lixo descartável, nunca versionado

`scripts/query_catalog.py ask` cria grafos temporários do `graphify` em
`.graphs/<slug>/<componente>/` — propositalmente git-ignorado
(`docs/como-perguntar-por-subdominio.md` explica o porquê). Nunca faça
`git add -f` nisso; se crescer demais, `rm -rf .graphs/` é seguro a qualquer
momento.

Mesma regra vale para `.repo-cache/`: quando `repository.local` de um
componente não existe nesta máquina (ex.: clone só do `context-repo`, sem os
7 repos-fonte em `../`), `ask`/`next-step` clonam `repository.remote` pinado
no `repository.commit` do catalog para lá, como cache reutilizável entre
perguntas. Também git-ignorado, também descartável (`rm -rf .repo-cache/`).

## `.claude/skills/blueprintfy/` também não é versionado

É instalação local da skill, não produto do trabalho dela — ver `.gitignore`.
Se sumir de um clone novo deste repo, a skill precisa ser reinstalada
separadamente; os `CONTEXT.md`/`CONTEXT-MAP.md` que ela já escreveu continuam
válidos e legíveis sem ela (são markdown comum).

## Antes de commitar, valide os três elos

```bash
python3 scripts/build_catalog.py --check   # catalog-info.yaml em dia com o markdown?
python3 -c "import yaml; list(yaml.safe_load_all(open('catalog-info.yaml')))"  # YAML íntegro?
python3 scripts/query_catalog.py list-domains  # os 5 domínios ainda resolvem?
```

Se `build_catalog.py --check` falhar num commit que não devia ter tocado o
domínio, é sinal de que algo editou o bloco `Domain` do YAML na mão — reverta
o bloco e regenere.

`python3 scripts/install_hooks.py` instala essa tríade como hook de pre-commit
(já instalado neste clone). Para pular pontualmente: `git commit --no-verify`.

## Os scripts são genéricos — não hardcode nada neles

`scripts/*.py` não conhecem "Home Assistant": nome do produto, owner, slug do
system e caminhos vêm de `.context-repo.yml` na raiz. Isso é deliberado — os
mesmos scripts são copiados para outros projetos pela skill
`context-repo-bootstrap` (ver `docs/como-criar-context-repo.md`). Se precisar
de um valor específico do produto, adicione ao `.context-repo.yml` e leia via
`catalog_config.load_config()`, nunca escreva literal no script.

## Commits

Conventional Commits, mensagem no imperativo, PT-BR, um commit por mudança
lógica (ex.: `feat(dominio): ...`, `chore(repo): ...`) — sem exceção, é a
convenção usada em todo o histórico deste repo.

## Ao adicionar componente técnico novo (8º repo, etc.)

1. Clone-o em `../` (fora deste repo) e registre a versão/commit.
2. Adicione o bloco `kind: Component` em `catalog-info.yaml` (à mão, mesmo
   formato dos outros 7 — `spec.scope`, `spec.repository.*`, `spec.subdomain`).
3. Decida com o usuário a qual subdomínio existente ele pertence, ou se exige
   um subdomínio novo (siga "Mudar o modelo de domínio" acima).
4. Rode a validação da seção anterior antes de commitar.
