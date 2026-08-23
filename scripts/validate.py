#!/usr/bin/env python3
"""Valida a integridade referencial do context-repo. Roda no pre-commit.

Antes, a validação existia para pegar um arquivo GERADO fora de sincronia com o
markdown. Esse arquivo não existe mais — o front matter é a fonte única, então esse
modo de falha morreu por construção. O que sobrou é o que ele nunca cobriu: elos
apontando para o nada.

O que é checado:

  1. O CONTEXT-MAP.md tem o front matter de config.
  2. Todo link do mapa aponta para um arquivo que existe.
  3. Todo CONTEXT.md e todo doc de componente é ALCANÇÁVEL pelo mapa. Um documento
     órfão é invisível para as ferramentas e some em silêncio — este é o modo de
     falha mais perigoso, e é novo aqui.
  4. Todo `realizado_por.componente` existe como doc de componente.
  5. Todo `depende_de`, `compartilha_contrato_com` e `dominio_pai` aponta para um
     contexto que existe.
  6. Todo componente tem `remote`, `commit` e `ultimo_visto`, e o `local` — quando
     declarado — resolve nesta máquina (case-sensitive: `../ios` != `../iOS`).
  7. Todo `caminho` de `realizado_por` existe DENTRO do código do componente.

O item 7 é o único que toca a rede, e segue a regra do repo: `local` existente vence
e não baixa nada; senão usa o `.repo-cache`; e só o primeiro encontro com um
componente exige rede. Sem rede e sem cache, vira aviso — nunca trava um commit de
markdown por causa de conectividade.

Este script NUNCA escreve. Ele falha com a instrução do que rodar.

Uso:
    python3 scripts/validate.py             # valida tudo
    python3 scripts/validate.py --offline   # não baixa nada; o que faltar vira aviso
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from context_config import (
    MAP_FILENAME,
    ROOT,
    BlueprintfyAusente,
    iter_components,
    iter_contexts,
    load_config,
    parse_frontmatter,
    repo_cache,
)

LINK_RE = re.compile(r"^-\s*\[(?P<nome>[^\]]+)\]\((?P<path>[^)]+)\)", re.MULTILINE)
CHAVES_CONFIG = ("product", "owner", "system", "repos_root", "domain_docs", "component_docs")

erros: list[str] = []
avisos: list[str] = []


def erro(msg: str) -> None:
    erros.append(msg)


def aviso(msg: str) -> None:
    avisos.append(msg)


def secao(texto: str, titulo: str) -> str:
    """Corpo de uma seção `## Titulo` do mapa, até o próximo `## `."""
    marcador = f"## {titulo}"
    if marcador not in texto:
        return ""
    return texto.split(marcador, 1)[1].split("\n## ", 1)[0]


def links(texto: str, titulo: str) -> list[tuple[str, Path]]:
    return [
        (m.group("nome"), (ROOT / m.group("path").lstrip("./")))
        for m in LINK_RE.finditer(secao(texto, titulo))
    ]


def validar_mapa(texto: str) -> tuple[set[Path], set[Path]]:
    cfg = parse_frontmatter(texto)
    if not cfg:
        erro(f"{MAP_FILENAME} não tem front matter de config — ele é a config do repo.")
    for chave in CHAVES_CONFIG:
        if chave not in cfg:
            aviso(f"{MAP_FILENAME}: front matter sem `{chave}` (usando o default).")

    contextos, componentes = set(), set()
    for titulo, destino in (("Contextos", contextos), ("Componentes técnicos", componentes)):
        achados = links(texto, titulo)
        if not achados:
            aviso(f"{MAP_FILENAME}: seção '## {titulo}' vazia ou ausente.")
        for nome, caminho in achados:
            if not caminho.exists():
                erro(f"{MAP_FILENAME}: link '{nome}' aponta para `{_rel(caminho)}`, "
                     "que não existe.")
            else:
                destino.add(caminho.resolve())
    return contextos, componentes


def validar_alcance(mapeados: set[Path], no_disco: list[Path], rotulo: str) -> None:
    for caminho in no_disco:
        if caminho.resolve() not in mapeados:
            erro(f"{rotulo} órfão: `{_rel(caminho)}` existe no disco mas o "
                 f"{MAP_FILENAME} não o alcança — ele é invisível para as ferramentas. "
                 f"Adicione-o à seção correspondente do mapa.")


def validar_componentes(componentes: dict) -> None:
    for nome, caminho, fm in componentes.values():
        for chave in ("remote", "commit", "ultimo_visto"):
            if not fm.get(chave):
                erro(f"{_rel(caminho)}: front matter sem `{chave}`.")
        local = fm.get("local")
        if local and not (ROOT / local).resolve().exists():
            # `local` ausente é legítimo — é o cenário que o .repo-cache cobre. Mas um
            # irmão com case diferente no disco não é clone faltando, é erro de
            # digitação: em Linux `../ios` e `../iOS` são caminhos distintos, e o typo
            # custa um clone remoto inteiro em silêncio.
            if (parecido := _irmao_com_outro_case(ROOT / local)):
                erro(f"{_rel(caminho)}: `local: {local}` não existe, mas `{parecido}` "
                     f"existe — só o case difere. Troque para `{parecido}`.")
            elif fm.get("remote"):
                aviso(f"{_rel(caminho)}: `local: {local}` não existe nesta máquina — "
                      "as consultas vão cair para o remote (cache).")
            else:
                erro(f"{_rel(caminho)}: `local: {local}` não existe e não há `remote`.")


def validar_relacoes(contextos: dict, componentes: dict) -> None:
    nomes_de_contexto = {fm.get("contexto", slug) for slug, _, fm in contextos.values()}
    slugs = set(contextos)

    for slug, caminho, fm in contextos.values():
        for chave in ("depende_de", "afeta"):
            for alvo in fm.get(chave) or []:
                if alvo not in nomes_de_contexto and alvo not in slugs:
                    erro(f"{_rel(caminho)}: `{chave}` aponta para '{alvo}', "
                         "que não é um contexto deste repo.")

        for rel in fm.get("compartilha_contrato_com") or []:
            alvo = rel.get("contexto")
            if alvo and alvo not in nomes_de_contexto and alvo not in slugs:
                erro(f"{_rel(caminho)}: `compartilha_contrato_com` aponta para "
                     f"'{alvo}', que não é um contexto deste repo.")

        pai = fm.get("dominio_pai")
        if pai and pai not in nomes_de_contexto and pai not in slugs:
            erro(f"{_rel(caminho)}: `dominio_pai: {pai}` não é um contexto deste repo.")

        realizado = fm.get("realizado_por") or []
        if not realizado:
            aviso(f"{_rel(caminho)}: sem `realizado_por` — nenhuma pergunta sobre este "
                  "contexto consegue chegar ao código.")
        for item in realizado:
            comp = item.get("componente")
            if comp not in componentes:
                erro(f"{_rel(caminho)}: `realizado_por` cita o componente '{comp}', "
                     f"que não tem doc em {load_config()['component_docs']}/.")


def validar_caminhos(contextos: dict, componentes: dict, offline: bool) -> None:
    """Confere que cada `caminho` existe dentro do código do componente."""
    try:
        rc = repo_cache()
    except BlueprintfyAusente as e:
        aviso(f"{e} Os `caminho` não foram conferidos contra o código.")
        return

    resolvidos: dict[str, object] = {}
    for slug, caminho_doc, fm in contextos.values():
        for item in fm.get("realizado_por") or []:
            comp = item.get("componente")
            sub = item.get("caminho")
            if not sub or comp not in componentes:
                continue

            if comp not in resolvidos:
                _, _, comp_fm = componentes[comp]
                resolvidos[comp] = rc.resolve(
                    comp, comp_fm, ROOT, rev="pin", allow_network=not offline
                )
                res = resolvidos[comp]
                if res.ok and res.source == "local" and res.revision != comp_fm.get("commit"):
                    aviso(f"{comp}: o clone local está em "
                          f"`{str(res.revision)[:12]}`, não no pin "
                          f"`{str(comp_fm.get('commit'))[:12]}` — os caminhos foram "
                          "conferidos contra o código local, não contra o pin.")
                elif res.stale:
                    aviso(f"{comp}: conferindo contra o cache em "
                          f"`{str(res.revision)[:12]}`, não no pin (sem rede).")

            res = resolvidos[comp]
            if not res.ok:
                aviso(f"{comp}: não consegui obter o código ({res.error}) — "
                      f"o caminho `{sub}` não foi conferido.")
                continue
            if not (Path(res.path) / sub).exists():
                erro(f"{_rel(caminho_doc)}: `caminho: {sub}` não existe em '{comp}' "
                     f"(conferido em {str(res.revision)[:12]}).")


def _irmao_com_outro_case(alvo: Path) -> str | None:
    """Nome de um irmão que só difere no case — sinal de typo, não de clone faltando."""
    alvo = Path(alvo)
    pai = alvo.parent
    if not pai.exists():
        return None
    for irmao in pai.iterdir():
        if irmao.name.lower() == alvo.name.lower() and irmao.name != alvo.name:
            try:
                return str(irmao.resolve().relative_to(ROOT))
            except ValueError:
                import os
                return os.path.relpath(irmao.resolve(), ROOT)
    return None


def _rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def main() -> int:
    offline = "--offline" in sys.argv

    mapa = ROOT / MAP_FILENAME
    if not mapa.exists():
        print(f"{MAP_FILENAME} não existe em {ROOT} — isto não é um context-repo.")
        return 1

    texto = mapa.read_text(encoding="utf-8")
    ctx_mapeados, comp_mapeados = validar_mapa(texto)

    contextos = {slug: (slug, p, fm) for slug, p, fm in iter_contexts()}
    componentes = {nome: (nome, p, fm) for nome, p, fm in iter_components()}

    validar_alcance(ctx_mapeados, [p for _, p, _ in contextos.values()], "CONTEXT.md")
    validar_alcance(comp_mapeados, [p for _, p, _ in componentes.values()], "Doc de componente")
    validar_componentes(componentes)
    validar_relacoes(contextos, componentes)
    validar_caminhos(contextos, componentes, offline)

    for a in avisos:
        print(f"  aviso: {a}")
    for e in erros:
        print(f"  ERRO:  {e}")

    total = f"{len(contextos)} contexto(s), {len(componentes)} componente(s)"
    if erros:
        print(f"\n{len(erros)} erro(s) de integridade referencial em {total}.")
        print("Corrija os elos acima — nada aqui é gerado, tudo é editável à mão.")
        return 1

    print(f"\nOK: {total} — todos os elos resolvem."
          + (f" ({len(avisos)} aviso(s))" if avisos else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
