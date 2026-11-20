"""Trie (árvore digital) para busca por prefixo / autocompletar.

Cada palavra indexada guarda o conjunto de ids de tarefas em que aparece.
"""


class _NoTrie:
    __slots__ = ("filhos", "ids")

    def __init__(self):
        self.filhos = {}
        self.ids = set()


class Trie:
    def __init__(self):
        self._raiz = _NoTrie()

    def inserir(self, palavra, id_):
        no = self._raiz
        for ch in palavra:
            no = no.filhos.setdefault(ch, _NoTrie())
        no.ids.add(id_)

    def remover(self, palavra, id_):
        """Remove a associação palavra->id e poda ramos que ficaram vazios."""
        caminho = []
        no = self._raiz
        for ch in palavra:
            if ch not in no.filhos:
                return
            caminho.append((no, ch))
            no = no.filhos[ch]
        no.ids.discard(id_)
        for pai, ch in reversed(caminho):
            filho = pai.filhos[ch]
            if filho.ids or filho.filhos:
                break
            del pai.filhos[ch]

    def buscar_prefixo(self, prefixo):
        """Retorna (palavras, ids) de tudo que começa com `prefixo`."""
        no = self._raiz
        for ch in prefixo:
            if ch not in no.filhos:
                return [], set()
            no = no.filhos[ch]
        palavras, ids = [], set()

        def coletar(n, acumulado):
            if n.ids:
                palavras.append(acumulado)
                ids.update(n.ids)
            for ch in sorted(n.filhos):
                coletar(n.filhos[ch], acumulado + ch)

        coletar(no, prefixo)
        return palavras, ids

    def como_arvore(self):
        """Exporta a trie como dicionários aninhados (usado na visualização web)."""

        def exportar(no, letra):
            return {"letra": letra, "ids": sorted(no.ids),
                    "filhos": [exportar(no.filhos[c], c) for c in sorted(no.filhos)]}

        return exportar(self._raiz, "")

    def autocompletar(self, prefixo, limite=5):
        palavras, _ = self.buscar_prefixo(prefixo)
        return palavras[:limite]
