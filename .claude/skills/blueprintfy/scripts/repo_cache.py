#!/usr/bin/env python3
"""Resolve o código-fonte de um componente técnico, com cache local descartável.

Este módulo existe para manter o `graph_query.py` puro: o grafo é uma view offline,
descartável e sem efeito colateral, e é isso que torna seguro invocá-lo de dentro de
outras skills. Toda a rede (clone, fetch, checkout) mora aqui, e é importada por quem
precisa de código-fonte de verdade — hoje a skill `ask`, o `validate.py` do
context-repo e o resolvedor de componente do grafo.

Fonte dos dados: o front matter de um doc de componente, ex.:

    ---
    componente: core
    remote: https://github.com/home-assistant/core.git
    local: ../core
    ref: 2026.8.2
    commit: 3fb456fa1fe4abbe6b89367b98f282043e9b02dd   # pin: muda quando um humano decide
    ultimo_visto: 9c1d0b7e...                          # marca d'água: o script atualiza
    ---

Duas revisões, dois consumidores:

  - `rev="pin"` (default) — o `commit`. É o que PB/PRD/ADR citam e o que o
    `validate.py` confere: a documentação descreve *aquele* código, não o HEAD.
  - `rev="latest"` — o `ultimo_visto`. É o que o `ask` quer, porque a pergunta é
    "como o produto funciona hoje".

`commit != ultimo_visto` é, literalmente, o sinal de que o componente está descasado.

Regras de rede (o pre-commit do context-repo depende delas):

  - `local` existente vence sempre e nunca toca a rede.
  - Cache já na revisão pedida também não toca a rede.
  - Só o primeiro encontro com um componente — ou uma troca de revisão — exige rede.
  - `allow_network=False` nunca falha por rede: devolve o cache marcado como
    `stale`, para o chamador decidir se avisa ou recusa.

Stdlib-only: nenhuma dependência externa.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

CACHE_DIRNAME = ".repo-cache"
DEFAULT_TIMEOUT = 120


@dataclass
class Resolution:
    """Resultado de uma resolução. `path is None` significa falha — veja `error`."""

    path: str | None = None
    revision: str | None = None
    source: str | None = None          # "local" | "cache" | None
    stale: bool = False                # cache existe, mas não na revisão pedida
    error: str | None = None
    logs: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.path is not None


def _git(args: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    """Roda git sem nunca abrir prompt de credencial.

    Um prompt interativo dentro de um hook de pre-commit trava o commit sem output;
    GIT_TERMINAL_PROMPT=0 transforma isso em erro imediato, que sabemos reportar.
    """
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="")
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, env=env, timeout=timeout
    )


def cache_dir(name: str, root: Path) -> Path:
    return Path(root) / CACHE_DIRNAME / name


def cached_revision(name: str, root: Path) -> str | None:
    """SHA atualmente em checkout no cache, ou None se não há cache utilizável."""
    cache = cache_dir(name, root)
    if not (cache / ".git").exists():
        return None
    proc = _git(["-C", str(cache), "rev-parse", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else None


def target_revision(repo: dict, rev: str = "pin") -> str | None:
    """Traduz `rev` para o SHA pedido no front matter do componente.

    `rev` aceita "pin", "latest" ou um SHA/ref literal.
    """
    if rev == "pin":
        return repo.get("commit")
    if rev == "latest":
        return repo.get("ultimo_visto") or repo.get("commit")
    return rev


def is_drifted(repo: dict) -> bool:
    """True quando o pin e a marca d'água divergem — o componente está descasado."""
    commit, visto = repo.get("commit"), repo.get("ultimo_visto")
    return bool(commit and visto and commit != visto)


