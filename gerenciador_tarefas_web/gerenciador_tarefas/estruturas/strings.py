"""Processamento de cadeias de caracteres.

- KMP (Knuth-Morris-Pratt): busca exata de substring em O(n + m).
- Distância de Levenshtein: busca aproximada (tolerante a erros de digitação).
- normalizar: minúsculas e remoção de acentos, usada por todos os índices.
"""

import unicodedata


def normalizar(texto):
    decomposto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def tabela_prefixo(padrao):
    """Vetor de falha (LPS) do KMP."""
    lps = [0] * len(padrao)
    k = 0
    for i in range(1, len(padrao)):
        while k and padrao[i] != padrao[k]:
            k = lps[k - 1]
        if padrao[i] == padrao[k]:
            k += 1
        lps[i] = k
    return lps


def kmp_buscar(texto, padrao):
    """Retorna todas as posições onde `padrao` ocorre em `texto`."""
    if not padrao:
        return []
    lps = tabela_prefixo(padrao)
    posicoes, k = [], 0
    for i, ch in enumerate(texto):
        while k and ch != padrao[k]:
            k = lps[k - 1]
        if ch == padrao[k]:
            k += 1
        if k == len(padrao):
            posicoes.append(i - k + 1)
            k = lps[k - 1]
    return posicoes


def levenshtein(a, b):
    """Número mínimo de inserções, remoções e trocas para transformar a em b."""
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(anterior[j] + 1,                # remoção
                             atual[j - 1] + 1,               # inserção
                             anterior[j - 1] + (ca != cb)))  # troca
        anterior = atual
    return anterior[-1]
