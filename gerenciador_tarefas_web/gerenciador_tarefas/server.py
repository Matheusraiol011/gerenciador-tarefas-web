"""Servidor web do TaskFlow (somente biblioteca padrão).

    python server.py [porta]      ->  http://127.0.0.1:8000

A página (static/index.html) conversa com esta API JSON; toda a lógica e todos
os algoritmos continuam nas estruturas de dados do projeto. Os dados são salvos
em tarefas.json após cada alteração.
"""

import json
import os
import re
import sys
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from gerenciador import GerenciadorTarefas, ErroTarefa

RAIZ = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(RAIZ, "tarefas.json")
PAGINA = os.path.join(RAIZ, "static", "index.html")

trava = threading.Lock()
g = (GerenciadorTarefas.carregar(ARQUIVO_DADOS)
     if os.path.exists(ARQUIVO_DADOS) else GerenciadorTarefas())


def serializar(t):
    d = asdict(t)
    d["dependencias"] = g.dependencias(t.id)
    d["bloqueios"] = g.bloqueios(t.id) if t.status != "concluida" else []
    return d


def estado(ordem="prazo"):
    if ordem not in ("prazo", "prioridade", "id"):
        ordem = "prazo"
    proxima = g.proxima()
    return {
        "tarefas": [serializar(t) for t in g.listar(ordem)],
        "proxima": proxima.id if proxima else None,
        "estruturas": g.estruturas(),
    }


def salvar():
    g.salvar(ARQUIVO_DADOS)


class Handler(BaseHTTPRequestHandler):
    server_version = "TaskFlow/1.0"

    # ---------------------------------------------------------------- saída
    def _enviar(self, status, corpo, tipo="application/json; charset=utf-8"):
        dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(dados)

    def _erro(self, status, msg):
        self._enviar(status, {"erro": msg})

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # -------------------------------------------------------------- entrada
    def _corpo(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 1_000_000:
            raise ErroTarefa("corpo da requisição grande demais")
        if not tamanho:
            return {}
        try:
            dados = json.loads(self.rfile.read(tamanho))
        except json.JSONDecodeError:
            raise ErroTarefa("JSON inválido")
        if not isinstance(dados, dict):
            raise ErroTarefa("o corpo deve ser um objeto JSON")
        return dados

    def _despachar(self, metodo):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        # Mutações exigem JSON: um site de terceiros não consegue enviar isso
        # para localhost sem passar por uma checagem CORS.
        if metodo != "GET" and "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._erro(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "use Content-Type: application/json")
        try:
            with trava:
                self._rotear(metodo, url.path, q)
        except ErroTarefa as e:
            self._erro(HTTPStatus.BAD_REQUEST, str(e))
        except (ValueError, TypeError) as e:
            self._erro(HTTPStatus.BAD_REQUEST, f"dados inválidos: {e}")

    def do_GET(self):
        self._despachar("GET")

    def do_POST(self):
        self._despachar("POST")

    def do_PUT(self):
        self._despachar("PUT")

    def do_DELETE(self):
        self._despachar("DELETE")

    # ---------------------------------------------------------------- rotas
    def _rotear(self, metodo, caminho, q):
        if metodo == "GET" and caminho in ("/", "/index.html"):
            with open(PAGINA, "rb") as f:
                return self._enviar(HTTPStatus.OK, f.read(), "text/html; charset=utf-8")

        if metodo == "GET" and caminho == "/api/estado":
            return self._enviar(HTTPStatus.OK, estado(q.get("ordem", "prazo")))

        if metodo == "POST" and caminho == "/api/tarefas":
            c = self._corpo()
            t = g.criar(str(c.get("titulo", "")), str(c.get("descricao", "")),
                        str(c.get("prazo", "")), int(c.get("prioridade", 3)),
                        [str(x) for x in c.get("tags", [])],
                        [int(x) for x in c.get("dependencias", [])])
            salvar()
            return self._enviar(HTTPStatus.CREATED, {"id": t.id})

        m = re.fullmatch(r"/api/tarefas/(\d+)", caminho)
        if m:
            id_ = int(m.group(1))
            if metodo == "PUT":
                c = self._corpo()
                campos = {k: c[k] for k in ("titulo", "descricao", "prazo", "status", "tags")
                          if k in c}
                if "prioridade" in c:
                    campos["prioridade"] = int(c["prioridade"])
                g.atualizar(id_, **campos)
                salvar()
                return self._enviar(HTTPStatus.OK, {"id": id_})
            if metodo == "DELETE":
                _, dependentes = g.excluir(id_)
                salvar()
                return self._enviar(HTTPStatus.OK, {"dependentes": dependentes})

        if metodo == "POST" and caminho == "/api/dependencias":
            c = self._corpo()
            g.adicionar_dependencia(int(c["antes"]), int(c["depois"]))
            salvar()
            return self._enviar(HTTPStatus.OK, {"ok": True})

        m = re.fullmatch(r"/api/dependencias/(\d+)/(\d+)", caminho)
        if metodo == "DELETE" and m:
            g.remover_dependencia(int(m.group(1)), int(m.group(2)))
            salvar()
            return self._enviar(HTTPStatus.OK, {"ok": True})

        if metodo == "GET" and caminho == "/api/busca":
            modo, termo = q.get("modo", "prefixo"), q.get("q", "").strip()
            if not termo:
                return self._enviar(HTTPStatus.OK, {"ids": [], "sugestoes": []})
            if modo == "texto":
                achadas = g.buscar_texto(termo)
            elif modo == "aproximado":
                achadas = g.buscar_aproximado(termo)
            else:
                achadas = g.buscar_prefixo(termo)
            return self._enviar(HTTPStatus.OK, {
                "ids": [t.id for t in achadas],
                "sugestoes": g.autocompletar(termo) if modo == "prefixo" else []})

        if metodo == "GET" and caminho == "/api/periodo":
            achadas = g.por_periodo(q.get("inicio", ""), q.get("fim", ""))
            return self._enviar(HTTPStatus.OK, {"ids": [t.id for t in achadas]})

        self._erro(HTTPStatus.NOT_FOUND, "rota não encontrada")


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    print(f"TaskFlow em http://127.0.0.1:{porta}  (Ctrl+C para encerrar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main()
