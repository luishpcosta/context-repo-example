#!/usr/bin/env python3
"""Percorre o catalog-info.yaml unificado (Domain + System + Component) para afunilar
de subdomínio -> componente -> ação concreta (ex.: acionar /graphify num repo local
para depois gerar PRD/ADR daquele subdomínio).

view descartável, só-leitura: reconstrói o grafo em memória a partir do YAML a cada
chamada — o YAML (gerado por build_catalog.py) continua sendo a fonte de verdade.

Uso:
    python3 scripts/query_catalog.py list-domains
    python3 scripts/query_catalog.py domain <slug>
    python3 scripts/query_catalog.py component <nome>
    python3 scripts/query_catalog.py next-step <slug-do-dominio> [componente]
    python3 scripts/query_catalog.py ask <slug-do-dominio> "<pergunta>" [componente] [--path <subpasta>]

`ask` prepara (cria no disco) uma pasta descartável em .graphs/<slug>/<componente>/
e imprime os comandos prontos para rodar /graphify apontando pro código do
componente, mas escrevendo o grafo dentro do context-repo (não no repo da app) —
com a pergunta já ancorada nos termos de glossário do subdomínio. Use --path para
apontar para uma subpasta específica do componente (ex.: --path src/billing) em vez
do repositório inteiro.

Se `spec.repository.local` de um componente não existir nesta máquina, cai para
`spec.repository.remote`, clonando pinado em `spec.repository.commit` dentro de
.repo-cache/<componente>/ (git-ignorado, reaproveitado entre chamadas).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from catalog_config import repo_root

ROOT = repo_root()
CATALOG_PATH = ROOT / "catalog-info.yaml"
REPO_CACHE = ROOT / ".repo-cache"


def _resolve_source(comp_name: str, repo: dict) -> tuple[str | None, list[str]]:
    """Resolve o caminho de código-fonte de um componente: local se existir,
    senão clona `repository.remote` (pinado no `commit` do catalog) para
    `.repo-cache/<comp>/` e reusa em chamadas futuras. Retorna (path, logs)."""
    local = repo.get("local")
    if local and Path(local).exists():
        return local, []

    remote = repo.get("remote")
    if not remote:
        return None, [
            f"Componente '{comp_name}' não tem repository.local nem repository.remote "
            "no catalog-info.yaml."
        ]

    commit = repo.get("commit")
    cache_dir = REPO_CACHE / comp_name
    logs = []

    if local:
        logs.append(f"repository.local (`{local}`) não existe nesta máquina — usando remote.")

    if (cache_dir / ".git").exists():
        logs.append(f"Usando clone já em cache: `{cache_dir}` (sem novo download).")
    else:
        logs.append(
            f"Clonando `{remote}` (pinado no commit `{commit[:12] if commit else 'HEAD'}`) "
            f"para `{cache_dir}` — só acontece uma vez, fica em cache pra próxima pergunta."
        )
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["git", "init", "-q", str(cache_dir)], check=True)
            subprocess.run(
                ["git", "-C", str(cache_dir), "remote", "add", "origin", remote], check=True
            )
            if commit:
                # Shallow fetch do commit exato — GitHub permite fetch direto por SHA
                # (allowReachableSHA1InWant), então evita clonar o histórico inteiro.
                fetch = subprocess.run(
                    ["git", "-C", str(cache_dir), "fetch", "--depth", "1", "origin", commit],
                    capture_output=True, text=True,
                )
                if fetch.returncode == 0:
                    subprocess.run(
                        ["git", "-C", str(cache_dir), "checkout", "-q", "FETCH_HEAD"], check=True
                    )
                else:
                    # Servidor não aceita fetch por SHA solto — cai pro clone raso normal
                    # e faz checkout do commit se ele estiver alcançável na branch default.
                    subprocess.run(
                        ["git", "-C", str(cache_dir), "fetch", "--depth", "50", "origin"],
                        check=True,
                    )
                    subprocess.run(
                        ["git", "-C", str(cache_dir), "checkout", "-q", commit], check=True
                    )
            else:
                subprocess.run(
                    ["git", "-C", str(cache_dir), "fetch", "--depth", "1", "origin"], check=True
                )
                subprocess.run(
                    ["git", "-C", str(cache_dir), "checkout", "-q", "FETCH_HEAD"], check=True
                )
        except subprocess.CalledProcessError as e:
            return None, logs + [f"Falha ao clonar '{comp_name}' de {remote}: {e}"]

    return str(cache_dir), logs


def load():
    docs = [d for d in yaml.safe_load_all(CATALOG_PATH.read_text(encoding="utf-8")) if d]
    domains = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Domain"}
    components = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Component"}
    system = next((d for d in docs if d["kind"] == "System"), None)
    return domains, components, system


def _domain_line(slug: str, d: dict, indent: str = "") -> None:
    realized = ", ".join(d["spec"].get("realizedBy", [])) or "(nenhum componente)"
    n_terms = len(d["spec"].get("glossary", []))
    print(f"{indent}- **{slug}** — {d['metadata']['description']}")
    print(f"{indent}  realizedBy: {realized} | glossário: {n_terms} termos")


def cmd_list_domains(domains: dict, components: dict) -> None:
    print("# Subdomínios de produto\n")
    # Hierarquia opcional via spec.parent: imprime em árvore quando existir, senão flat.
    children: dict[str, list[str]] = {}
    roots: list[str] = []
    for slug, d in domains.items():
        parent = d["spec"].get("parent")
        if parent and parent in domains:
            children.setdefault(parent, []).append(slug)
        else:
            roots.append(slug)

    for slug in roots:
        _domain_line(slug, domains[slug])
        for child in children.get(slug, []):
            _domain_line(child, domains[child], indent="  ")
    print(
        "\nPróximo passo: `python3 scripts/query_catalog.py domain <slug>` para "
        "abrir um subdomínio específico."
    )


def cmd_domain(domains: dict, components: dict, slug: str) -> int:
    d = domains.get(slug)
    if not d:
        print(f"Subdomínio '{slug}' não encontrado. Use list-domains para ver os slugs.")
        return 1
    spec = d["spec"]
    print(f"# {slug}\n\n{d['metadata']['description']}\n")

    if spec.get("parent"):
        print(f"Domínio pai: {spec['parent']}\n")
    sub_domains = [s for s, dd in domains.items() if dd["spec"].get("parent") == slug]
    if sub_domains:
        print("## Subdomínios filhos\n")
        for s in sub_domains:
            print(f"- {s} — {domains[s]['metadata']['description']}")
        print()

    if spec.get("dependsOn"):
        print("## Depende de\n")
        for dep in spec["dependsOn"]:
            print(f"- {dep}")
        print()
    if spec.get("sharesContractWith"):
        print("## Compartilha contrato com\n")
        for rel in spec["sharesContractWith"]:
            print(f"- {rel['domain']} (contrato: `{rel['contract']}`)")
        print()

    print("## Realizado por (componentes técnicos)\n")
    for comp_name in spec.get("realizedBy", []):
        comp = components.get(comp_name, {})
        repo = comp.get("spec", {}).get("repository", {})
        print(f"- **{comp_name}** — local: `{repo.get('local', '?')}` "
              f"(ref {repo.get('ref', '?')}, commit {str(repo.get('commit', '?'))[:12]})")
    print()

    print(f"## Glossário ({len(spec.get('glossary', []))} termos)\n")
    for term in spec.get("glossary", []):
        line = f"**{term['term']}**: {term['definition']}"
        if term.get("avoid"):
            line += f" _Evitar_: {term['avoid']}"
        print(f"- {line}")
    print(f"\nFonte editável: `{spec.get('source')}`")
    print(
        f"\nPróximo passo: `python3 scripts/query_catalog.py next-step {slug}` para "
        "afunilar até um componente específico e acionar o /graphify."
    )
    return 0


def cmd_component(components: dict, name: str) -> int:
    c = components.get(name)
    if not c:
        print(f"Componente '{name}' não encontrado.")
        return 1
    spec = c["spec"]
    repo = spec.get("repository", {})
    print(f"# {name}\n\n{spec.get('scope', c['metadata'].get('description', ''))}\n")
    print(f"- subdomain(s): {', '.join(spec.get('subdomain', []))}")
    print(f"- local: {repo.get('local')}")
    print(f"- remote: {repo.get('remote')}")
    print(f"- ref: {repo.get('ref')} (commit {repo.get('commit')})")
    return 0


def cmd_next_step(domains: dict, components: dict, slug: str, comp_hint: str | None) -> int:
    d = domains.get(slug)
    if not d:
        print(f"Subdomínio '{slug}' não encontrado. Use list-domains para ver os slugs.")
        return 1
    realized_by = d["spec"].get("realizedBy", [])
    if not realized_by:
        print(f"Subdomínio '{slug}' não tem componente técnico associado ainda.")
        return 1

    if comp_hint and comp_hint in realized_by:
        targets = [comp_hint]
    elif len(realized_by) == 1:
        targets = realized_by
    else:
        print(
            f"Subdomínio '{slug}' é realizado por {len(realized_by)} componentes: "
            f"{', '.join(realized_by)}."
        )
        print(
            "Rode de novo passando um deles, ex.: "
            f"`python3 scripts/query_catalog.py next-step {slug} {realized_by[0]}`\n"
        )
        targets = realized_by

    terms = [t["term"] for t in d["spec"].get("glossary", [])]
    print(f"# Funil de foco: {slug}\n")
    print(f"Termos de domínio para orientar a leitura do código (contexto para o "
          f"/graphify): {', '.join(terms)}\n")
    for comp_name in targets:
        comp = components.get(comp_name, {})
        repo = comp.get("spec", {}).get("repository", {})
        local, logs = _resolve_source(comp_name, repo)
        for line in logs:
            print(f"> {line}")
        print(f"## {comp_name}")
        print(f"1. `cd {local}`")
        print("2. Rode `/graphify` nesse repositório para construir o grafo de "
              "conhecimento do código.")
        print(f"3. Ao explorar o grafo, use os termos de domínio acima como âncora "
              f"para localizar os nós relevantes (ex.: onde '{terms[0] if terms else '...'}' "
              f"é implementado).")
        print(f"4. Com o grafo + o glossário do subdomínio em mãos, é possível "
              f"iniciar PRDs/ADRs específicos de '{slug}'.\n")
    return 0


def cmd_ask(
    domains: dict, components: dict, slug: str, question: str,
    comp_hint: str | None, path_override: str | None,
) -> int:
    d = domains.get(slug)
    if not d:
        print(f"Subdomínio '{slug}' não encontrado. Use list-domains para ver os slugs.")
        return 1
    realized_by = d["spec"].get("realizedBy", [])
    if not realized_by:
        print(f"Subdomínio '{slug}' não tem componente técnico associado ainda.")
        return 1

    if comp_hint and comp_hint in realized_by:
        comp_name = comp_hint
    elif len(realized_by) == 1:
        comp_name = realized_by[0]
    else:
        print(
            f"Subdomínio '{slug}' é realizado por {len(realized_by)} componentes: "
            f"{', '.join(realized_by)}. Passe um deles, ex.: "
            f"`ask {slug} \"{question}\" {realized_by[0]}`"
        )
        return 1

    comp = components.get(comp_name, {})
    repo = comp.get("spec", {}).get("repository", {})
    local, logs = _resolve_source(comp_name, repo)
    for line in logs:
        print(f"> {line}")
    if not local:
        return 1

    source_path = str((Path(local) / path_override).resolve()) if path_override else local

    graph_dir = ROOT / ".graphs" / slug / comp_name
    graph_dir.mkdir(parents=True, exist_ok=True)

    terms = [t["term"] for t in d["spec"].get("glossary", [])]
    anchored_question = question
    hint_terms = [t for t in terms if t.lower() in question.lower()]
    if not hint_terms:
        hint_terms = terms[:3]

    print(f"# Pergunta ancorada em '{slug}' / componente '{comp_name}'\n")
    print(f"Pergunta: {question}")
    print(f"Termos de glossário relevantes: {', '.join(hint_terms)}\n")
    print("Grafo temporário — nasce dentro do context-repo, não no repo da app:")
    print(f"1. `cd {graph_dir}`")
    print(f"2. `/graphify {source_path}`")
    print(f'3. `/graphify query "{anchored_question}"`')
    print(
        f"\n(pasta criada em `{graph_dir.relative_to(ROOT)}` — descartável, "
        "`rm -rf .graphs/` para limpar tudo)"
    )
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    if not CATALOG_PATH.exists():
        print(f"catalog-info.yaml não encontrado em {ROOT}.")
        return 1

    domains, components, system = load()
    cmd, *rest = args

    if cmd == "list-domains":
        cmd_list_domains(domains, components)
        return 0
    if cmd == "domain" and rest:
        return cmd_domain(domains, components, rest[0])
    if cmd == "component" and rest:
        return cmd_component(components, rest[0])
    if cmd == "next-step" and rest:
        return cmd_next_step(domains, components, rest[0], rest[1] if len(rest) > 1 else None)
    if cmd == "ask" and len(rest) >= 2:
        slug, question, *tail = rest
        path_override = None
        if "--path" in tail:
            i = tail.index("--path")
            path_override = tail[i + 1]
            del tail[i:i + 2]
        comp_hint = tail[0] if tail else None
        return cmd_ask(domains, components, slug, question, comp_hint, path_override)

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
