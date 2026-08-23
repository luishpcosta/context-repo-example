#!/usr/bin/env python3
"""Instala um hook de pre-commit que valida a integridade referencial do context-repo.

Antes existia uma tríade, e ela existia por causa de um arquivo GERADO que podia sair
de sincronia com o markdown. Esse arquivo não existe mais: o front matter é a fonte
única, então esse modo de falha morreu por construção e a tríade virou um comando só.

O que o hook pega agora é o que a tríade nunca cobria — elos apontando para o nada:
documento órfão que o CONTEXT-MAP.md não alcança, `realizado_por` citando componente
inexistente, `caminho` que o upstream moveu, `local` com case errado.

O hook NUNCA escreve. Ele falha com a instrução do que rodar, porque um hook que
altera o conteúdo do commit produz commits diferentes em máquinas diferentes a partir
do mesmo `git commit`.

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

from context_config import repo_root

ROOT = repo_root()
HOOK_PATH = ROOT / ".git" / "hooks" / "pre-commit"
SENTINEL = "# context-repo-validation-hook"

HOOK_BODY = f"""#!/bin/sh
{SENTINEL} — gerado por scripts/install_hooks.py, seguro de remover.
# Valida a integridade referencial do context-repo antes de deixar o commit passar.
set -e

cd "$(git rev-parse --show-toplevel)"

echo "[context-repo] validando os elos..."
python3 scripts/validate.py
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
    print("A partir de agora, todo commit valida os elos do mapa, dos contextos e\n"
          "dos componentes (inclusive os `caminho`, contra o código real).")
    print("Para pular pontualmente (ex.: commit de WIP): git commit --no-verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
