# context-repo

Repositório documental da POC Home Assistant. Não contém código executável — só o
catálogo de arquitetura da aplicação distribuída, em `catalog-info.yaml`.

## Formato

`catalog-info.yaml` segue o formato **Backstage Software Catalog**
(`apiVersion: backstage.io/v1alpha1`), o padrão de mercado (CNCF/Spotify Backstage)
para descrever sistemas distribuídos como um `System` composto por `Component`s
relacionados entre si via `dependsOn`, `dependencyOf`, `providesApis` e `consumesApis`.

Esse formato foi escolhido em vez de alternativas como Docker Compose, Open Application
Model/KubeVela ou Score porque seu propósito é puramente documental/de catálogo — não
executa nem orquestra nada — o que combina com o objetivo aqui: só representar a
arquitetura e as dependências.

## Adaptação em relação ao padrão Backstage

O schema oficial não tem campos para escopo de responsabilidade nem para localização
de repositório/versão. Para cobrir isso, cada `Component.spec` foi estendido com dois
campos **não-padrão**:

- `spec.scope` (string): descrição livre da responsabilidade/fronteira do componente
  dentro do sistema.
- `spec.repository` (objeto):
  - `remote`: URL do repositório no GitHub.
  - `local`: caminho absoluto do clone local nesta máquina.
  - `ref`: tag/versão em uso (ex. `2026.8.2`).
  - `commit`: hash completo do commit correspondente a essa tag (`git rev-parse HEAD`).

Essas extensões não quebram compatibilidade com o schema Backstage (que aceita campos
adicionais em `spec`), mas não são reconhecidas por um Backstage real sem um processor
customizado — aqui o arquivo é usado apenas como documento de referência da POC.

## Componentes catalogados

| componente | tipo | repositório remoto |
|---|---|---|
| core | service | github.com/home-assistant/core |
| frontend | website | github.com/home-assistant/frontend |
| supervisor | service | github.com/home-assistant/supervisor |
| operating-system | platform | github.com/home-assistant/operating-system |
| docker | library | github.com/home-assistant/docker |
| android | mobile-app | github.com/home-assistant/android |
| ios | mobile-app | github.com/home-assistant/iOS |

## Como atualizar

Sempre que um dos repositórios em `../` (fora deste repo) mudar de tag/commit, atualize
o bloco `Component` correspondente em `catalog-info.yaml`:

```bash
git -C ../<repo> rev-parse HEAD     # novo commit
git -C ../<repo> describe --tags    # nova ref/tag
```

Depois valide a sintaxe do YAML:

```bash
python3 -c "import yaml; list(yaml.safe_load_all(open('catalog-info.yaml')))"
```
