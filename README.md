# Analisador Sintático
Projeto da disciplina de Construção de Compiladores - Universidade Federal da Paraíba.
Victor José de Sousa Koehler

<br />

## Execução
`python sintatico.py [-h -r -s -t] {arquivo de entrada} [{arquivo de saída}]`

ou ainda

`python sintatico.py [-h -r -s -t] -i [{arquivo de saída}]`

Onde:

-h: Imprime um texto de ajuda e encerra.

-r: Por padrão, é lançada uma exceção quando um arquivo de regras contém uma recursão à esquerda de primeiro nível. Ao usar esta opção, a exceção é suprimida, uma mensagem de erro é impressa e a execução do parser continua.

-s: Imprime uma string simplificada no formato REGRA:TOKEN para cada nó folha da árvore resultante na saída. Isso facilita um pouco a leitura do arquivo resultante.

-t: Invoca uma exceção quando encontrado um erro de tipo.

-i: Lê a entrada através de stdin (a entrada de texto padrão do terminal).

O arquivo de entrada é gerado pelo projeto https://github.com/VictorKoehler/COMP-1st-Lexico (usando -u como opção de linha de comando).

O arquivo de saída é produzido no formato JSON. Se suprimido da linha de comando, será impresso na saída padrão de texto do terminal.


## Dependências:
- Python
