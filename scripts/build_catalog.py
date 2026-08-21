#!/usr/bin/env python3
"""Gera um catalog-info.yaml unificado a partir de CONTEXT-MAP.md + CONTEXT.md.

Fonte da verdade (editada por humanos / pela skill blueprintfy):
  - CONTEXT-MAP.md            -> lista de subdomínios (nome, slug, descrição)
  - docs/dominio/*/CONTEXT.md -> front matter de relação + seção `## Linguagem`

catalog-info.yaml já contém os blocos `System` e `Component` (editados manualmente
quando um repo muda de tag/commit — ver README.md). Este script preserva esses blocos
como estão e (re)gera só os blocos `kind: Domain`, escrevendo tudo de volta em um único
arquivo: Domain(s) + System + Component(s), nessa ordem.

Uso:
    python3 scripts/build_catalog.py            # regrava catalog-info.yaml
    python3 scripts/build_catalog.py --check     # só valida, não escreve (exit 1 se
                                                    o arquivo ficaria diferente)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog-info.yaml"
CONTEXT_MAP_PATH = ROOT / "CONTEXT-MAP.md"

CONTEXT_BULLET_RE = re.compile(
    r"^-\s*\[(?P<name>[^\]]+)\]\((?P<path>[^)]+)\)\s*(?:—|--|-)\s*(?P<desc>.+)$",
    re.MULTILINE,
)
TERM_HEADER_RE = re.compile(r"^\*\*(?P<term>.+?)\*\*:\s*\n(?P<rest>.*)$", re.DOTALL)
AVOID_LINE_RE = re.compile(r"^_Evitar_:\s*(?P<avoid>.+)$")


def slugify_from_path(rel_path: str) -> str:
    # ./docs/dominio/<slug>/CONTEXT.md -> <slug>
    parts = Path(rel_path).parts
    return parts[-2]


def parse_context_map(text: str) -> list[dict]:
    """Extrai [{name, slug, description, context_md}] da seção ## Contextos."""
    section = text.split("## Contextos", 1)[1].split("\n## ", 1)[0]
    domains = []
    for m in CONTEXT_BULLET_RE.finditer(section):
        rel = m.group("path")
        domains.append(
            {
                "name": m.group("name").strip(),
                "slug": slugify_from_path(rel),
                "description": m.group("desc").strip(),
                "context_md": (ROOT / rel.lstrip("./")).resolve(),
            }
        )
    return domains


def parse_front_matter(md_text: str) -> tuple[dict, str]:
    if not md_text.startswith("---"):
        return {}, md_text
    _, fm_raw, body = md_text.split("---", 2)
    return (yaml.safe_load(fm_raw) or {}), body


def parse_glossary(body: str) -> list[dict]:
    if "## Linguagem" not in body:
        return []
    section = body.split("## Linguagem", 1)[1]
    blocks = [b.strip() for b in section.strip().split("\n\n") if b.strip()]
    terms = []
    for block in blocks:
        m = TERM_HEADER_RE.match(block)
        if not m:
            continue
        rest_lines = m.group("rest").strip("\n").split("\n")
        avoid = None
        if rest_lines and AVOID_LINE_RE.match(rest_lines[-1].strip()):
            avoid = AVOID_LINE_RE.match(rest_lines[-1].strip()).group("avoid").strip()
            rest_lines = rest_lines[:-1]
        definition = " ".join(line.strip() for line in rest_lines if line.strip())
        entry = {"term": m.group("term").strip(), "definition": definition}
        if avoid:
            entry["avoid"] = avoid
        terms.append(entry)
    return terms


def name_to_slug_map(domains: list[dict]) -> dict[str, str]:
    return {d["name"]: d["slug"] for d in domains}


def load_existing_docs() -> list[dict]:
    raw = CATALOG_PATH.read_text()
    return list(yaml.safe_load_all(raw))


