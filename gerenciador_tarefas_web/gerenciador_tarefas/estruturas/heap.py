"""Fila de prioridades implementada com um min-heap binário.

Mantém um mapa chave -> posição, o que permite atualizar a prioridade e
remover elementos arbitrários em O(log n) (necessário para o CRUD).
"""


class FilaPrioridade:
    def __init__(self):
        self._heap = []  # lista de (prioridade, id)
        self._pos = {}   # id -> índice no heap

    def __len__(self):
        return len(self._heap)

    def __contains__(self, item):
        return item in self._pos

    def inserir(self, item, prioridade):
        """Insere ou atualiza `item`. Menor `prioridade` sai primeiro."""
        if item in self._pos:
            self.atualizar(item, prioridade)
            return
        self._heap.append((prioridade, item))
        self._pos[item] = len(self._heap) - 1
        self._subir(len(self._heap) - 1)

    def topo(self):
        return self._heap[0][1] if self._heap else None

    def extrair(self):
        """Remove e retorna o item de maior prioridade (menor valor)."""
        if not self._heap:
            return None
        item = self._heap[0][1]
        self.remover(item)
        return item

    def atualizar(self, item, nova_prioridade):
        i = self._pos[item]
        antiga = self._heap[i][0]
        self._heap[i] = (nova_prioridade, item)
        if nova_prioridade < antiga:
            self._subir(i)
        else:
            self._descer(i)

    def remover(self, item):
        if item not in self._pos:
            return False
        i = self._pos[item]
        ultimo = len(self._heap) - 1
        self._trocar(i, ultimo)
        self._heap.pop()
        del self._pos[item]
        if i < len(self._heap):
            self._subir(i)
            self._descer(i)
        return True

    def como_lista(self):
        """Vetor do heap na ordem real de armazenamento (usado na visualização web)."""
        return [{"item": item, "prioridade": list(p) if isinstance(p, tuple) else p}
                for p, item in self._heap]

    def ordenado(self):
        """Itens em ordem de prioridade, sem alterar a fila (heap sort em cópia)."""
        copia = FilaPrioridade()
        copia._heap = list(self._heap)
        copia._pos = dict(self._pos)
        saida = []
        while len(copia):
            saida.append(copia.extrair())
        return saida

    # ---------- internos ----------
    def _trocar(self, i, j):
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._pos[self._heap[i][1]] = i
        self._pos[self._heap[j][1]] = j

    def _subir(self, i):
        while i > 0:
            pai = (i - 1) // 2
            if self._heap[i] < self._heap[pai]:
                self._trocar(i, pai)
                i = pai
            else:
                break

    def _descer(self, i):
        n = len(self._heap)
        while True:
            menor = i
            for filho in (2 * i + 1, 2 * i + 2):
                if filho < n and self._heap[filho] < self._heap[menor]:
                    menor = filho
            if menor == i:
                break
            self._trocar(i, menor)
            i = menor
