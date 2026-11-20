import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from gerenciador import GerenciadorTarefas
from http.server import ThreadingHTTPServer


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        server.ARQUIVO_DADOS = os.path.join(cls.pasta.name, "t.json")
        server.g = GerenciadorTarefas()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.pasta.cleanup()

    def chamar(self, metodo, caminho, corpo=None, json_header=True):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(self.base + caminho, data=dados, method=metodo)
        if json_header and metodo != "GET":
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def test_fluxo_completo(self):
        _, a = self.chamar("POST", "/api/tarefas", {"titulo": "Estudar AVL", "prazo": "2026-10-25", "prioridade": 2, "tags": ["estudo"]})
        _, b = self.chamar("POST", "/api/tarefas", {"titulo": "Implementar", "prazo": "2026-11-15", "prioridade": 1, "dependencias": [a["id"]]})

        # dependência circular e conclusão bloqueada são recusadas com 400
        st, r = self.chamar("POST", "/api/dependencias", {"antes": b["id"], "depois": a["id"]})
        self.assertEqual(st, 400)
        self.assertIn("ciclo", r["erro"])
        st, r = self.chamar("PUT", f"/api/tarefas/{b['id']}", {"status": "concluida"})
        self.assertEqual(st, 400)

        _, estado = self.chamar("GET", "/api/estado")
        self.assertEqual(estado["proxima"], a["id"])
        self.assertEqual(estado["estruturas"]["grafo"]["arestas"], [[a["id"], b["id"]]])
        self.assertEqual(estado["estruturas"]["avl"]["tamanho"], 2)
        self.assertEqual(len(estado["estruturas"]["heap"]), 2)

        _, achou = self.chamar("GET", "/api/busca?modo=prefixo&q=impl")
        self.assertEqual(achou["ids"], [b["id"]])
        _, periodo = self.chamar("GET", "/api/periodo?inicio=2026-11-01&fim=2026-11-30")
        self.assertEqual(periodo["ids"], [b["id"]])

        # concluir o pré-requisito libera a próxima; os dados são gravados no arquivo
        self.assertEqual(self.chamar("PUT", f"/api/tarefas/{a['id']}", {"status": "concluida"})[0], 200)
        _, estado = self.chamar("GET", "/api/estado")
        self.assertEqual(estado["proxima"], b["id"])
        self.assertTrue(os.path.exists(server.ARQUIVO_DADOS))

        st, r = self.chamar("DELETE", f"/api/tarefas/{a['id']}")
        self.assertEqual((st, r["dependentes"]), (200, [b["id"]]))

    def test_rejeita_corpo_que_nao_e_json(self):
        st, _ = self.chamar("POST", "/api/tarefas", {"titulo": "x"}, json_header=False)
        self.assertEqual(st, 415)

    def test_pagina_e_rota_desconhecida(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"TaskFlow", r.read())
        self.assertEqual(self.chamar("GET", "/api/nada")[0], 404)


if __name__ == "__main__":
    unittest.main()
