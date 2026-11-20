# TaskFlow — Gerenciador de Tarefas com Dependências

Atividade avaliativa de Estruturas de Dados II. Sistema CRUD de tarefas (estudo/projetos) sem banco de dados, com interação por terminal e uma estrutura de dados para cada item do conteúdo programático. Só usa a biblioteca padrão do Python 3.9+.

## Tema (para a apresentação de 19 e 21/10)

Gerenciador de tarefas acadêmicas e de projetos em que **tarefas podem depender de outras** (ex.: "Escrever relatório" só pode ser concluída depois de "Implementar trabalho"). O sistema responde a perguntas como: *o que devo fazer agora? em que ordem fazer tudo? o que vence neste período? qual tarefa tem "grafo" no nome, mesmo que eu digite errado?*

## Como executar

```bash
python server.py                        # interface web em http://127.0.0.1:8000
python main.py                          # menu interativo no terminal
python -m unittest discover -s tests    # 22 testes
```

Terminal e web usam o mesmo `tarefas.json`; não rode os dois ao mesmo tempo.

## Interface web

`server.py` (só biblioteca padrão) expõe uma API JSON sobre o `GerenciadorTarefas` e serve a página `static/index.html`. Toda a lógica continua nas estruturas de dados em Python; a página só desenha o que elas devolvem.

- **Tarefas**: criar, editar, excluir, mudar status com um clique, ordenar por prazo (AVL), prioridade (heap) ou criação, filtrar por período (AVL).
- **Próxima tarefa**: heap combinado com o grafo, ignorando tarefas bloqueadas.
- **Busca**: prefixo (trie, com sugestões), texto exato (KMP) e aproximada (Levenshtein).
- **Painel de estruturas**: dependências (grafo, ordem topológica e caminho crítico), árvore AVL com fator de balanceamento, heap como árvore e como vetor, tabela hash com colisões e trie com o caminho do prefixo digitado. Clicar em um nó abre a tarefa.
- Botão "Carregar exemplo" na lista vazia cria tarefas com dependências para demonstração.

| Rota | Função |
|---|---|
| `GET /api/estado?ordem=` | tarefas, próxima tarefa e estado de cada estrutura |
| `POST /api/tarefas`, `PUT/DELETE /api/tarefas/<id>` | criar, atualizar, excluir |
| `POST /api/dependencias`, `DELETE /api/dependencias/<antes>/<depois>` | dependências |
| `GET /api/busca?modo=prefixo\|texto\|aproximado&q=` | buscas |
| `GET /api/periodo?inicio=&fim=` | consulta por intervalo na AVL |

O servidor escuta apenas em 127.0.0.1 e exige `Content-Type: application/json` nas alterações.

## Onde cada conteúdo programático aparece

| Conteúdo | Arquivo | Uso no sistema |
|---|---|---|
| Árvores balanceadas | `estruturas/avl.py` | Índice por prazo: listagem ordenada e consulta por período em O(log n + k) |
| Listas de prioridades | `estruturas/heap.py` | Min-heap com mapa de posições: "próxima tarefa", atualização e remoção em O(log n) |
| Tabelas de dispersão | `estruturas/hash_table.py` | Armazenamento principal id → tarefa (encadeamento + redimensionamento, sem `dict`) |
| Busca digital | `estruturas/trie.py` | Autocompletar e busca por prefixo em títulos e tags |
| Grafos | `estruturas/grafo.py` | Dependências: detecção de ciclo (DFS), ordem topológica (Kahn), caminho crítico |
| Cadeias de caracteres | `estruturas/strings.py` | KMP (busca exata em título/descrição) e Levenshtein (busca aproximada) |

`gerenciador.py` integra tudo e mantém os índices consistentes a cada criação, atualização e exclusão. `main.py` é a interface de terminal e `server.py` com `static/index.html` formam a interface web.

## Regras de negócio

- Prioridade de 1 (urgente) a 5; prazo no formato `AAAA-MM-DD` (opcional).
- Uma tarefa só pode ser concluída se todos os pré-requisitos estiverem concluídos.
- Dependências que criariam ciclo são rejeitadas.
- "Próxima tarefa" = a de maior prioridade (desempate por prazo) que não está bloqueada.
- Persistência em arquivo JSON, salvo ao sair (não é banco de dados).

## Estrutura

```
estruturas/   avl.py  heap.py  hash_table.py  trie.py  grafo.py  strings.py
gerenciador.py   main.py   server.py   static/index.html
tests/   test_tudo.py  test_api.py
```

## Entregas

1. 19 e 21/10/2026: apresentação do tema (seção "Tema" acima).
2. Dezembro: slides + relatório em PDF + anexo com os principais prompts usados.
