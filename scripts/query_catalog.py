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
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog-info.yaml"


def load():
    docs = list(yaml.safe_load_all(CATALOG_PATH.read_text()))
    domains = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Domain"}
    components = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Component"}
    system = next(d for d in docs if d["kind"] == "System")
    return domains, components, system


def cmd_list_domains(domains: dict, components: dict) -> None:
    print("# Subdomínios de produto\n")
    for slug, d in domains.items():
        realized = ", ".join(d["spec"].get("realizedBy", [])) or "(nenhum componente)"
        n_terms = len(d["spec"].get("glossary", []))
        print(f"- **{slug}** — {d['metadata']['description']}")
        print(f"  realizedBy: {realized} | glossário: {n_terms} termos")
    print(
        "\nPróximo passo: `python3 scripts/query_catalog.py domain <slug>` para "
        "abrir um subdomínio específico."
    )


def cmd_domain(domains: dict, components: dict, slug: str) -> None:
    d = domains.get(slug)
    if not d:
        print(f"Subdomínio '{slug}' não encontrado. Use list-domains para ver os slugs.")
        return 1
    spec = d["spec"]
    print(f"# {slug}\n\n{d['metadata']['description']}\n")

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
              f"(ref {repo.get('ref', '?')}, commit {repo.get('commit', '?')[:12]})")
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
        local = comp.get("spec", {}).get("repository", {}).get("local")
        print(f"## {comp_name}")
        print(f"1. `cd {local}`")
        print(f"2. Rode `/graphify` nesse repositório para construir o grafo de "
              f"conhecimento do código.")
        print(f"3. Ao explorar o grafo, use os termos de domínio acima como âncora "
              f"para localizar os nós relevantes (ex.: onde '{terms[0] if terms else '...'}' "
              f"é implementado).")
        print(f"4. Com o grafo + o glossário do subdomínio em mãos, é possível "
              f"iniciar PRDs/ADRs específicos de '{slug}' (ex.: via skills "
              f"pm-create-prd/prd-to-adr, se instaladas).\n")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    domains, components, system = load()
    cmd, *rest = args

    if cmd == "list-domains":
        cmd_list_domains(domains, components)
        return 0
    if cmd == "domain" and rest:
        return cmd_domain(domains, components, rest[0]) or 0
    if cmd == "component" and rest:
        return cmd_component(components, rest[0])
    if cmd == "next-step" and rest:
        return cmd_next_step(domains, components, rest[0], rest[1] if len(rest) > 1 else None)

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
