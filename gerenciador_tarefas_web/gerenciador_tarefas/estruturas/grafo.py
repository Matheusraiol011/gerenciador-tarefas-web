"""Grafo dirigido de dependências entre tarefas.

Aresta A -> B significa "A precisa ser concluída antes de B".
Algoritmos: detecção de ciclo (DFS), ordenação topológica (Kahn) e
caminho crítico (maior cadeia de dependências, programação dinâmica na ordem topológica).
"""

from collections import deque


class GrafoDependencias:
    def __init__(self):
        self._adj = {}   # nó -> conjunto de sucessores
        self._radj = {}  # nó -> conjunto de predecessores

    def adicionar_no(self, no):
        self._adj.setdefault(no, set())
        self._radj.setdefault(no, set())

    def remover_no(self, no):
        for suc in self._adj.pop(no, set()):
            self._radj[suc].discard(no)
        for pred in self._radj.pop(no, set()):
            self._adj[pred].discard(no)

    def nos(self):
        return sorted(self._adj)

    def arestas(self):
        return sorted((a, b) for a, suc in self._adj.items() for b in suc)

    def predecessores(self, no):
        return set(self._radj.get(no, ()))

    def sucessores(self, no):
        return set(self._adj.get(no, ()))

    def existe_caminho(self, origem, destino):
        """DFS iterativa: existe caminho origem ->* destino?"""
        if origem not in self._adj:
            return False
        visitados, pilha = set(), [origem]
        while pilha:
            atual = pilha.pop()
            if atual == destino:
                return True
            if atual in visitados:
                continue
            visitados.add(atual)
            pilha.extend(self._adj[atual])
        return False

    def criaria_ciclo(self, antes, depois):
        """Adicionar antes -> depois cria ciclo? (self-loop também conta)"""
        return antes == depois or self.existe_caminho(depois, antes)

    def adicionar_dependencia(self, antes, depois):
        if self.criaria_ciclo(antes, depois):
            raise ValueError("a dependência criaria um ciclo")
        self.adicionar_no(antes)
        self.adicionar_no(depois)
        self._adj[antes].add(depois)
        self._radj[depois].add(antes)

    def remover_dependencia(self, antes, depois):
        if antes in self._adj:
            self._adj[antes].discard(depois)
        if depois in self._radj:
            self._radj[depois].discard(antes)

    def ordem_topologica(self):
        """Algoritmo de Kahn. Empates resolvidos por ordem de id (determinístico)."""
        grau = {n: len(self._radj[n]) for n in self._adj}
        fila = deque(sorted(n for n, g in grau.items() if g == 0))
        ordem = []
        while fila:
            n = fila.popleft()
            ordem.append(n)
            liberados = []
            for suc in self._adj[n]:
                grau[suc] -= 1
                if grau[suc] == 0:
                    liberados.append(suc)
            fila.extend(sorted(liberados))
        if len(ordem) != len(self._adj):
            raise ValueError("o grafo possui ciclo")
        return ordem

    def caminho_critico(self):
        """Maior cadeia de dependências (em número de tarefas)."""
        ordem = self.ordem_topologica()
        if not ordem:
            return []
        dist = {n: 1 for n in ordem}
        anterior = {n: None for n in ordem}
        for n in ordem:
            for suc in self._adj[n]:
                if dist[n] + 1 > dist[suc]:
                    dist[suc] = dist[n] + 1
                    anterior[suc] = n
        fim = max(ordem, key=lambda n: dist[n])
        caminho = []
        while fim is not None:
            caminho.append(fim)
            fim = anterior[fim]
        return caminho[::-1]
