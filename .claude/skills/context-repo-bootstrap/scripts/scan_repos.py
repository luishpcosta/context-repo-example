#!/usr/bin/env python3
"""Descobre os repositórios técnicos clonados e gera/atualiza os blocos `kind: Component`
do catalog-info.yaml — sem ninguém digitar remote/ref/commit à mão.

Varre `repos_root` (default `..`, configurável em .context-repo.yml), encontra toda
pasta que é um repositório git, e lê de cada uma: URL do remote `origin`, commit
atual (`HEAD`) e a tag mais próxima (ou o nome do branch, se não houver tag).

Uso:
    python3 scripts/scan_repos.py                 # dry-run: imprime o que encontrou
    python3 scripts/scan_repos.py --write         # adiciona os componentes novos ao catálogo
    python3 scripts/scan_repos.py --update-refs   # atualiza ref/commit dos já existentes
    python3 scripts/scan_repos.py --root <path>   # varre outro diretório

`--write` só ACRESCENTA componentes que ainda não existem no catálogo — nunca
sobrescreve `scope`, `subdomain` ou `description` já preenchidos à mão. Os campos que
o script não tem como saber (descrição, escopo, subdomínio) nascem como placeholder
`TODO`, para você preencher depois.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from build_catalog import render
from catalog_config import load_config, repo_root

ROOT = repo_root()
CONFIG = load_config(ROOT)
CATALOG_PATH = ROOT / "catalog-info.yaml"

TODO_DESCRIPTION = "TODO: descreva o componente em uma linha"
TODO_SCOPE = "TODO: o que este componente faz no produto (usado no funil de foco)"


def git(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def normalize_remote(url: str | None) -> str | None:
    """git@github.com:org/repo.git -> https://github.com/org/repo.git"""
    if not url:
        return None
    if url.startswith("git@"):
        host, _, path = url.partition(":")
        host = host.removeprefix("git@")
        return f"https://{host}/{path}"
    return url


def relative_local(repo: Path) -> str:
    """Caminho do repositório relativo à raiz do context-repo (ex.: `../core`).

    Gravar relativo mantém o catálogo portátil e evita vazar o caminho absoluto da
    máquina de quem gerou. Se o repositório estiver em outro volume (relpath
    impossível), cai para absoluto — é melhor um caminho feio que um catálogo errado.
    """
    try:
        return os.path.relpath(repo.resolve(), ROOT)
    except ValueError:
        return str(repo.resolve())


def describe_repo(repo: Path) -> dict:
    ref = git(repo, "describe", "--tags", "--abbrev=0")
    if not ref:
        ref = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    return {
        "name": repo.name.lower(),
        "local": relative_local(repo),
        "remote": normalize_remote(git(repo, "remote", "get-url", "origin")),
        "ref": ref,
        "commit": git(repo, "rev-parse", "HEAD"),
    }


def discover(repos_root: Path) -> list[dict]:
    found = []
    for child in sorted(repos_root.iterdir()):
        if not child.is_dir() or not (child / ".git").exists():
            continue
        if child.resolve() == ROOT.resolve():
            continue  # o próprio context-repo não é um componente do produto
        found.append(describe_repo(child))
    return found


def component_block(info: dict) -> dict:
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Component",
        "metadata": {"name": info["name"], "description": TODO_DESCRIPTION},
        "spec": {
            "type": "service",
            "lifecycle": "production",
            "owner": CONFIG["owner"],
            "system": CONFIG["system"],
            "scope": TODO_SCOPE,
            "subdomain": [],
            "repository": {
                "remote": info["remote"],
                "local": info["local"],
                "ref": info["ref"],
                "commit": info["commit"],
            },
        },
    }


def load_docs() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    return [d for d in yaml.safe_load_all(CATALOG_PATH.read_text(encoding="utf-8")) if d]


def write_docs(docs: list[dict]) -> None:
    order = {"Domain": 0, "System": 1, "Component": 2}
    docs = sorted(docs, key=lambda d: order.get(d.get("kind", ""), 9))
    CATALOG_PATH.write_text(render(docs), encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    write = "--write" in args
    update_refs = "--update-refs" in args

    repos_root = Path(CONFIG["repos_root"])
    if "--root" in args:
        repos_root = Path(args[args.index("--root") + 1])
    if not repos_root.is_absolute():
        repos_root = (ROOT / repos_root).resolve()

    if not repos_root.exists():
        print(f"Diretório de repositórios não existe: {repos_root}")
        return 1

    found = discover(repos_root)
    if not found:
        print(f"Nenhum repositório git encontrado em {repos_root}.")
        return 1

    docs = load_docs()
    existing = {
        d["metadata"]["name"]: d for d in docs if d.get("kind") == "Component"
    }

    print(f"# Repositórios encontrados em {repos_root}\n")
    novos, atualizados = [], []
    for info in found:
        status = "já no catálogo" if info["name"] in existing else "NOVO"
        print(f"- **{info['name']}** ({status})")
        print(f"  remote: {info['remote']}")
        print(f"  ref: {info['ref']} | commit: {(info['commit'] or '?')[:12]}")
        if info["name"] not in existing:
            novos.append(info)
        else:
            repo = existing[info["name"]].setdefault("spec", {}).setdefault("repository", {})
            # `local` entra na comparação para migrar catálogos antigos, gravados com
            # caminho absoluto, para o formato relativo/portátil.
            if (repo.get("commit") != info["commit"]
                    or repo.get("ref") != info["ref"]
                    or repo.get("local") != info["local"]):
                atualizados.append((info, repo))
    print()

    if not write and not update_refs:
        if novos:
            print("## Blocos Component que seriam adicionados (--write para gravar)\n")
            print(
                yaml.dump_all(
                    [component_block(i) for i in novos],
                    allow_unicode=True, sort_keys=False, width=88,
                )
            )
        if atualizados:
            print(f"{len(atualizados)} componente(s) com ref/commit/local divergente do "
                  "catálogo — rode com --update-refs para atualizar.")
        if not novos and not atualizados:
            print("Catálogo já está em dia com os repositórios encontrados.")
        return 0

    changed = 0
    if write and novos:
        docs.extend(component_block(i) for i in novos)
        changed += len(novos)
        print(f"{len(novos)} componente(s) adicionado(s) — preencha os campos TODO "
              "(description, scope, subdomain) antes de rodar build_catalog.py.")
    if update_refs and atualizados:
        for info, repo in atualizados:
            repo["ref"] = info["ref"]
            repo["commit"] = info["commit"]
            repo["local"] = info["local"]
        changed += len(atualizados)
        print(f"{len(atualizados)} componente(s) com ref/commit/local atualizado(s).")

    if not changed:
        print("Nada a fazer — catálogo já está em dia.")
        return 0

    write_docs(docs)
    print(f"catalog-info.yaml regravado. Rode `python3 scripts/build_catalog.py` em "
          "seguida para regenerar os blocos Domain (realizedBy depende de subdomain).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
