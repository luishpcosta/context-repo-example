#!/usr/bin/env python3
"""Instala um hook de pre-commit que roda a tríade de validação do context-repo.

A tríade existe porque os três elos podem sair de sincronia silenciosamente:
  1. catalog-info.yaml em dia com CONTEXT-MAP.md/CONTEXT.md  (build_catalog.py --check)
  2. o YAML continua íntegro/parseável
  3. os subdomínios ainda resolvem  (query_catalog.py list-domains)

Sem o hook, esquecer o passo 1 deixa o catálogo desatualizado sem nenhum aviso até
alguém notar a divergência manualmente.

Uso:
    python3 scripts/install_hooks.py              # instala .git/hooks/pre-commit
    python3 scripts/install_hooks.py --force      # sobrescreve um hook de terceiros
    python3 scripts/install_hooks.py --uninstall  # remove o hook (só se for o nosso)
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

from catalog_config import repo_root

ROOT = repo_root()
HOOK_PATH = ROOT / ".git" / "hooks" / "pre-commit"
SENTINEL = "# context-repo-validation-hook"

HOOK_BODY = f"""#!/bin/sh
{SENTINEL} — gerado por scripts/install_hooks.py, seguro de remover.
# Valida os três elos do context-repo antes de deixar o commit passar.
set -e

cd "$(git rev-parse --show-toplevel)"

echo "[context-repo] validando catálogo..."
python3 scripts/build_catalog.py --check
python3 -c "import yaml; list(yaml.safe_load_all(open('catalog-info.yaml', encoding='utf-8')))"
python3 scripts/query_catalog.py list-domains > /dev/null
echo "[context-repo] ok."
"""


def main() -> int:
    args = sys.argv[1:]
    hooks_dir = HOOK_PATH.parent
    if not hooks_dir.exists():
        print(f"{hooks_dir} não existe — este diretório é um repositório git?")
        return 1

    existing = HOOK_PATH.read_text(encoding="utf-8") if HOOK_PATH.exists() else None
    ours = existing is not None and SENTINEL in existing

    if "--uninstall" in args:
        if existing is None:
            print("Nenhum hook de pre-commit instalado.")
            return 0
        if not ours:
            print("O pre-commit existente não foi criado por este script — "
                  "não vou remover. Apague à mão se for o caso.")
            return 1
        HOOK_PATH.unlink()
        print(f"Hook removido: {HOOK_PATH}")
        return 0

    if existing is not None and not ours and "--force" not in args:
        print(f"Já existe um pre-commit em {HOOK_PATH} que não foi criado por este "
              "script. Use --force para sobrescrever (o conteúdo atual será perdido).")
        return 1

    HOOK_PATH.write_text(HOOK_BODY, encoding="utf-8")
    HOOK_PATH.chmod(HOOK_PATH.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Hook instalado em {HOOK_PATH}")
    print("A partir de agora, todo commit valida catálogo + YAML + subdomínios.")
    print("Para pular pontualmente (ex.: commit de WIP): git commit --no-verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
