#!/usr/bin/env python3
"""Descobre os repositórios técnicos clonados e mantém os docs de componente em dia.

Varre `repos_root` (front matter do CONTEXT-MAP.md, default `..`), encontra toda pasta
que é um repositório git, e lê de cada uma: URL do remote `origin`, commit atual
(`HEAD`) e a tag mais próxima (ou o branch, se não houver tag).

Cada componente é um markdown em `component_docs` (default `docs/componentes/`), com
os dados no front matter. Duas revisões, com donos diferentes:

    commit:       o PIN. Descreve o código que a documentação afirma descrever.
                  Só um humano o move, com --pin. PB/PRD/ADR citam este.
    ultimo_visto: a MARCA D'ÁGUA. O script atualiza sozinho com --update-refs.
                  É o "como está hoje" que o /graphify usa.

`commit != ultimo_visto` é o sinal de que o componente está descasado: o código andou
e a documentação ainda não foi conferida contra ele.

Uso:
    python3 scripts/scan_repos.py                 # dry-run: o que encontrou e o que divergiu
    python3 scripts/scan_repos.py --write         # cria os docs dos componentes novos
    python3 scripts/scan_repos.py --update-refs   # atualiza ultimo_visto (nunca o pin)
    python3 scripts/scan_repos.py --pin           # promove o pin para o ultimo_visto
    python3 scripts/scan_repos.py --root <path>   # varre outro diretório

Stdlib-only: nenhuma dependência externa.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from context_config import (
    ROOT,
    component_dir,
    iter_components,
    load_config,
    set_frontmatter_keys,
)

TODO_TITULO = "TODO: descreva o componente em uma linha"
TODO_ESCOPO = "TODO: o que este componente faz no produto, em uma frase."


def git(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return (proc.stdout.strip() or None) if proc.returncode == 0 else None


def normalize_remote(url: str | None) -> str | None:
    """git@github.com:org/repo.git -> https://github.com/org/repo.git"""
    if not url:
        return None
    if url.startswith("git@"):
        host, _, path = url.partition(":")
        return f"https://{host.removeprefix('git@')}/{path}"
    return url


def relative_local(repo: Path) -> str:
    """Caminho relativo à raiz do context-repo (ex.: `../core`).

    Relativo mantém o catálogo portátil e não vaza a estrutura de diretórios de quem o
    gerou. Preserva o case do diretório: `../iOS` e `../ios` são caminhos diferentes em
    Linux, e errar isso quebra a resolução em silêncio.
    """
    try:
        return os.path.relpath(repo.resolve(), ROOT)
    except ValueError:
        return str(repo.resolve())


def describe_repo(repo: Path) -> dict:
    ref = git(repo, "describe", "--tags", "--abbrev=0") or git(
        repo, "rev-parse", "--abbrev-ref", "HEAD"
    )
    return {
        "nome": repo.name.lower(),
        "local": relative_local(repo),
        "remote": normalize_remote(git(repo, "remote", "get-url", "origin")),
        "ref": ref,
        "head": git(repo, "rev-parse", "HEAD"),
    }


def discover(repos_root: Path) -> list[dict]:
    achados = []
    for child in sorted(repos_root.iterdir()):
        if not child.is_dir() or not (child / ".git").exists():
            continue
        if child.resolve() == ROOT.resolve():
            continue  # o próprio context-repo não é um componente do produto
        achados.append(describe_repo(child))
    return achados


def novo_doc(info: dict) -> str:
    return "\n".join([
        "---",
        f"componente: {info['nome']}",
        f"titulo: {TODO_TITULO}",
        f"remote: {info['remote']}",
        f"local: {info['local']}",
        f"ref: {info['ref']}",
        f"commit: {info['head']}",
        f"ultimo_visto: {info['head']}",
        "---",
        "",
        f"# {info['nome']}",
        "",
        TODO_ESCOPO,
        "",
    ])


