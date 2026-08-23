#!/usr/bin/env python3
"""Testes do repo_cache.py (unittest da stdlib, sem dependências externas).

Nenhum teste toca a rede: os "remotes" são repositórios git de verdade criados em
tmpdir e servidos por `file://`, o que exercita os mesmos caminhos de código
(fetch raso, fallback, checkout) sem depender de internet.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "repo_cache", os.path.join(_HERE, "repo_cache.py")
)
rc = importlib.util.module_from_spec(_spec)
# Registrar antes de executar: `@dataclass` resolve anotações via sys.modules e
# quebra se o módulo ainda não estiver lá.
sys.modules[_spec.name] = rc
_spec.loader.exec_module(rc)


def _run(*args, cwd=None):
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
    )
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True, env=env
    )


def make_repo(path: Path, commits=2, any_sha=False) -> list[str]:
    """Cria um repo git com N commits; devolve os SHAs em ordem cronológica."""
    path.mkdir(parents=True, exist_ok=True)
    _run("git", "init", "-q", "-b", "main", str(path))
    if any_sha:
        # Permite `fetch origin <sha>` — exercita o caminho rápido do _fetch.
        _run("git", "-C", str(path), "config", "uploadpack.allowAnySHA1InWant", "true")
    shas = []
    for i in range(commits):
        (path / f"arquivo-{i}.txt").write_text(f"conteudo {i}\n", encoding="utf-8")
        _run("git", "-C", str(path), "add", ".")
        _run("git", "-C", str(path), "commit", "-q", "-m", f"commit {i}")
        shas.append(_run("git", "-C", str(path), "rev-parse", "HEAD").stdout.strip())
    return shas


class RevisionTest(unittest.TestCase):
    def test_pin_usa_commit(self):
        repo = {"commit": "aaa", "ultimo_visto": "bbb"}
        self.assertEqual(rc.target_revision(repo, "pin"), "aaa")

    def test_latest_usa_ultimo_visto(self):
        repo = {"commit": "aaa", "ultimo_visto": "bbb"}
        self.assertEqual(rc.target_revision(repo, "latest"), "bbb")

    def test_latest_cai_para_commit_sem_marca_dagua(self):
        self.assertEqual(rc.target_revision({"commit": "aaa"}, "latest"), "aaa")

    def test_rev_literal_passa_direto(self):
        self.assertEqual(rc.target_revision({"commit": "aaa"}, "v1.2.3"), "v1.2.3")

    def test_drift_e_a_divergencia_entre_pin_e_marca_dagua(self):
        self.assertTrue(rc.is_drifted({"commit": "aaa", "ultimo_visto": "bbb"}))
        self.assertFalse(rc.is_drifted({"commit": "aaa", "ultimo_visto": "aaa"}))
        self.assertFalse(rc.is_drifted({"commit": "aaa"}))


class ResolveLocalTest(unittest.TestCase):
    def test_local_existente_vence_e_nao_toca_a_rede(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "context-repo"
            root.mkdir()
            fonte = Path(tmp) / "core"
            shas = make_repo(fonte)

            res = rc.resolve(
                "core",
                {"local": "../core", "remote": "file:///inexistente", "commit": shas[0]},
                root,
                allow_network=False,
            )
            self.assertTrue(res.ok)
            self.assertEqual(res.source, "local")
            self.assertEqual(res.path, str(fonte.resolve()))
            self.assertEqual(res.revision, shas[-1])

    def test_sem_local_e_sem_remote_e_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = rc.resolve("core", {"local": "../sumiu"}, Path(tmp))
            self.assertFalse(res.ok)
            self.assertIn("remote", res.error)


class ResolveRemoteTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.root = tmp / "context-repo"
        self.root.mkdir()
        self.fonte = tmp / "origem"
        self.shas = make_repo(self.fonte, commits=3)
        self.remote = f"file://{self.fonte}"

    def tearDown(self):
        self._tmp.cleanup()

    def test_primeiro_encontro_clona_no_pin(self):
        res = rc.resolve(
            "core", {"remote": self.remote, "commit": self.shas[0]}, self.root
        )
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.source, "cache")
        self.assertEqual(res.revision, self.shas[0])
        self.assertTrue((Path(res.path) / "arquivo-0.txt").exists())
        self.assertFalse((Path(res.path) / "arquivo-2.txt").exists())

    def test_caminho_rapido_por_sha_quando_o_servidor_permite(self):
        fonte = Path(self._tmp.name) / "permissiva"
        shas = make_repo(fonte, commits=2, any_sha=True)
        res = rc.resolve(
            "permissiva", {"remote": f"file://{fonte}", "commit": shas[0]}, self.root
        )
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.revision, shas[0])

    def test_segunda_chamada_na_mesma_revisao_nao_toca_a_rede(self):
        repo = {"remote": self.remote, "commit": self.shas[0]}
        rc.resolve("core", repo, self.root)

        # Remove a origem: qualquer acesso à rede agora falharia.
        subprocess.run(["rm", "-rf", str(self.fonte)], check=True)

        res = rc.resolve("core", repo, self.root)
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.revision, self.shas[0])
        self.assertFalse(res.stale)
        self.assertTrue(any("sem rede" in linha.lower() for linha in res.logs))

    def test_troca_de_revisao_atualiza_o_cache(self):
        rc.resolve("core", {"remote": self.remote, "commit": self.shas[0]}, self.root)
        res = rc.resolve("core", {"remote": self.remote, "commit": self.shas[2]}, self.root)
        self.assertTrue(res.ok, res.error)
        self.assertEqual(res.revision, self.shas[2])
        self.assertTrue((Path(res.path) / "arquivo-2.txt").exists())

    def test_pin_e_latest_resolvem_revisoes_diferentes(self):
        repo = {"remote": self.remote, "commit": self.shas[0], "ultimo_visto": self.shas[2]}
        pin = rc.resolve("core", repo, self.root, rev="pin")
        self.assertEqual(pin.revision, self.shas[0])
        latest = rc.resolve("core", repo, self.root, rev="latest")
        self.assertEqual(latest.revision, self.shas[2])


class OfflineTest(unittest.TestCase):
    """O pre-commit do context-repo depende exatamente destas regras."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.root = tmp / "context-repo"
        self.root.mkdir()
        self.fonte = tmp / "origem"
        self.shas = make_repo(self.fonte, commits=2)
        self.remote = f"file://{self.fonte}"

    def tearDown(self):
        self._tmp.cleanup()

    def test_sem_rede_e_sem_cache_falha_com_instrucao(self):
        res = rc.resolve(
            "core", {"remote": self.remote, "commit": self.shas[0]}, self.root,
            allow_network=False,
        )
        self.assertFalse(res.ok)
        self.assertIn(".repo-cache", res.error)

    def test_sem_rede_com_cache_em_outra_revisao_devolve_stale(self):
        rc.resolve("core", {"remote": self.remote, "commit": self.shas[0]}, self.root)
        res = rc.resolve(
            "core", {"remote": self.remote, "commit": self.shas[1]}, self.root,
            allow_network=False,
        )
        self.assertTrue(res.ok)
        self.assertTrue(res.stale)
        self.assertEqual(res.revision, self.shas[0])

    def test_falha_de_rede_degrada_para_o_cache_marcado_como_stale(self):
        rc.resolve("core", {"remote": self.remote, "commit": self.shas[0]}, self.root)
        subprocess.run(["rm", "-rf", str(self.fonte)], check=True)

        res = rc.resolve(
            "core", {"remote": self.remote, "commit": self.shas[1]}, self.root
        )
        self.assertTrue(res.ok)
        self.assertTrue(res.stale)
        self.assertEqual(res.revision, self.shas[0])

    def test_cache_ausente_reportado_por_cached_revision(self):
        self.assertIsNone(rc.cached_revision("nunca-baixado", self.root))


if __name__ == "__main__":
    unittest.main()
