#!/usr/bin/env python3
"""Config e acesso aos documentos do context-repo, para os scripts locais.

Não existe arquivo de config separado: a configuração é o front matter do
`CONTEXT-MAP.md` da raiz, que também é o marcador do repositório — se ele existe,
isto é um context-repo.

O parser de front matter não é reimplementado aqui: ele vem do `graph_query.py` da
skill `blueprintfy`, que é a fonte única do formato. O mesmo vale para o
`repo_cache.py` (rede/cache). Isso é deliberado — o context-repo carrega as skills
canônicas; duplicar o parser aqui criaria duas gramáticas que divergem em silêncio.

Stdlib-only (além do que a blueprintfy expõe, que também é stdlib-only).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MAP_FILENAME = "CONTEXT-MAP.md"

DEFAULTS = {
    "product": "Produto",
    "owner": "time",
    "system": "sistema",
    "repos_root": "..",
    "domain_docs": "docs/dominio",
    "component_docs": "docs/componentes",
}

# Onde a blueprintfy pode estar instalada, em ordem de preferência.
SKILL_DIRS = (
    ".claude/skills/blueprintfy/scripts",
    ".agents/skills/blueprintfy/scripts",
)


class BlueprintfyAusente(RuntimeError):
    """A skill blueprintfy não está instalada — sem ela não há parser nem cache."""


def repo_root(start: Path | None = None) -> Path:
    """Raiz do context-repo: a pasta que contém o CONTEXT-MAP.md."""
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / MAP_FILENAME).exists():
            return candidate
    return Path(__file__).resolve().parent.parent


ROOT = repo_root()


def _load_skill_module(nome: str):
    for rel in SKILL_DIRS:
        caminho = ROOT / rel / f"{nome}.py"
        if caminho.exists():
            spec = importlib.util.spec_from_file_location(nome, caminho)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[nome] = mod          # dataclasses resolvem anotações por aqui
            spec.loader.exec_module(mod)
            return mod
    raise BlueprintfyAusente(
        f"Não encontrei `{nome}.py` da skill blueprintfy. Instale-a com "
        "`lup-skills install blueprintfy` (ou copie de ai-lup-skills/skills/blueprintfy) "
        f"— procurei em: {', '.join(SKILL_DIRS)}."
    )


def parse_frontmatter(texto: str) -> dict:
    return _load_skill_module("graph_query").parse_frontmatter(texto)


def repo_cache():
    return _load_skill_module("repo_cache")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

def load_config(root: Path | None = None) -> dict:
    root = root or ROOT
    cfg = dict(DEFAULTS)
    mapa = root / MAP_FILENAME
    if mapa.exists():
        lido = parse_frontmatter(mapa.read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in lido.items() if v is not None})
    return cfg


# --------------------------------------------------------------------------- #
# Documentos
# --------------------------------------------------------------------------- #

def component_dir(root: Path | None = None) -> Path:
    root = root or ROOT
    return root / load_config(root)["component_docs"]


def domain_dir(root: Path | None = None) -> Path:
    root = root or ROOT
    return root / load_config(root)["domain_docs"]


def iter_components(root: Path | None = None):
    """(nome, caminho_do_doc, front_matter) de cada doc de componente."""
    pasta = component_dir(root)
    if not pasta.exists():
        return
    for p in sorted(pasta.glob("*.md")):
        fm = parse_frontmatter(p.read_text(encoding="utf-8"))
        yield fm.get("componente", p.stem), p, fm


def iter_contexts(root: Path | None = None):
    """(slug, caminho_do_CONTEXT, front_matter) de cada contexto."""
    pasta = domain_dir(root)
    if not pasta.exists():
        return
    for p in sorted(pasta.glob("*/CONTEXT.md")):
        yield p.parent.name, p, parse_frontmatter(p.read_text(encoding="utf-8"))


def set_frontmatter_keys(path: Path, valores: dict[str, str]) -> list[str]:
    """Reescreve chaves escalares do front matter preservando o resto do arquivo.

    Edição por linha de propósito: sem emissor de YAML, o corpo do documento, os
    comentários e a ordem das chaves ficam exatamente como estavam. Só chaves que já
    existem são alteradas — criar chave nova é trabalho de quem escreve o documento.
    """
    texto = path.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return []
    _, fm, corpo = texto.split("---", 2)

    mudadas: list[str] = []
    linhas = fm.split("\n")
    for i, linha in enumerate(linhas):
        if ":" not in linha or linha.startswith((" ", "\t", "-")):
            continue
        chave = linha.split(":", 1)[0].strip()
        if chave in valores and str(valores[chave]) != linha.split(":", 1)[1].strip():
            linhas[i] = f"{chave}: {valores[chave]}"
            mudadas.append(chave)

    if mudadas:
        path.write_text(f"---{chr(10).join(linhas)}---{corpo}", encoding="utf-8")
    return mudadas
