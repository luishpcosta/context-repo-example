#!/usr/bin/env python3
"""Grafo de dependências do modelo de domínio, derivado do front matter.

O grafo NÃO é fonte de verdade: ele é reconstruído em memória a cada execução a
partir do front matter dos documentos alcançáveis pelo `CONTEXT-MAP.md` da raiz
(CONTEXT.md de cada contexto + ADRs). A saída é markdown já-digerido para o agente
consumir — o agente delega a travessia a esta ferramenta em vez de reler todas as
ADRs à mão.

Nós:   `contexto:<Nome>`, `adr:<ID>`, `pb:<ID>`, `prd:<ID>`, `contrato:<Nome>`
Arestas: depende_de, supera, afeta, compartilha_contrato

Uso:
    graph_query.py impacto <no> [--saltos N] [--map CAMINHO]
        BFS de N saltos a partir de um nó; lista o que é afetado.
    graph_query.py vigentes <contexto> [--map CAMINHO]
        ADRs/PBs/PRDs vigentes (não-superados) x superados que tocam o contexto.
    graph_query.py valida-aresta <de> <para> [--contrato X] [--map CAMINHO]
        Verifica se a aresta proposta existe na topologia declarada (query "viola").
    graph_query.py ciclos [--map CAMINHO]
        Detecta ciclos em `depende_de` entre contextos.

`<no>` aceita `contexto:Ordering`, `adr:ADR-...`, `pb:PB-...`, `prd:PRD-...`, ou o
nome curto — IDs `ADR-`/`PB-`/`PRD-` têm o tipo inferido; o resto assume contexto.
Stdlib-only: nenhuma dependência externa. Sem Python, o agente navega à mão (fallback).
"""
import argparse
import os
import re
import sys
from collections import defaultdict


# --------------------------------------------------------------------------- #
# Parser de front matter (subconjunto de YAML — listas planas e listas de maps)
# --------------------------------------------------------------------------- #

def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _strip_comment(s):
    """Remove um comentário ` # ...` fora de colchetes/chaves."""
    depth = 0
    for idx, ch in enumerate(s):
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "#" and depth == 0 and (idx == 0 or s[idx - 1] == " "):
            return s[:idx]
    return s


