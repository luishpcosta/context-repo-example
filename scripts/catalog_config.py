#!/usr/bin/env python3
"""Config compartilhada pelos scripts do context-repo.

Um context-repo é descrito por um `.context-repo.yml` na raiz. Ele existe para que
`build_catalog.py`/`query_catalog.py`/`scan_repos.py` sejam genéricos — nada de nome
de produto, owner ou caminho hardcoded no código.

Formato (todos os campos têm default, o arquivo inteiro é opcional):

    product: Nome do Produto           # usado no cabeçalho do catalog-info.yaml gerado
    owner: time-dono                   # vira spec.owner nos blocos Domain gerados
    system: slug-do-system             # nome do bloco kind: System
    repos_root: ..                     # onde os repositórios técnicos estão clonados
    domain_docs: docs/dominio          # onde vivem os CONTEXT.md por subdomínio
"""
from __future__ import annotations

from pathlib import Path

import yaml

DEFAULTS = {
    "product": "Produto",
    "owner": "time",
    "system": "sistema",
    "repos_root": "..",
    "domain_docs": "docs/dominio",
}

CONFIG_FILENAME = ".context-repo.yml"


def repo_root(start: Path | None = None) -> Path:
    """Raiz do context-repo: a pasta que contém catalog-info.yaml.

    Sobe a partir de `start` (default: a pasta do script) até achar o catálogo, o que
    permite rodar os scripts de qualquer subdiretório do repo.
    """
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "catalog-info.yaml").exists():
            return candidate
    # Sem catálogo ainda (bootstrap em andamento): assume o pai de scripts/.
    return Path(__file__).resolve().parent.parent


def load_config(root: Path | None = None) -> dict:
    root = root or repo_root()
    cfg = dict(DEFAULTS)
    path = root / CONFIG_FILENAME
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in loaded.items() if v is not None})
    return cfg