def realized_by_map(existing_docs: list[dict]) -> dict[str, list[str]]:
    """slug do domínio -> [nomes de Component que o realizam], lido do catalog-info.yaml."""
    result: dict[str, list[str]] = {}
    for doc in existing_docs:
        if doc.get("kind") != "Component":
            continue
        comp_name = doc["metadata"]["name"]
        for slug in doc.get("spec", {}).get("subdomain", []) or []:
            result.setdefault(slug, []).append(comp_name)
    return result


def build_domain_docs(domains: list[dict], existing_docs: list[dict]) -> list[dict]:
    slug_by_name = name_to_slug_map(domains)
    realized_by = realized_by_map(existing_docs)
    docs = []
    for d in domains:
        md_text = d["context_md"].read_text()
        front_matter, body = parse_front_matter(md_text)
        glossary = parse_glossary(body)

        depends_on = [
            slug_by_name.get(n, n) for n in front_matter.get("depende_de", []) or []
        ]
        shares_contract = []
        for rel in front_matter.get("compartilha_contrato_com", []) or []:
            shares_contract.append(
                {
                    "domain": slug_by_name.get(rel["contexto"], rel["contexto"]),
                    "contract": rel["contrato"],
                }
            )

        spec = {"owner": "home-assistant"}
        if depends_on:
            spec["dependsOn"] = depends_on
        if shares_contract:
            spec["sharesContractWith"] = shares_contract
        spec["realizedBy"] = realized_by.get(d["slug"], [])
        spec["source"] = str(d["context_md"].relative_to(ROOT))
        spec["glossary"] = glossary

        docs.append(
            {
                "apiVersion": "backstage.io/v1alpha1",
                "kind": "Domain",
                "metadata": {"name": d["slug"], "description": d["description"]},
                "spec": spec,
            }
        )
    return docs


def render(docs: list[dict]) -> str:
    header = (
        "# Catálogo unificado da POC Home Assistant — GERADO por scripts/build_catalog.py.\n"
        "# Não edite os blocos `kind: Domain` diretamente: eles são reconstruídos a partir de\n"
        "# CONTEXT-MAP.md + docs/dominio/*/CONTEXT.md (fonte editável, mantida pela skill\n"
        "# blueprintfy). Os blocos `System`/`Component` continuam editados à mão aqui — ver\n"
        "# README.md (\"Como atualizar\").\n"
        "# Formato: Backstage catalog-info.yaml (backstage.io/v1alpha1), adaptado com campos\n"
        "# custom: spec.scope, spec.repository.*, spec.subdomain (Component) e\n"
        "# spec.glossary/spec.realizedBy/spec.source (Domain). Ver README.md.\n"
    )
    parts = [
        yaml.dump(doc, allow_unicode=True, sort_keys=False, width=88) for doc in docs
    ]
    return header + "---\n" + "---\n".join(parts)


def main() -> int:
    check_only = "--check" in sys.argv

    existing_docs = load_existing_docs()
    non_domain_docs = [d for d in existing_docs if d.get("kind") != "Domain"]
    system_docs = [d for d in non_domain_docs if d.get("kind") == "System"]
    component_docs = [d for d in non_domain_docs if d.get("kind") == "Component"]

    domains = parse_context_map(CONTEXT_MAP_PATH.read_text())
    domain_docs = build_domain_docs(domains, non_domain_docs)

    system_docs[0].setdefault("spec", {})["domains"] = [d["slug"] for d in domains]

    final_docs = domain_docs + system_docs + component_docs
    rendered = render(final_docs)

    if check_only:
        current = CATALOG_PATH.read_text()
        if current.strip() == rendered.strip():
            print("catalog-info.yaml está em dia com CONTEXT-MAP.md/CONTEXT.md.")
            return 0
        print("catalog-info.yaml está DESATUALIZADO — rode sem --check para regravar.")
        return 1

    CATALOG_PATH.write_text(rendered)
    print(f"catalog-info.yaml regravado com {len(domain_docs)} Domain(s), "
          f"{len(system_docs)} System, {len(component_docs)} Component(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