def _split_top(s):
    """Divide por vírgula no nível superior (ignora vírgulas dentro de [] ou {})."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _parse_scalar(s):
    return s.strip().strip('"').strip("'")


def _parse_value(s):
    s = s.strip()
    if s.startswith("["):
        return _parse_inline_list(s)
    if s.startswith("{"):
        return _parse_inline_map(s)
    return _parse_scalar(s)


def _parse_inline_list(s):
    inner = s.strip()[1:-1].strip()
    if not inner:
        return []
    return [_parse_value(p.strip()) for p in _split_top(inner)]


def _parse_inline_map(s):
    inner = s.strip().lstrip("{").rstrip("}")
    d = {}
    for part in _split_top(inner):
        if ":" in part:
            k, _, v = part.partition(":")
            d[k.strip()] = _parse_value(v.strip())
    return d


def _frontmatter_lines(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        out.append(line)
    return out


def _next_meaningful(lines, i):
    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("#")):
        i += 1
    return i


def _parse_map(lines, i, indent):
    d = {}
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue
        cur = _indent(raw)
        if cur != indent:
            break
        key, _, val = raw.strip().partition(":")
        key = key.strip()
        val = _strip_comment(val).strip()
        if val:
            d[key] = _parse_value(val)
            i += 1
            continue
        # valor vazio: bloco (lista ou map) indentado abaixo
        j = _next_meaningful(lines, i + 1)
        if j < len(lines) and _indent(lines[j]) > indent and lines[j].strip().startswith("-"):
            d[key], i = _parse_list(lines, j, _indent(lines[j]))
        elif j < len(lines) and _indent(lines[j]) > indent:
            d[key], i = _parse_map(lines, j, _indent(lines[j]))
        else:
            d[key] = None
            i += 1
    return d, i


def _parse_list(lines, i, indent):
    items = []
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue
        cur = _indent(raw)
        if cur < indent or not raw.strip().startswith("-"):
            break
        after = _strip_comment(raw.strip()[1:].strip())
        if after.startswith("{"):
            items.append(_parse_inline_map(after))
            i += 1
        elif ":" in after and not after.startswith("["):
            item = {}
            k, _, v = after.partition(":")
            item[k.strip()] = _parse_value(v.strip()) if v.strip() else None
            i += 1
            while i < len(lines):
                r2 = lines[i]
                if not r2.strip() or r2.strip().startswith("#"):
                    i += 1
                    continue
                if _indent(r2) <= cur or r2.strip().startswith("-"):
                    break
                k2, _, v2 = r2.strip().partition(":")
                item[k2.strip()] = _parse_value(_strip_comment(v2).strip())
                i += 1
            items.append(item)
        else:
            items.append(_parse_value(after))
            i += 1
    return items, i


def parse_frontmatter(text):
    """Retorna o dict de front matter (vazio se não houver)."""
    lines = _frontmatter_lines(text)
    if not lines:
        return {}
    result, _ = _parse_map(lines, 0, 0)
    return result


# --------------------------------------------------------------------------- #
# Grafo
# --------------------------------------------------------------------------- #

def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _as_scalar(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


LINK_RE = re.compile(r"\]\(([^)]+)\)")


def extract_links(md_text):
    """Caminhos referenciados por links markdown, sem âncoras nem URLs externas."""
    out = []
    for m in LINK_RE.finditer(md_text):
        link = m.group(1).split("#")[0].strip()
        if link and not link.startswith(("http://", "https://", "mailto:")):
            out.append(link)
    return out


def reachable_docs(map_path):
    """Documentos `.md` alcançáveis a partir do CONTEXT-MAP.md (mapa = ponto de entrada)."""
    base = os.path.dirname(os.path.abspath(map_path))
    docs, seen = [], set()

    def add(fp):
        fp = os.path.normpath(fp)
        if fp not in seen and fp != os.path.abspath(map_path):
            seen.add(fp)
            docs.append(fp)

    for link in extract_links(_read(map_path)):
        p = os.path.normpath(os.path.join(base, link))
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in sorted(files):
                    if f.endswith(".md"):
                        add(os.path.join(root, f))
        elif os.path.isfile(p):
            add(p)
    return docs


class Graph:
    def __init__(self):
        self.nodes = {}          # id -> {status, superado_por, titulo, path, fm}
        self.out = defaultdict(list)   # id -> [(kind, target, extra)]
        self.inb = defaultdict(list)   # id -> [(kind, source, extra)]
        self.reachable_total = 0       # docs alcançáveis pelo mapa
        self.with_frontmatter = 0      # docs que renderam um nó (tinham front matter)

    def node(self, nid):
        return self.nodes.setdefault(
            nid, {"status": None, "superado_por": [], "titulo": None, "path": None, "fm": {}}
        )

    def add_edge(self, src, kind, tgt, extra=None):
        self.out[src].append((kind, tgt, extra))
        self.inb[tgt].append((kind, src, extra))
        self.node(tgt)


def _id_type(raw):
    """Tipo de nó inferido do prefixo do ID (convenção PB-/PRD-/ADR-...)."""
    if raw.startswith("PB-"):
        return "pb"
    if raw.startswith("PRD-"):
        return "prd"
    return "adr"


def _node_id(fm):
    if fm.get("id"):
        raw = _as_scalar(fm["id"])
        return _id_type(raw) + ":" + raw
    if fm.get("contexto"):
        return "contexto:" + _as_scalar(fm["contexto"])
    return None


def _norm_target(tgt, source_id):
    if tgt.startswith(("ADR-", "PB-", "PRD-")):
        return _id_type(tgt) + ":" + tgt
    return ("adr:" if source_id.startswith("adr:") else "contexto:") + tgt


def build_graph(map_path):
    g = Graph()
    for doc in reachable_docs(map_path):
        g.reachable_total += 1
        fm = parse_frontmatter(_read(doc))
        nid = _node_id(fm)
        if nid is None:
            continue
        g.with_frontmatter += 1
        node = g.node(nid)
        node["fm"] = fm
        node["path"] = doc
        node["status"] = _as_scalar(fm.get("status"))
        node["titulo"] = _as_scalar(fm.get("titulo"))   # None p/ contexto → _label mostra só o nome
        for tgt in _as_list(fm.get("depende_de")):
            g.add_edge(nid, "depende_de", _norm_target(tgt, nid))
        for tgt in _as_list(fm.get("supera")):
            g.add_edge(nid, "supera", _id_type(tgt) + ":" + tgt)
        for tgt in _as_list(fm.get("afeta")):
            g.add_edge(nid, "afeta", "contexto:" + tgt)
        for c in _as_list(fm.get("compartilha_contrato_com")):
            if isinstance(c, dict) and c.get("contexto"):
                g.add_edge(nid, "compartilha_contrato", "contexto:" + c["contexto"], c.get("contrato"))
    derive_supersession(g)
    return g


def derive_supersession(g):
    """Marca como `superado` todo doc alvo de uma aresta `supera` — sem editar o doc antigo."""
    for src, edges in list(g.out.items()):
        for kind, tgt, _extra in edges:
            if kind == "supera":
                node = g.node(tgt)
                node["status"] = "superado"
                if src not in node["superado_por"]:
                    node["superado_por"].append(src)


# --------------------------------------------------------------------------- #
# Consultas
# --------------------------------------------------------------------------- #

def empty_graph_warning(g):
    """Aviso quando o grafo não tem front matter (repo brownfield) — evita ler '(nenhuma)'
    como 'sem tensões'. Retorna '' quando há ao menos um doc com front matter."""
    if g.with_frontmatter == 0 and g.reachable_total > 0:
        return (
            f"⚠ Nenhum dos {g.reachable_total} documento(s) alcançável(is) pelo mapa tem "
            "front matter de relação — o grafo está vazio.\n"
            "Provavelmente os docs precedem o front matter (repo brownfield). NÃO conclua "
            "'sem tensões' a partir daqui: faça o backfill (contextos/afeta/supera) ou a "
            "travessia à mão lendo as ADRs.\n"
        )
    return ""


def _with_banner(g, body):
    warn = empty_graph_warning(g)
    return (warn + "\n" + body) if warn else body


def _short(nid):
    return nid.split(":", 1)[1] if ":" in nid else nid


def _label(g, nid):
    node = g.nodes.get(nid, {})
    titulo = node.get("titulo")
    return f"{_short(nid)} — {titulo}" if titulo else _short(nid)


def _doc_contexts(fm):
    ctxs = set()
    for x in _as_list(fm.get("contextos")):
        ctxs.add("contexto:" + x)
    for x in _as_list(fm.get("afeta")):
        ctxs.add("contexto:" + x)
    return ctxs


def _type_tag(nid):
    return "[" + nid.split(":", 1)[0].upper() + "] "


def cmd_vigentes(g, contexto):
    vig, sup = [], []
    for nid, node in g.nodes.items():
        if nid.split(":", 1)[0] not in ("adr", "pb", "prd"):
            continue
        if contexto in _doc_contexts(node.get("fm", {})):
            (sup if node.get("status") == "superado" else vig).append(nid)
    lines = [f"Decisões e docs de produto que tocam {_short(contexto)}:", ""]
    lines.append("VIGENTES:")
    if vig:
        for nid in sorted(vig):
            node = g.nodes[nid]
            lines.append(f"- {_type_tag(nid)}{_label(g, nid)} [{node.get('status') or 'sem status'}]")
            for _k, tgt, _e in g.out.get(nid, []):
                if _k == "supera":
                    lines.append(f"    ⚠ SUPERA {_short(tgt)} — não usar a premissa antiga.")
    else:
        lines.append("- (nenhuma)")
    lines.append("")
    lines.append("SUPERADAS (não usar como premissa):")
    if sup:
        for nid in sorted(sup):
            por = ", ".join(_short(x) for x in g.nodes[nid]["superado_por"])
            lines.append(f"- {_type_tag(nid)}{_label(g, nid)}  [superado_por {por}]")
    else:
        lines.append("- (nenhuma)")
    return "\n".join(lines)


def cmd_impacto(g, start, saltos=2):
    if start not in g.nodes:
        return f"Nó '{_short(start)}' não encontrado no grafo (nada alcançável no mapa o referencia)."
    seen = {start}
    frontier = [(start, 0)]
    reached = []
    while frontier:
        n, d = frontier.pop(0)
        if d >= saltos:
            continue
        neighbors = [(k, t, e) for (k, t, e) in g.out.get(n, [])]
        neighbors += [(k, s, e) for (k, s, e) in g.inb.get(n, [])]
        for kind, tgt, extra in neighbors:
            if tgt not in seen:
                seen.add(tgt)
                frontier.append((tgt, d + 1))
                reached.append((kind, tgt, extra, d + 1))
    lines = [f"Impacto de {_short(start)} ({saltos} salto(s)):", ""]
    if not reached:
        lines.append("- Nada alcançável (nó isolado no grafo).")
        return "\n".join(lines)
    for kind, tgt, extra, dist in reached:
        node = g.nodes.get(tgt, {})
        suf = f" ({extra})" if extra else ""
        flag = "  ⚠ SUPERADA" if node.get("status") == "superado" else ""
        lines.append(f"- [{kind}{suf}] {_label(g, tgt)}{flag}")
    return "\n".join(lines)


def cmd_valida_aresta(g, de, para, contrato=None):
    for kind, tgt, extra in g.out.get(de, []):
        if tgt == para and kind in ("depende_de", "compartilha_contrato"):
            if contrato and kind == "compartilha_contrato" and extra != contrato:
                continue
            via = f" (via {kind}{', contrato ' + extra if extra else ''})"
            return f"OK: aresta {_short(de)} → {_short(para)} existe na topologia declarada{via}."
    return (
        f"VIOLAÇÃO: {_short(de)} → {_short(para)} não está na topologia declarada.\n"
        f"Nenhuma aresta `depende_de`/`compartilha_contrato` liga esses contextos"
        + (f" com contrato '{contrato}'" if contrato else "")
        + ".\nSe a dependência é legítima, declare-a no front matter do CONTEXT.md; "
        "senão, é acoplamento furando o bounded context."
    )


def cmd_ciclos(g):
    adj = defaultdict(list)
    for src, edges in g.out.items():
        for kind, tgt, _e in edges:
            if kind == "depende_de":
                adj[src].append(tgt)
    color = {}
    cycles = []

    def dfs(node, stack):
        color[node] = "gray"
        stack.append(node)
        for nxt in adj.get(node, []):
            if color.get(nxt) == "gray":
                idx = stack.index(nxt)
                cycles.append(stack[idx:] + [nxt])
            elif color.get(nxt) != "black":
                dfs(nxt, stack)
        stack.pop()
        color[node] = "black"

    for node in list(adj.keys()):
        if color.get(node) != "black":
            dfs(node, [])
    if not cycles:
        return "Nenhum ciclo de `depende_de` entre contextos."
    lines = ["Ciclos de dependência detectados (cheiro de acoplamento):"]
    for cyc in cycles:
        lines.append("- " + " → ".join(_short(n) for n in cyc))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def normalize_node_arg(s):
    if ":" in s and s.split(":", 1)[0] in ("contexto", "adr", "pb", "prd", "contrato"):
        return s
    if s.startswith(("ADR-", "PB-", "PRD-")):
        return _id_type(s) + ":" + s
    return "contexto:" + s


def _default_map(cli_map):
    return cli_map or os.path.join(os.getcwd(), "CONTEXT-MAP.md")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Grafo de dependências derivado do front matter.")
    parser.add_argument("--map", help="Caminho do CONTEXT-MAP.md (default: ./CONTEXT-MAP.md)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_imp = sub.add_parser("impacto")
    p_imp.add_argument("no")
    p_imp.add_argument("--saltos", type=int, default=2)

    p_vig = sub.add_parser("vigentes")
    p_vig.add_argument("contexto")

    p_val = sub.add_parser("valida-aresta")
    p_val.add_argument("de")
    p_val.add_argument("para")
    p_val.add_argument("--contrato")

    sub.add_parser("ciclos")

    args = parser.parse_args(argv)
    map_path = _default_map(args.map)
    if not os.path.isfile(map_path):
        print(f"CONTEXT-MAP.md não encontrado em {map_path}. Rode na raiz do repo ou use --map.",
              file=sys.stderr)
        return 2

    g = build_graph(map_path)
    if args.cmd == "impacto":
        body = cmd_impacto(g, normalize_node_arg(args.no), args.saltos)
    elif args.cmd == "vigentes":
        body = cmd_vigentes(g, normalize_node_arg(args.contexto))
    elif args.cmd == "valida-aresta":
        body = cmd_valida_aresta(g, normalize_node_arg(args.de), normalize_node_arg(args.para), args.contrato)
    else:  # ciclos
        body = cmd_ciclos(g)
    print(_with_banner(g, body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
