import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estruturas import (ArvoreAVL, FilaPrioridade, TabelaHash, Trie,
                        GrafoDependencias, kmp_buscar, levenshtein, normalizar)
from gerenciador import GerenciadorTarefas, ErroTarefa


class TestAVL(unittest.TestCase):
    def test_balanceamento_sequencial(self):
        a = ArvoreAVL()
        for i in range(1000):
            a.inserir(i, i)
        self.assertTrue(a.esta_balanceada())
        self.assertLessEqual(a.altura(), 11)  # ~1.44*log2(1000)

    def test_aleatorio_insercao_remocao(self):
        random.seed(1)
        a, ref = ArvoreAVL(), set()
        for _ in range(2000):
            k = random.randint(0, 300)
            if random.random() < 0.6:
                a.inserir(k, k)
                ref.add(k)
            else:
                self.assertEqual(a.remover(k), k in ref)
                ref.discard(k)
            self.assertEqual(len(a), len(ref))
        self.assertTrue(a.esta_balanceada())
        self.assertEqual([k for k, _ in a.em_ordem()], sorted(ref))

    def test_intervalo(self):
        a = ArvoreAVL()
        for k in [5, 1, 9, 3, 7]:
            a.inserir(k, k)
        self.assertEqual([k for k, _ in a.intervalo(3, 7)], [3, 5, 7])


class TestHeap(unittest.TestCase):
    def test_ordem_e_atualizacao(self):
        h = FilaPrioridade()
        for item, p in [("a", 5), ("b", 1), ("c", 3)]:
            h.inserir(item, p)
        h.atualizar("a", 0)
        h.remover("c")
        self.assertEqual(h.ordenado(), ["a", "b"])
        self.assertEqual(h.extrair(), "a")
        self.assertEqual(len(h), 1)

    def test_heap_sort_aleatorio(self):
        random.seed(2)
        h, valores = FilaPrioridade(), list(range(200))
        random.shuffle(valores)
        for v in valores:
            h.inserir(v, v)
        self.assertEqual(h.ordenado(), sorted(valores))


class TestHash(unittest.TestCase):
    def test_basico_e_resize(self):
        t = TabelaHash(2)
        for i in range(500):
            t.colocar(i, i * 2)
        self.assertEqual(len(t), 500)
        self.assertEqual(t.obter(123), 246)
        self.assertLessEqual(t.fator_de_carga(), 0.75)
        t.colocar(123, "x")
        self.assertEqual(t.obter(123), "x")
        self.assertTrue(t.remover(123))
        self.assertNotIn(123, t)
        self.assertFalse(t.remover(123))


class TestTrie(unittest.TestCase):
    def test_prefixo_e_remocao(self):
        t = Trie()
        t.inserir("casa", 1)
        t.inserir("caso", 2)
        t.inserir("cama", 3)
        palavras, ids = t.buscar_prefixo("cas")
        self.assertEqual(palavras, ["casa", "caso"])
        self.assertEqual(ids, {1, 2})
        t.remover("casa", 1)
        self.assertEqual(t.buscar_prefixo("cas")[0], ["caso"])
        self.assertEqual(t.buscar_prefixo("x"), ([], set()))


class TestGrafo(unittest.TestCase):
    def test_topologica_ciclo_e_critico(self):
        g = GrafoDependencias()
        for a, b in [(1, 2), (2, 3), (1, 4), (4, 3), (3, 5)]:
            g.adicionar_dependencia(a, b)
        ordem = g.ordem_topologica()
        for a, b in [(1, 2), (2, 3), (1, 4), (4, 3), (3, 5)]:
            self.assertLess(ordem.index(a), ordem.index(b))
        with self.assertRaises(ValueError):
            g.adicionar_dependencia(5, 1)
        with self.assertRaises(ValueError):
            g.adicionar_dependencia(2, 2)
        self.assertEqual(len(g.caminho_critico()), 4)


class TestStrings(unittest.TestCase):
    def test_kmp(self):
        self.assertEqual(kmp_buscar("abababa", "aba"), [0, 2, 4])
        self.assertEqual(kmp_buscar("abc", "x"), [])
        self.assertEqual(kmp_buscar("abc", ""), [])

    def test_levenshtein(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3)
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("abc", "abc"), 0)

    def test_normalizar(self):
        self.assertEqual(normalizar("Ação ÚTIL"), "acao util")


class TestGerenciador(unittest.TestCase):
    def setUp(self):
        self.g = GerenciadorTarefas()
        self.a = self.g.criar("Estudar grafos", "revisar Dijkstra", "2026-11-10", 2, ["estudo"])
        self.b = self.g.criar("Implementar trabalho", "código em Python", "2026-12-01", 1,
                              ["projeto"], [self.a.id])
        self.c = self.g.criar("Escrever relatório", "incluir prompts", "2026-11-20", 3,
                              ["projeto"], [self.b.id])

    def test_crud(self):
        self.assertEqual(self.g.ler(1).titulo, "Estudar grafos")
        self.g.atualizar(1, titulo="Estudar árvores AVL")
        self.assertEqual(self.g.ler(1).titulo, "Estudar árvores AVL")
        self.assertEqual(self.g.buscar_prefixo("arv")[0].id, 1)
        self.assertEqual(self.g.buscar_prefixo("grafos"), [])
        self.g.excluir(3)
        with self.assertRaises(ErroTarefa):
            self.g.ler(3)
        self.assertEqual(len(self.g.listar("id")), 2)

    def test_listagens(self):
        self.assertEqual([t.id for t in self.g.listar("prazo")], [1, 3, 2])
        self.assertEqual([t.id for t in self.g.listar("prioridade")], [2, 1, 3])

    def test_dependencias_bloqueiam_conclusao(self):
        with self.assertRaises(ErroTarefa):
            self.g.atualizar(2, status="concluida")
        self.assertEqual(self.g.proxima().id, 1)
        self.g.atualizar(1, status="concluida")
        self.g.atualizar(2, status="concluida")
        self.assertEqual(self.g.proxima().id, 3)
        self.assertEqual(self.g.ordem_execucao(), [3])

    def test_ciclo_rejeitado(self):
        with self.assertRaises(ErroTarefa):
            self.g.adicionar_dependencia(3, 1)

    def test_periodo(self):
        ids = [t.id for t in self.g.por_periodo("2026-11-15", "2026-12-31")]
        self.assertEqual(ids, [3, 2])

    def test_buscas_textuais(self):
        self.assertEqual([t.id for t in self.g.buscar_texto("dijkstra")], [1])
        self.assertEqual([t.id for t in self.g.buscar_texto("PROMPTS")], [3])
        self.assertEqual(self.g.buscar_aproximado("relatorrio")[0].id, 3)
        self.assertIn("estudar", self.g.autocompletar("est"))

    def test_persistencia(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "t.json")
            self.g.atualizar(1, status="concluida")
            self.g.salvar(caminho)
            g2 = GerenciadorTarefas.carregar(caminho)
        self.assertEqual([t.id for t in g2.listar("prazo")], [1, 3, 2])
        self.assertEqual(g2.dependencias(2), [1])
        self.assertEqual(g2.ler(1).status, "concluida")
        self.assertEqual(g2.criar("nova").id, 4)

    def test_validacao(self):
        for kwargs in [dict(titulo=" "), dict(titulo="x", prazo="31/12/2026"),
                       dict(titulo="x", prioridade=9), dict(titulo="x", dependencias=[99])]:
            with self.assertRaises(ErroTarefa):
                self.g.criar(**kwargs)


if __name__ == "__main__":
    unittest.main()
