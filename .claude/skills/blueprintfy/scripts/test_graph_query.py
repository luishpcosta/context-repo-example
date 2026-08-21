#!/usr/bin/env python3
"""Testes do graph_query.py (unittest da stdlib, sem dependências externas)."""

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "graph_query", os.path.join(_HERE, "graph_query.py")
)
gq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gq)


# --------------------------------------------------------------------------- #
# Front matter
# --------------------------------------------------------------------------- #

class FrontmatterTest(unittest.TestCase):
    def test_no_frontmatter(self):
        self.assertEqual(gq.parse_frontmatter("# Só markdown\ntexto"), {})

    def test_scalars_and_inline_list(self):
        fm = gq.parse_frontmatter(
            "---\n"
            "id: ADR-1\n"
            "status: aceito   # proposto | aceito | superado\n"
            "afeta: [Payment, Ordering]\n"
            "---\n"
            "corpo\n"
        )
        self.assertEqual(fm["id"], "ADR-1")
        self.assertEqual(fm["status"], "aceito")
        self.assertEqual(fm["afeta"], ["Payment", "Ordering"])

    def test_empty_inline_list(self):
        fm = gq.parse_frontmatter("---\nsupera: []\n---\n")
        self.assertEqual(fm["supera"], [])

    def test_block_list_of_maps(self):
        fm = gq.parse_frontmatter(
            "---\n"
            "contexto: Payment\n"
            "compartilha_contrato_com:\n"
            "  - contexto: Ordering\n"
            "    contrato: PedidoCancelado\n"
            "---\n"
        )
        self.assertEqual(fm["contexto"], "Payment")
        self.assertEqual(
            fm["compartilha_contrato_com"],
            [{"contexto": "Ordering", "contrato": "PedidoCancelado"}],
        )

    def test_inline_map_in_list(self):
        fm = gq.parse_frontmatter(
            "---\ncompartilha_contrato_com:\n  - { contexto: Ordering, contrato: X }\n---\n"
        )
        self.assertEqual(
            fm["compartilha_contrato_com"], [{"contexto": "Ordering", "contrato": "X"}]
        )


class LinkExtractionTest(unittest.TestCase):
    def test_ignores_external_and_anchors(self):
        md = "[a](./x/CONTEXT.md) [b](https://ex.com) [c](./adr/#sec)"
        self.assertEqual(gq.extract_links(md), ["./x/CONTEXT.md", "./adr/"])


# --------------------------------------------------------------------------- #
# Grafo (fixtures em disco)
# --------------------------------------------------------------------------- #

