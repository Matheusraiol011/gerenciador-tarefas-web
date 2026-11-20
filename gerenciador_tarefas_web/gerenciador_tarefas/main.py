"""Interface de terminal do TaskFlow.  Execute:  python main.py"""

import os
import sys

from gerenciador import GerenciadorTarefas, ErroTarefa, STATUS

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarefas.json")

MENU = """
========== TaskFlow - Gerenciador de Tarefas ==========
 CRUD
  1) Criar tarefa           2) Listar tarefas
  3) Ver tarefa             4) Atualizar tarefa
  5) Excluir tarefa
 Algoritmos
  6) Próxima tarefa (heap + grafo)
  7) Tarefas por período (AVL)
  8) Autocompletar / prefixo (trie)
  9) Buscar texto (KMP)    10) Busca aproximada (Levenshtein)
 11) Dependências (grafo): adicionar / ordem / caminho crítico
  0) Salvar e sair
"""


def linha(t, g):
    marca = {"pendente": " ", "andamento": "~", "concluida": "x"}[t.status]
    bloq = g.bloqueios(t.id)
    extra = f"  [bloqueada por {', '.join('#' + str(b) for b in bloq)}]" if bloq and t.status != "concluida" else ""
    tags = f"  tags: {','.join(t.tags)}" if t.tags else ""
    return f"[{marca}] #{t.id:<3} P{t.prioridade}  {t.prazo or 'sem prazo':<10}  {t.titulo}{tags}{extra}"


def detalhe(t, g):
    print(f"\n#{t.id} - {t.titulo}")
    print(f"  descrição : {t.descricao or '-'}")
    print(f"  prazo     : {t.prazo or '-'}   prioridade: {t.prioridade}   status: {t.status}")
    print(f"  tags      : {', '.join(t.tags) or '-'}")
    print(f"  depende de: {', '.join('#' + str(d) for d in g.dependencias(t.id)) or '-'}")


def ler_int(msg, padrao=None):
    bruto = input(msg).strip()
    if not bruto and padrao is not None:
        return padrao
    try:
        return int(bruto)
    except ValueError:
        raise ErroTarefa("digite um número inteiro")


def ler_lista_ids(msg):
    bruto = input(msg).replace(",", " ").split()
    try:
        return [int(x.lstrip("#")) for x in bruto]
    except ValueError:
        raise ErroTarefa("ids devem ser números")


def mostrar(lista, g):
    if not lista:
        print("  (nenhuma tarefa)")
    for t in lista:
        print(" ", linha(t, g))


def acao(op, g):
    if op == "1":
        titulo = input("Título: ")
        desc = input("Descrição: ")
        prazo = input("Prazo (AAAA-MM-DD, opcional): ").strip()
        prio = ler_int("Prioridade 1-5 [3]: ", 3)
        tags = [x for x in input("Tags (separadas por vírgula): ").split(",")]
        deps = ler_lista_ids("Depende de (ids, opcional): ")
        t = g.criar(titulo, desc, prazo, prio, tags, deps)
        print(f"Tarefa #{t.id} criada.")
    elif op == "2":
        ordem = input("Ordenar por [prazo/prioridade/id] (prazo): ").strip() or "prazo"
        mostrar(g.listar(ordem), g)
    elif op == "3":
        detalhe(g.ler(ler_int("Id: ")), g)
    elif op == "4":
        i = ler_int("Id: ")
        t = g.ler(i)
        detalhe(t, g)
        print("(Enter mantém o valor atual)")
        titulo = input("Novo título: ") or None
        desc = input("Nova descrição: ") or None
        prazo = input("Novo prazo: ") or None
        p = input("Nova prioridade: ").strip()
        status = input(f"Novo status ({'/'.join(STATUS)}): ").strip() or None
        g.atualizar(i, titulo=titulo, descricao=desc, prazo=prazo,
                    prioridade=int(p) if p else None, status=status)
        print("Tarefa atualizada.")
    elif op == "5":
        t, dependentes = g.excluir(ler_int("Id: "))
        print(f"Tarefa #{t.id} excluída.")
        if dependentes:
            print("  Atenção: dependiam dela:", ", ".join(f"#{d}" for d in dependentes))
    elif op == "6":
        t = g.proxima()
        print(linha(t, g) if t else "Nenhuma tarefa liberada. Tudo feito!")
    elif op == "7":
        ini = input("De (AAAA-MM-DD, opcional): ").strip()
        fim = input("Até (AAAA-MM-DD, opcional): ").strip()
        mostrar(g.por_periodo(ini, fim), g)
    elif op == "8":
        pref = input("Prefixo: ").strip()
        print("  sugestões:", ", ".join(g.autocompletar(pref)) or "-")
        mostrar(g.buscar_prefixo(pref), g)
    elif op == "9":
        mostrar(g.buscar_texto(input("Texto: ")), g)
    elif op == "10":
        mostrar(g.buscar_aproximado(input("Termo (pode ter erros): ")), g)
    elif op == "11":
        sub = input("[a]dicionar dependência / [o]rdem de execução / [c]aminho crítico: ").strip().lower()
        if sub == "a":
            antes = ler_int("Tarefa que deve vir ANTES (id): ")
            depois = ler_int("Tarefa que depende dela (id): ")
            g.adicionar_dependencia(antes, depois)
            print("Dependência adicionada.")
        elif sub == "o":
            print("  ordem:", " -> ".join(f"#{i}" for i in g.ordem_execucao()) or "-")
        elif sub == "c":
            print("  caminho crítico:", " -> ".join(f"#{i}" for i in g.caminho_critico()) or "-")
    else:
        print("Opção inválida.")


def main():
    g = GerenciadorTarefas.carregar(ARQUIVO) if os.path.exists(ARQUIVO) else GerenciadorTarefas()
    while True:
        print(MENU)
        try:
            op = input("Opção: ").strip()
        except EOFError:
            op = "0"
        if op == "0":
            g.salvar(ARQUIVO)
            print("Dados salvos em tarefas.json. Até logo!")
            return
        try:
            acao(op, g)
        except ErroTarefa as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    sys.exit(main())
