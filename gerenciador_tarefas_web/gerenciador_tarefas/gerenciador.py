"""Gerenciador de tarefas (CRUD) que integra todas as estruturas de dados.

Estrutura          | Papel no sistema
-------------------|-----------------------------------------------------------
TabelaHash         | armazenamento principal id -> tarefa
ArvoreAVL          | índice por prazo (listagem ordenada e consulta por período)
FilaPrioridade     | "o que fazer agora?" (prioridade, depois prazo)
Trie               | autocompletar e busca por prefixo em títulos e tags
GrafoDependencias  | dependências entre tarefas, ordem topológica, caminho crítico
KMP / Levenshtein  | busca textual exata na descrição e busca aproximada no título
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import date

from estruturas import (ArvoreAVL, FilaPrioridade, TabelaHash, Trie,
                        GrafoDependencias, kmp_buscar, levenshtein, normalizar)

STATUS = ("pendente", "andamento", "concluida")


@dataclass
class Tarefa:
    id: int
    titulo: str
    descricao: str = ""
    prazo: str = ""          # AAAA-MM-DD
    prioridade: int = 3      # 1 (mais urgente) a 5 (menos urgente)
    status: str = "pendente"
    tags: list = field(default_factory=list)


class ErroTarefa(Exception):
    pass


class GerenciadorTarefas:
    def __init__(self):
        self._tarefas = TabelaHash()
        self._por_prazo = ArvoreAVL()
        self._fila = FilaPrioridade()
        self._trie = Trie()
        self._grafo = GrafoDependencias()
        self._proximo_id = 1

    # ------------------------------------------------------------ validações
    @staticmethod
    def _validar(titulo, prazo, prioridade, status=None):
        if not titulo or not titulo.strip():
            raise ErroTarefa("o título não pode ser vazio")
        if prazo:
            try:
                date.fromisoformat(prazo)
            except ValueError:
                raise ErroTarefa("prazo inválido, use AAAA-MM-DD")
        if not 1 <= prioridade <= 5:
            raise ErroTarefa("a prioridade deve estar entre 1 e 5")
        if status is not None and status not in STATUS:
            raise ErroTarefa(f"status inválido, use: {', '.join(STATUS)}")

    # --------------------------------------------------------------- índices
    @staticmethod
    def _palavras(t):
        palavras = set(normalizar(t.titulo).split())
        palavras.update(normalizar(tag) for tag in t.tags)
        return palavras

    @staticmethod
    def _chave_prazo(t):
        return (t.prazo or "9999-12-31", t.id)

    @staticmethod
    def _chave_fila(t):
        return (t.prioridade, t.prazo or "9999-12-31", t.id)

    def _indexar(self, t):
        self._por_prazo.inserir(self._chave_prazo(t), t.id)
        if t.status != "concluida":
            self._fila.inserir(t.id, self._chave_fila(t))
        for p in self._palavras(t):
            self._trie.inserir(p, t.id)

    def _desindexar(self, t):
        self._por_prazo.remover(self._chave_prazo(t))
        self._fila.remover(t.id)
        for p in self._palavras(t):
            self._trie.remover(p, t.id)

    # ------------------------------------------------------------------ CRUD
    def criar(self, titulo, descricao="", prazo="", prioridade=3, tags=None,
              dependencias=None):
        self._validar(titulo, prazo, prioridade)
        dependencias = dependencias or []
        for d in dependencias:
            if self._tarefas.obter(d) is None:
                raise ErroTarefa(f"dependência #{d} não existe")
        t = Tarefa(self._proximo_id, titulo.strip(), descricao, prazo,
                   prioridade, "pendente", [x.strip() for x in (tags or []) if x.strip()])
        self._proximo_id += 1
        self._tarefas.colocar(t.id, t)
        self._grafo.adicionar_no(t.id)
        for d in dependencias:
            self._grafo.adicionar_dependencia(d, t.id)  # nunca cria ciclo (t é novo)
        self._indexar(t)
        return t

    def ler(self, id_):
        t = self._tarefas.obter(id_)
        if t is None:
            raise ErroTarefa(f"tarefa #{id_} não encontrada")
        return t

    def listar(self, ordem="prazo"):
        """ordem: 'prazo' (AVL), 'prioridade' (heap) ou 'id'."""
        if ordem == "prazo":
            return [self._tarefas.obter(i) for _, i in self._por_prazo.em_ordem()]
        if ordem == "prioridade":
            pendentes = [self._tarefas.obter(i) for i in self._fila.ordenado()]
            concluidas = sorted((t for t in self._tarefas.valores()
                                 if t.status == "concluida"), key=lambda t: t.id)
            return pendentes + concluidas
        return sorted(self._tarefas.valores(), key=lambda t: t.id)

    def atualizar(self, id_, **campos):
        t = self.ler(id_)
        novo = Tarefa(**asdict(t))
        for k, v in campos.items():
            if v is None:
                continue
            if not hasattr(novo, k) or k == "id":
                raise ErroTarefa(f"campo inválido: {k}")
            setattr(novo, k, v)
        self._validar(novo.titulo, novo.prazo, novo.prioridade, novo.status)
        if novo.status == "concluida" and t.status != "concluida":
            bloqueios = self.bloqueios(id_)
            if bloqueios:
                ids = ", ".join(f"#{b}" for b in bloqueios)
                raise ErroTarefa(f"bloqueada por tarefas não concluídas: {ids}")
        self._desindexar(t)
        self._tarefas.colocar(id_, novo)
        self._indexar(novo)
        return novo

    def excluir(self, id_):
        t = self.ler(id_)
        dependentes = self._grafo.sucessores(id_)
        self._desindexar(t)
        self._tarefas.remover(id_)
        self._grafo.remover_no(id_)
        return t, sorted(dependentes)

    # ------------------------------------------------------------ dependências
    def adicionar_dependencia(self, antes, depois):
        self.ler(antes)
        self.ler(depois)
        try:
            self._grafo.adicionar_dependencia(antes, depois)
        except ValueError as e:
            raise ErroTarefa(str(e))

    def remover_dependencia(self, antes, depois):
        self._grafo.remover_dependencia(antes, depois)

    def dependencias(self, id_):
        return sorted(self._grafo.predecessores(id_))

    def bloqueios(self, id_):
        """Pré-requisitos ainda não concluídos."""
        return sorted(p for p in self._grafo.predecessores(id_)
                      if self._tarefas.obter(p).status != "concluida")

    def ordem_execucao(self):
        """Ordem topológica das tarefas ainda não concluídas."""
        return [i for i in self._grafo.ordem_topologica()
                if self._tarefas.obter(i).status != "concluida"]

    def caminho_critico(self):
        return self._grafo.caminho_critico()

    # --------------------------------------------------------------- consultas
    def proxima(self):
        """Tarefa mais urgente que já está liberada (sem bloqueios)."""
        for i in self._fila.ordenado():
            if not self.bloqueios(i):
                return self._tarefas.obter(i)
        return None

    def por_periodo(self, inicio, fim):
        a, b = (inicio or "0000-01-01", 0), (fim or "9999-12-31", float("inf"))
        return [self._tarefas.obter(i) for _, i in self._por_prazo.intervalo(a, b)]

    def autocompletar(self, prefixo, limite=5):
        return self._trie.autocompletar(normalizar(prefixo), limite)

    def buscar_prefixo(self, prefixo):
        _, ids = self._trie.buscar_prefixo(normalizar(prefixo))
        return [self._tarefas.obter(i) for i in sorted(ids)]

    def buscar_texto(self, termo):
        """Busca exata (KMP) de `termo` em título e descrição."""
        termo = normalizar(termo)
        achadas = []
        for t in self.listar("id"):
            texto = normalizar(t.titulo + "\n" + t.descricao)
            if kmp_buscar(texto, termo):
                achadas.append(t)
        return achadas

    def buscar_aproximado(self, termo, tolerancia=2):
        """Busca tolerante a erros: Levenshtein entre `termo` e cada palavra do título."""
        termo = normalizar(termo)
        resultado = []
        for t in self.listar("id"):
            melhor = min((levenshtein(termo, p) for p in normalizar(t.titulo).split()),
                         default=99)
            if melhor <= tolerancia:
                resultado.append((melhor, t))
        resultado.sort(key=lambda x: (x[0], x[1].id))
        return [t for _, t in resultado]

    # ------------------------------------------------------------ visualização
    def estruturas(self):
        """Estado interno de cada estrutura, para a interface web."""
        return {
            "avl": {"raiz": self._por_prazo.como_arvore(),
                    "tamanho": len(self._por_prazo), "altura": self._por_prazo.altura()},
            "heap": self._fila.como_lista(),
            "hash": {"baldes": self._tarefas.como_baldes(),
                     "tamanho": len(self._tarefas),
                     "carga": round(self._tarefas.fator_de_carga(), 2)},
            "trie": self._trie.como_arvore(),
            "grafo": {"nos": self._grafo.nos(), "arestas": self._grafo.arestas(),
                      "ordem": self.ordem_execucao(), "critico": self.caminho_critico()},
        }

    # ------------------------------------------------------------ persistência
    def salvar(self, caminho):
        dados = {
            "proximo_id": self._proximo_id,
            "tarefas": [asdict(t) for t in self.listar("id")],
            "dependencias": [[a, b] for b in self._tarefas.chaves()
                             for a in self._grafo.predecessores(b)],
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, caminho):
        g = cls()
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        for d in dados["tarefas"]:
            t = Tarefa(**d)
            g._tarefas.colocar(t.id, t)
            g._grafo.adicionar_no(t.id)
            g._indexar(t)
        for a, b in dados["dependencias"]:
            g._grafo.adicionar_dependencia(a, b)
        g._proximo_id = dados["proximo_id"]
        return g