def resolve(
    name: str,
    repo: dict,
    root: Path,
    *,
    rev: str = "pin",
    allow_network: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> Resolution:
    """Devolve um caminho no disco com o código de `name` na revisão pedida.

    `repo` é o front matter do doc de componente; `root` é a raiz do context-repo,
    contra a qual `local` é resolvido (ele é gravado relativo de propósito, para não
    vazar a estrutura de diretórios de quem gerou o catálogo).
    """
    res = Resolution()
    wanted = target_revision(repo, rev)

    local = repo.get("local")
    if local:
        local_path = (Path(root) / local).resolve()
        if local_path.exists():
            res.path = str(local_path)
            res.source = "local"
            res.revision = _head_of(local_path)
            return res
        res.logs.append(f"`{local}` não existe nesta máquina — caindo para o remote.")

    remote = repo.get("remote")
    if not remote:
        res.error = (
            f"Componente '{name}' não tem `local` utilizável nem `remote` no front matter."
        )
        return res

    cache = cache_dir(name, root)
    current = cached_revision(name, root)

    if current and (not wanted or current.startswith(wanted) or wanted.startswith(current)):
        res.path = str(cache)
        res.source = "cache"
        res.revision = current
        res.logs.append(f"Cache já está na revisão pedida ({_short(current)}) — sem rede.")
        return res

    if not allow_network:
        if current:
            res.path = str(cache)
            res.source = "cache"
            res.revision = current
            res.stale = True
            res.logs.append(
                f"Sem rede: usando o cache em {_short(current)}, mas a revisão pedida é "
                f"{_short(wanted)}."
            )
            return res
        res.error = (
            f"Componente '{name}' nunca foi baixado e a rede está desabilitada — "
            f"rode uma vez com rede para popular `{CACHE_DIRNAME}/{name}`."
        )
        return res

    ok, logs = _fetch(name, remote, wanted, cache, timeout)
    res.logs.extend(logs)
    if not ok:
        if current:
            res.path = str(cache)
            res.source = "cache"
            res.revision = current
            res.stale = True
            res.logs.append(f"Falha na rede — seguindo com o cache em {_short(current)}.")
            return res
        res.error = f"Não consegui obter o código de '{name}' a partir de {remote}."
        return res

    res.path = str(cache)
    res.source = "cache"
    res.revision = cached_revision(name, root)
    return res


def _fetch(
    name: str, remote: str, wanted: str | None, cache: Path, timeout: int
) -> tuple[bool, list[str]]:
    """Popula/atualiza `cache` na revisão `wanted` (ou no HEAD, se ela for None)."""
    logs: list[str] = []
    fresh = not (cache / ".git").exists()

    if fresh:
        logs.append(
            f"Baixando `{remote}` em {_short(wanted)} para `{cache.name}` — "
            "só na primeira vez, fica em cache para as próximas."
        )
        cache.mkdir(parents=True, exist_ok=True)
        for args in (["init", "-q", str(cache)], ["-C", str(cache), "remote", "add", "origin", remote]):
            proc = _git(args, timeout)
            if proc.returncode != 0:
                return False, logs + [f"git {' '.join(args)}: {proc.stderr.strip()}"]
    else:
        logs.append(f"Atualizando o cache de '{name}' para {_short(wanted)}.")

    try:
        if wanted:
            # Fetch direto por SHA: o GitHub permite (allowReachableSHA1InWant), o que
            # evita baixar o histórico inteiro de repositórios grandes.
            proc = _git(["-C", str(cache), "fetch", "--depth", "1", "origin", wanted], timeout)
            if proc.returncode != 0:
                # Servidor que não aceita SHA solto: clone raso e checkout pelo nome.
                proc = _git(["-C", str(cache), "fetch", "--depth", "50", "origin"], timeout)
                if proc.returncode != 0:
                    return False, logs + [proc.stderr.strip()]
                proc = _git(["-C", str(cache), "checkout", "-q", wanted], timeout)
                return (proc.returncode == 0), logs + _err(proc)
            proc = _git(["-C", str(cache), "checkout", "-q", "FETCH_HEAD"], timeout)
            return (proc.returncode == 0), logs + _err(proc)

        proc = _git(["-C", str(cache), "fetch", "--depth", "1", "origin"], timeout)
        if proc.returncode != 0:
            return False, logs + [proc.stderr.strip()]
        proc = _git(["-C", str(cache), "checkout", "-q", "FETCH_HEAD"], timeout)
        return (proc.returncode == 0), logs + _err(proc)
    except subprocess.TimeoutExpired:
        return False, logs + [f"git excedeu {timeout}s falando com {remote}."]


def _err(proc: subprocess.CompletedProcess) -> list[str]:
    return [proc.stderr.strip()] if proc.returncode != 0 and proc.stderr.strip() else []


def _head_of(path: Path) -> str | None:
    proc = _git(["-C", str(path), "rev-parse", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else None


def _short(sha: str | None) -> str:
    return sha[:12] if sha else "HEAD"