def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class GraphFixture(unittest.TestCase):
    """Repo com Ordering/Payment e duas ADRs onde a 20250620 supera a 20250115."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _write(
            os.path.join(self.tmp, "CONTEXT-MAP.md"),
            "# Context Map\n\n## Contextos\n"
            "- [Ordering](./docs/ordering/CONTEXT.md) — pedidos\n"
            "- [Payment](./docs/payment/CONTEXT.md) — pagamentos\n\n"
            "## Decisões (ADR)\n- [Registro](./adr/)\n",
        )
        _write(
            os.path.join(self.tmp, "docs/ordering/CONTEXT.md"),
            "---\ncontexto: Ordering\ndepende_de: []\n"
            "compartilha_contrato_com:\n  - contexto: Payment\n    contrato: PedidoCancelado\n"
            "---\n# Ordering\n",
        )
        _write(
            os.path.join(self.tmp, "docs/payment/CONTEXT.md"),
            "---\ncontexto: Payment\ndepende_de: [Identity]\n---\n# Payment\n",
        )
        _write(
            os.path.join(self.tmp, "adr/ADR-20250115-1030-7a2c-estorno-sincrono.md"),
            "---\nid: ADR-20250115-1030-7a2c\ntitulo: Estorno síncrono\n"
            "status: aceito\ncontextos: [Ordering]\nafeta: [Ordering, Payment]\n---\n# ADR\n",
        )
        _write(
            os.path.join(self.tmp, "adr/ADR-20250620-1542-3f0a-fila-assincrona.md"),
            "---\nid: ADR-20250620-1542-3f0a\ntitulo: Fila assíncrona para estornos\n"
            "status: aceito\ncontextos: [Payment]\nafeta: [Payment, Ordering]\n"
            "supera: [ADR-20250115-1030-7a2c]\n---\n# ADR\n",
        )
        self.map = os.path.join(self.tmp, "CONTEXT-MAP.md")
        self.g = gq.build_graph(self.map)

    def test_reachable_docs_finds_all(self):
        docs = gq.reachable_docs(self.map)
        self.assertEqual(len(docs), 4)  # 2 CONTEXT.md + 2 ADRs (dir adr/ varrido)

    def test_nodes_built(self):
        self.assertIn("contexto:Ordering", self.g.nodes)
        self.assertIn("adr:ADR-20250620-1542-3f0a", self.g.nodes)

    def test_supersession_derived(self):
        antiga = self.g.nodes["adr:ADR-20250115-1030-7a2c"]
        self.assertEqual(antiga["status"], "superado")
        self.assertIn("adr:ADR-20250620-1542-3f0a", antiga["superado_por"])

    def test_vigentes_splits_current_and_superseded(self):
        out = gq.cmd_vigentes(self.g, "contexto:Ordering")
        self.assertIn("VIGENTES:", out)
        self.assertIn("Fila assíncrona", out)      # a nova é vigente
        self.assertIn("SUPERA ADR-20250115-1030-7a2c", out)
        # a antiga aparece na seção de superadas
        sup_section = out.split("SUPERADAS")[1]
        self.assertIn("Estorno síncrono", sup_section)

    def test_impacto_reaches_related_nodes(self):
        out = gq.cmd_impacto(self.g, "contexto:Ordering", saltos=2)
        self.assertIn("Payment", out)
        self.assertIn("ADR-20250620-1542-3f0a", out)   # alcança ADRs também
        self.assertIn("⚠ SUPERADA", out)               # sinaliza a ADR superada alcançada

    def test_impacto_unknown_node(self):
        out = gq.cmd_impacto(self.g, "contexto:Inexistente")
        self.assertIn("não encontrado", out)

    def test_valida_aresta_ok(self):
        out = gq.cmd_valida_aresta(self.g, "contexto:Ordering", "contexto:Payment")
        self.assertTrue(out.startswith("OK"))

    def test_valida_aresta_ok_with_contract(self):
        out = gq.cmd_valida_aresta(
            self.g, "contexto:Ordering", "contexto:Payment", contrato="PedidoCancelado"
        )
        self.assertTrue(out.startswith("OK"))

    def test_valida_aresta_violation(self):
        out = gq.cmd_valida_aresta(self.g, "contexto:Payment", "contexto:Ordering")
        self.assertIn("VIOLAÇÃO", out)

    def test_valida_aresta_wrong_contract_is_violation(self):
        out = gq.cmd_valida_aresta(
            self.g, "contexto:Ordering", "contexto:Payment", contrato="Outro"
        )
        self.assertIn("VIOLAÇÃO", out)

    def test_no_cycles(self):
        self.assertIn("Nenhum ciclo", gq.cmd_ciclos(self.g))


class CycleTest(unittest.TestCase):
    def test_cycle_detected(self):
        tmp = tempfile.mkdtemp()
        _write(
            os.path.join(tmp, "CONTEXT-MAP.md"),
            "## Contextos\n- [A](./a/CONTEXT.md)\n- [B](./b/CONTEXT.md)\n",
        )
        _write(os.path.join(tmp, "a/CONTEXT.md"), "---\ncontexto: A\ndepende_de: [B]\n---\n")
        _write(os.path.join(tmp, "b/CONTEXT.md"), "---\ncontexto: B\ndepende_de: [A]\n---\n")
        g = gq.build_graph(os.path.join(tmp, "CONTEXT-MAP.md"))
        out = gq.cmd_ciclos(g)
        self.assertIn("Ciclos de dependência", out)
        self.assertIn("A", out)
        self.assertIn("B", out)


class BrownfieldTest(unittest.TestCase):
    """Docs existentes SEM front matter → grafo vazio deve avisar, não fingir 'sem tensões'."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _write(
            os.path.join(self.tmp, "CONTEXT-MAP.md"),
            "## Contextos\n- [Ordering](./o/CONTEXT.md)\n## Decisões\n- [adr](./adr/)\n",
        )
        _write(os.path.join(self.tmp, "o/CONTEXT.md"), "# Ordering\nsem front matter\n")
        _write(
            os.path.join(self.tmp, "adr/ADR-velha.md"),
            "# ADR-velha: decisão antiga\n\n- **Status**: Aceito\n",
        )
        self.map = os.path.join(self.tmp, "CONTEXT-MAP.md")
        self.g = gq.build_graph(self.map)

    def test_counts_reachable_but_no_frontmatter(self):
        self.assertEqual(self.g.reachable_total, 2)
        self.assertEqual(self.g.with_frontmatter, 0)

    def test_warning_present(self):
        warn = gq.empty_graph_warning(self.g)
        self.assertIn("brownfield", warn)
        self.assertIn("backfill", warn)

    def test_no_warning_when_frontmatter_exists(self):
        g = GraphFixture()
        g.setUp()
        self.assertEqual(gq.empty_graph_warning(g.g), "")

    def test_main_prepends_warning_on_brownfield(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = gq.main(["--map", self.map, "vigentes", "Ordering"])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("grafo está vazio", out)
        self.assertIn("(nenhuma)", out)   # o corpo ainda vem, mas precedido do aviso


class PbPrdFixtureTest(unittest.TestCase):
    """Repo com PB/PRDs no planejamento to-be: nós pb:/prd: derivados do prefixo do id."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _write(
            os.path.join(self.tmp, "CONTEXT-MAP.md"),
            "# Context Map\n\n## Contextos\n"
            "- [Ordering](./docs/ordering/CONTEXT.md) — pedidos\n"
            "- [Payment](./docs/payment/CONTEXT.md) — pagamentos\n\n"
            "## Decisões (ADR)\n- [Registro](./adr/)\n\n"
            "## Planejamento (to-be)\n- [Refinamento](./docs/refinamento/)\n",
        )
        _write(
            os.path.join(self.tmp, "docs/ordering/CONTEXT.md"),
            "---\ncontexto: Ordering\n---\n# Ordering\n",
        )
        _write(
            os.path.join(self.tmp, "docs/payment/CONTEXT.md"),
            "---\ncontexto: Payment\n---\n# Payment\n",
        )
        _write(
            os.path.join(self.tmp, "adr/ADR-20250620-1542-3f0a-fila-assincrona.md"),
            "---\nid: ADR-20250620-1542-3f0a\ntitulo: Fila assíncrona para estornos\n"
            "status: aceito\ncontextos: [Payment]\nafeta: [Payment, Ordering]\n---\n# ADR\n",
        )
        _write(
            os.path.join(self.tmp, "docs/refinamento/ordering/reembolso/PRODUCT_BRIEF.md"),
            "---\nid: PB-20260708-0900-aa01\ntitulo: Reembolso instantâneo\n"
            "status: rascunho\ncontextos: [Ordering]\nafeta: [Payment]\n"
            "supera: [PB-20260101-0800-ff00]\n---\n# Briefing de produto: Reembolso\n",
        )
        _write(
            os.path.join(self.tmp, "docs/refinamento/ordering/reembolso-v0/PRODUCT_BRIEF.md"),
            "---\nid: PB-20260101-0800-ff00\ntitulo: Reembolso (v0)\n"
            "status: aprovado\ncontextos: [Ordering]\n---\n# Briefing antigo\n",
        )
        _write(
            os.path.join(self.tmp, "docs/refinamento/ordering/reembolso/001-solicitacao-PRD.md"),
            "---\nid: PRD-20260708-0910-bb02\ntitulo: Solicitação de reembolso\n"
            "status: rascunho\ncontextos: [Ordering]\nafeta: [Payment]\n"
            "depende_de: [PB-20260708-0900-aa01]\n---\n# PRD 1\n",
        )
        _write(
            os.path.join(self.tmp, "docs/refinamento/ordering/reembolso/002-notificacao-PRD.md"),
            "---\nid: PRD-20260708-0920-cc03\ntitulo: Notificação de reembolso\n"
            "status: rascunho\ncontextos: [Ordering]\n"
            "depende_de: [PRD-20260708-0910-bb02]\n---\n# PRD 2\n",
        )
        self.map = os.path.join(self.tmp, "CONTEXT-MAP.md")
        self.g = gq.build_graph(self.map)

    def test_pb_node_classified_as_pb(self):
        self.assertIn("pb:PB-20260708-0900-aa01", self.g.nodes)
        self.assertNotIn("adr:PB-20260708-0900-aa01", self.g.nodes)

    def test_prd_node_classified_as_prd(self):
        self.assertIn("prd:PRD-20260708-0910-bb02", self.g.nodes)
        self.assertNotIn("adr:PRD-20260708-0910-bb02", self.g.nodes)

    def test_prd_depende_de_pb_edge(self):
        edges = self.g.out["prd:PRD-20260708-0910-bb02"]
        self.assertIn(("depende_de", "pb:PB-20260708-0900-aa01", None), edges)

    def test_prd_depende_de_prd_edge(self):
        edges = self.g.out["prd:PRD-20260708-0920-cc03"]
        self.assertIn(("depende_de", "prd:PRD-20260708-0910-bb02", None), edges)

    def test_pb_supera_pb_derived(self):
        antigo = self.g.nodes["pb:PB-20260101-0800-ff00"]
        self.assertEqual(antigo["status"], "superado")
        self.assertIn("pb:PB-20260708-0900-aa01", antigo["superado_por"])

    def test_vigentes_lists_pb_and_prd_with_labels(self):
        out = gq.cmd_vigentes(self.g, "contexto:Ordering")
        self.assertIn("[PB] PB-20260708-0900-aa01 — Reembolso instantâneo", out)
        self.assertIn("[PRD] PRD-20260708-0910-bb02 — Solicitação de reembolso", out)
        self.assertIn("[ADR] ADR-20250620-1542-3f0a — Fila assíncrona para estornos", out)
        sup_section = out.split("SUPERADAS")[1]
        self.assertIn("[PB] PB-20260101-0800-ff00 — Reembolso (v0)", sup_section)

    def test_impacto_reaches_prd_from_context(self):
        out = gq.cmd_impacto(self.g, "contexto:Payment", saltos=2)
        self.assertIn("PB-20260708-0900-aa01", out)
        self.assertIn("PRD-20260708-0910-bb02", out)

    def test_normalize_pb_prd_args(self):
        self.assertEqual(gq.normalize_node_arg("PB-1"), "pb:PB-1")
        self.assertEqual(gq.normalize_node_arg("PRD-1"), "prd:PRD-1")
        self.assertEqual(gq.normalize_node_arg("ADR-1"), "adr:ADR-1")
        self.assertEqual(gq.normalize_node_arg("pb:PB-1"), "pb:PB-1")
        self.assertEqual(gq.normalize_node_arg("prd:PRD-1"), "prd:PRD-1")
        self.assertEqual(gq.normalize_node_arg("Ordering"), "contexto:Ordering")


class CliTest(unittest.TestCase):
    def test_normalize_node_arg(self):
        self.assertEqual(gq.normalize_node_arg("Ordering"), "contexto:Ordering")
        self.assertEqual(gq.normalize_node_arg("adr:ADR-1"), "adr:ADR-1")

    def test_main_missing_map_returns_2(self):
        tmp = tempfile.mkdtemp()
        rc = gq.main(["--map", os.path.join(tmp, "nope.md"), "ciclos"])
        self.assertEqual(rc, 2)

    def test_main_vigentes_runs(self):
        tmp = tempfile.mkdtemp()
        _write(
            os.path.join(tmp, "CONTEXT-MAP.md"),
            "## Contextos\n- [Ordering](./o/CONTEXT.md)\n## ADR\n- [adr](./adr/)\n",
        )
        _write(os.path.join(tmp, "o/CONTEXT.md"), "---\ncontexto: Ordering\n---\n")
        _write(
            os.path.join(tmp, "adr/ADR-1.md"),
            "---\nid: ADR-1\ntitulo: T\nstatus: aceito\ncontextos: [Ordering]\n---\n",
        )
        rc = gq.main(["--map", os.path.join(tmp, "CONTEXT-MAP.md"), "vigentes", "Ordering"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
