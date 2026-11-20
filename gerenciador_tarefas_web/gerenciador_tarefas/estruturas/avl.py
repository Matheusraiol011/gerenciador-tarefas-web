"""Árvore AVL (árvore balanceada de busca).

Usada para indexar tarefas por prazo. A chave é uma tupla (prazo, id), o que
permite chaves repetidas de prazo e consultas por intervalo em O(log n + k).
"""


class _No:
    __slots__ = ("chave", "valor", "esq", "dir", "altura")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.esq = None
        self.dir = None
        self.altura = 1


def _altura(no):
    return no.altura if no else 0


def _atualizar(no):
    no.altura = 1 + max(_altura(no.esq), _altura(no.dir))


def _fator(no):
    return _altura(no.esq) - _altura(no.dir) if no else 0


def _rot_dir(y):
    x = y.esq
    y.esq = x.dir
    x.dir = y
    _atualizar(y)
    _atualizar(x)
    return x


def _rot_esq(x):
    y = x.dir
    x.dir = y.esq
    y.esq = x
    _atualizar(x)
    _atualizar(y)
    return y


def _balancear(no):
    _atualizar(no)
    f = _fator(no)
    if f > 1:  # pesado à esquerda
        if _fator(no.esq) < 0:
            no.esq = _rot_esq(no.esq)  # caso esquerda-direita
        return _rot_dir(no)
    if f < -1:  # pesado à direita
        if _fator(no.dir) > 0:
            no.dir = _rot_dir(no.dir)  # caso direita-esquerda
        return _rot_esq(no)
    return no


class ArvoreAVL:
    def __init__(self):
        self._raiz = None
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def altura(self):
        return _altura(self._raiz)

    # ---------- inserção ----------
    def inserir(self, chave, valor=None):
        self._raiz = self._inserir(self._raiz, chave, valor)

    def _inserir(self, no, chave, valor):
        if no is None:
            self._tamanho += 1
            return _No(chave, valor)
        if chave < no.chave:
            no.esq = self._inserir(no.esq, chave, valor)
        elif chave > no.chave:
            no.dir = self._inserir(no.dir, chave, valor)
        else:
            no.valor = valor  # chave já existe: atualiza
            return no
        return _balancear(no)

    # ---------- remoção ----------
    def remover(self, chave):
        antes = self._tamanho
        self._raiz = self._remover(self._raiz, chave)
        return self._tamanho < antes

    def _remover(self, no, chave):
        if no is None:
            return None
        if chave < no.chave:
            no.esq = self._remover(no.esq, chave)
        elif chave > no.chave:
            no.dir = self._remover(no.dir, chave)
        else:
            if no.esq is None or no.dir is None:
                self._tamanho -= 1
                return no.esq or no.dir
            sucessor = no.dir
            while sucessor.esq:
                sucessor = sucessor.esq
            no.chave, no.valor = sucessor.chave, sucessor.valor
            # a remoção recursiva do sucessor já decrementa o tamanho
            no.dir = self._remover(no.dir, sucessor.chave)
        return _balancear(no)

    # ---------- consultas ----------
    def buscar(self, chave):
        no = self._raiz
        while no:
            if chave < no.chave:
                no = no.esq
            elif chave > no.chave:
                no = no.dir
            else:
                return no.valor
        return None

    def em_ordem(self):
        """Lista (chave, valor) em ordem crescente de chave."""
        resultado = []

        def visitar(no):
            if no:
                visitar(no.esq)
                resultado.append((no.chave, no.valor))
                visitar(no.dir)

        visitar(self._raiz)
        return resultado

    def intervalo(self, minimo, maximo):
        """Todos os (chave, valor) com minimo <= chave <= maximo."""
        resultado = []

        def visitar(no):
            if no is None:
                return
            if minimo < no.chave:
                visitar(no.esq)
            if minimo <= no.chave <= maximo:
                resultado.append((no.chave, no.valor))
            if no.chave < maximo:
                visitar(no.dir)

        visitar(self._raiz)
        return resultado

    def como_arvore(self):
        """Exporta a árvore como dicionários aninhados (usado na visualização web)."""

        def exportar(no):
            if no is None:
                return None
            return {"chave": list(no.chave) if isinstance(no.chave, tuple) else no.chave,
                    "valor": no.valor, "altura": no.altura, "fator": _fator(no),
                    "esq": exportar(no.esq), "dir": exportar(no.dir)}

        return exportar(self._raiz)

    def esta_balanceada(self):
        """Verificação usada nos testes: |fator| <= 1 em todos os nós."""

        def ok(no):
            if no is None:
                return True
            return abs(_fator(no)) <= 1 and ok(no.esq) and ok(no.dir)

        return ok(self._raiz)
