"""Tabela de dispersão (hash table) com encadeamento separado e redimensionamento.

É o armazenamento principal das tarefas: id -> Tarefa em O(1) esperado.
Não usa `dict` internamente.
"""


class TabelaHash:
    CARGA_MAXIMA = 0.75

    def __init__(self, capacidade=8):
        self._capacidade = capacidade
        self._baldes = [[] for _ in range(capacidade)]
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def __contains__(self, chave):
        return self.obter(chave, _AUSENTE) is not _AUSENTE

    @staticmethod
    def _hash(chave):
        """Hash polinomial (base 31) sobre a representação textual da chave."""
        h = 7
        for ch in str(chave):
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return h

    def _indice(self, chave):
        return self._hash(chave) % self._capacidade

    def colocar(self, chave, valor):
        balde = self._baldes[self._indice(chave)]
        for i, (k, _) in enumerate(balde):
            if k == chave:
                balde[i] = (chave, valor)
                return
        balde.append((chave, valor))
        self._tamanho += 1
        if self._tamanho / self._capacidade > self.CARGA_MAXIMA:
            self._redimensionar(self._capacidade * 2)

    def obter(self, chave, padrao=None):
        for k, v in self._baldes[self._indice(chave)]:
            if k == chave:
                return v
        return padrao

    def remover(self, chave):
        balde = self._baldes[self._indice(chave)]
        for i, (k, _) in enumerate(balde):
            if k == chave:
                del balde[i]
                self._tamanho -= 1
                return True
        return False

    def itens(self):
        for balde in self._baldes:
            for par in balde:
                yield par

    def valores(self):
        return [v for _, v in self.itens()]

    def chaves(self):
        return [k for k, _ in self.itens()]

    def como_baldes(self):
        """Chaves de cada balde, na ordem dos índices (usado na visualização web)."""
        return [[k for k, _ in balde] for balde in self._baldes]

    def fator_de_carga(self):
        return self._tamanho / self._capacidade

    def _redimensionar(self, nova_capacidade):
        antigos = list(self.itens())
        self._capacidade = nova_capacidade
        self._baldes = [[] for _ in range(nova_capacidade)]
        self._tamanho = 0
        for k, v in antigos:
            self.colocar(k, v)


_AUSENTE = object()