def main() -> int:
    args = sys.argv[1:]
    write = "--write" in args
    update_refs = "--update-refs" in args
    pin = "--pin" in args

    cfg = load_config()
    repos_root = Path(args[args.index("--root") + 1]) if "--root" in args else Path(cfg["repos_root"])
    if not repos_root.is_absolute():
        repos_root = (ROOT / repos_root).resolve()

    if not repos_root.exists():
        print(f"Diretório de repositórios não existe: {repos_root}")
        return 1

    achados = discover(repos_root)
    if not achados:
        print(f"Nenhum repositório git encontrado em {repos_root}.")
        return 1

    documentados = {nome: (p, fm) for nome, p, fm in iter_components()}

    print(f"# Repositórios encontrados em {repos_root}\n")
    novos, divergentes, descasados = [], [], []
    for info in achados:
        conhecido = info["nome"] in documentados
        print(f"- **{info['nome']}** ({'documentado' if conhecido else 'NOVO'})")
        print(f"  remote: {info['remote']}")
        print(f"  ref: {info['ref']} | HEAD: {(info['head'] or '?')[:12]}")

        if not conhecido:
            novos.append(info)
            continue

        caminho, fm = documentados[info["nome"]]
        if fm.get("ultimo_visto") != info["head"] or fm.get("local") != info["local"]:
            divergentes.append((info, caminho, fm))
        if fm.get("commit") != info["head"]:
            descasados.append((info, caminho, fm))
    print()

    if not (write or update_refs or pin):
        if novos:
            print(f"## {len(novos)} componente(s) sem doc — `--write` para criar\n")
            for i in novos:
                print(f"- `{component_dir().name}/{i['nome']}.md`")
            print()
        if divergentes:
            print(f"{len(divergentes)} componente(s) com marca d'água atrasada — "
                  "`--update-refs` para atualizar.")
        if descasados:
            print(f"\n## {len(descasados)} componente(s) DESCASADO(s) do pin\n")
            for info, caminho, fm in descasados:
                print(f"- **{info['nome']}**: pin `{str(fm.get('commit'))[:12]}` "
                      f"→ código em `{info['head'][:12]}`")
            print("\nO código andou desde o commit que a documentação descreve. Confira o "
                  "que mudou e, quando a documentação estiver conferida, `--pin` promove "
                  "o pin.")
        if not (novos or divergentes or descasados):
            print("Tudo em dia: docs, marca d'água e pin batem com os repositórios.")
        return 0

    mexidos = 0

    if write and novos:
        pasta = component_dir()
        pasta.mkdir(parents=True, exist_ok=True)
        for info in novos:
            (pasta / f"{info['nome']}.md").write_text(novo_doc(info), encoding="utf-8")
            print(f"criado: {pasta.name}/{info['nome']}.md")
        mexidos += len(novos)
        print(f"\n{len(novos)} doc(s) criado(s). Falta, para cada um: preencher `titulo` e o "
              "corpo, referenciá-lo na seção 'Componentes técnicos' do CONTEXT-MAP.md, e "
              "declarar `realizado_por` no CONTEXT.md do contexto que ele realiza.")

    if update_refs and divergentes:
        for info, caminho, _ in divergentes:
            mudadas = set_frontmatter_keys(
                caminho, {"ultimo_visto": info["head"], "local": info["local"]}
            )
            if mudadas:
                print(f"{info['nome']}: {', '.join(mudadas)} atualizado(s).")
        mexidos += len(divergentes)

    if pin and descasados:
        for info, caminho, _ in descasados:
            mudadas = set_frontmatter_keys(
                caminho,
                {"commit": info["head"], "ref": info["ref"], "ultimo_visto": info["head"]},
            )
            if mudadas:
                print(f"{info['nome']}: pin promovido para {info['head'][:12]} "
                      f"(ref {info['ref']}).")
        mexidos += len(descasados)

    if not mexidos:
        print("Nada a fazer — tudo já está em dia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
