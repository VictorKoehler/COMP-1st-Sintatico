from rules_reader import read_rules, empty_char
from sys import argv, stderr
import json


def parse_rule_label(inpc: dict, inpdata: str, rules, label: str, recsel = {}, recpath = '', simple_terminal=False):
    '''Tenta expandir recursivamente o label (regra) de acordo com a entrada (inpdata) e o cursor dela (inpc).
    Recebe o conjunto de regras (rules) e o nome da regra a ser interpretada (label).
    Se simple_terminal=True, então as folhas da árvore serão representadas de maneira simplificada.
    Também recebe, opcionalmente, um caminho completo da recursividade em string e
    um dicionário contendo as terminações ambíguas demarcadas por este caminho recursivo.
    parse_permutations utiliza estes dois últimos parâmetros para permutar as combinações ambíguas
    até encontrar alguma terminação que gere algum resultado viável.
    Retorna uma lista de produções, se for viável; uma lista vazia (caso a regra tenha uma terminação vazia);
    ou None caso não seja possível aplicar esta regra na entrada.
    '''
    exprules = rules[1][rules[0][label]]["expr_rules"]

    def is_empty_rule(rs):
        return len(rs) == 1 and rs[0] == empty_char

    productions = []
    for rs in exprules: # Para cada alternativa de expansão da regra:
        curs = inpc.copy() # Faça uma cópia de onde está o cursor
        applies = [] # Salva o que será retornado - se será retornado.
        for r in rs: # Para cada palavra da alternativa

            # Verifica se o cursor já chegou no fim do arquivo.
            if curs["cursor"] >= len(inpdata):
                applies = None # Se sim, aborta a regra.
                break
            c = inpdata[curs["cursor"]] # Token lido
            rh = r[0] # Sinal (@#$%£)
            rt = r[1:] # Palavra

            act = {
                "#": c["token"] == rt and c["class"] != "identificador",
                "$": c["class"] == "identificador",
                "%": c["class"] == rt
            }
            act_g = act.get(rh, None)

            if not act_g is None: # Sinal/Token simples: Identificador/Reservado/Aditivo/Classe/etc
                if act_g: # Se satisfaz o sinal, o token é aceito
                    t = (r + ':' + c['token']) if simple_terminal else { 'symbol': r, 'token': c['token'] }
                    applies.append(t)
                    curs["cursor"] += 1
                else: # Senão, reverte.
                    applies = None
                    break
            
            elif rh == "@": # Invocação de outra regra
                fullpath = '->'.join([recpath, label, str(exprules.index(rs)), r])
                reapp = parse_rule_label(curs, inpdata, rules, rt, recsel, fullpath, simple_terminal)
                if reapp is None: # Se a regra não pode ser derivada, aborta esta expansão.
                    applies = None
                    break
                elif len(reapp) > 0: # Senão, adiciona a expansão.
                    applies.append({ 'symbol': r, 'expansion': reapp })
            elif rh != empty_char: # Token inválido: aborta a expansão.
                applies = None
                break
        if applies is None: # Se a expansão foi abortada, tenta outra regra alternativa.
            continue
        productions.append((applies, curs, r, rs, label)) # Senão, diz que o label produz esta expansão.

    prodind = 0 # Retorna a única expansão, se possível.
    if len(productions) > 1: # Se há mais de uma expansão, temos uma ambiguidade!
        s = recsel.get(recpath, None)
        if s is None: # Se a ambiguidade ainda não foi detectada, registramos-na.
            print('Ambiguidade detectada! Revise as regras e o modelo de saída.', file=stderr)
            s = (0, len(productions), label, recpath, productions) # Por padrão, vamos tentar resolver o modelo
            recsel[recpath] = s #       usando a primeira correspondência encontrada.
        # Se a solução se demonstrar inviavel, parse_permutations irá alterar o valor padrão
        # na tentativa de encontrar alguma solução viável.
        prodind = s[0] # Retornamos uma das expansões

    elif len(productions) == 0: # Se o label não produz nenhuma expansão.
        hasempty = len([x for x in exprules if is_empty_rule(x)]) > 0
        if hasempty: # Verificamos se existe a regra vazia no conjunto
            return [] # Se sim, retorna uma produção vazia.
        return None # Se não, retorna que a produção é inviavel.
    
    inpc["cursor"] = productions[prodind][1]["cursor"] # Reposiciona o cursor
    return productions[prodind][0] # Retorna a expansão.

def parse_permutations(inpdata, rules, psel={}, *args, **kwargs):
    '''Tenta interpretar um programa inserido (inpdata) usando as regras fornecidas (rules) através de
    sucessivas interações entre os resultados ambíguos.
    Retorna assim que encontra algum resultado viável. Se não encontrar, retorna None.
    '''
    inpcursor = { "cursor": 0 }
    locked = psel.keys() # Marca as ambiguidades que esse método não deve mexer (pois o método é recursivo)
    ps = psel.copy() # Faça uma cópia completa do dicionário de ambiguidades e passa-o para o método

    # Cada ambiguidade de ps consiste de um endereço completo das derivações das regras.
    r = parse_rule_label(inpcursor, inpdata, rules, "program", ps, *args, **kwargs)
    if not r is None: # Se o método foi bem sucedido, retorna-o!
        return r

    for p in ps: # Senão, olha todas as ambiguidades e permuta-as.
        if not p in locked: # Se a atual pilha pode mexer na ambiguidade
            l = ps[p][1] # Número de ambiguidades para este endereço.
            o = ps[p][0] # Qual ambiguidade foi escolhida.
            for i in range(o + 1, l): # Para cada possível ambiguidade, itere sobre as possíveis ramificações
                ps[p] = (i, l) # Mude a ramificação e chame o método recursivamente.
                rec = parse_permutations(inpdata, rules, ps.copy(), *args, **kwargs)
                if not rec is None: # Se houve sucesso, simplesmente retorna
                    return rec
            ps[p] = (o, l) # Se não houve sucesso, restaure o estado inicial para a próxima iteração.
    return None

def parse_program(inp, rules, *args, **kwargs):
    '''Invoca parse_permutations, recebendo a entrada (pre-processada pelo analisador léxico)
    e o conjunto de regras.
    '''
    def pdt2dict(d):
        dt = d.split("|")
        return {"token": dt[0], "a": dt[0], "class": dt[1], "line": dt[2]}

    return parse_permutations([pdt2dict(d) for d in inp.strip().split("\n")], rules, *args, **kwargs)


def print_help_msg(autoexit=True):
    print('Usage: python sintatico.py [-r -s] {input file} {output file}')
    print('Or:    python sintatico.py [-r -s] {input file}')
    print('Or:    python sintatico.py [-r -s] -i {output file}')
    print('Or:    python sintatico.py [-r -s] -i')
    print('Or:    python sintatico.py -h|--help')
    print('Where -r: Supress exceptions on 1-st level left recursion.')
    print('      -s: Show terminal expansions as strings.')
    print('      -i: Read input from the stdin.')
    print('      -h or --help: Show this message.')
    if autoexit:
        exit()

if __name__ == "__main__":
    """Por padrão, ou recebe o arquivo de entrada como argumento da linha de comando, ou lê o caminho da entrada padrão.
    """
    if '-h' in argv or '--help' in argv:
        print_help_msg()

    cargs = list(filter(lambda x: len(x) != 2 or x[0] != '-', argv[1:]))
    finp, fout = None, None

    if '-i' in argv:
        finp = ''
        try:
            while True:
                finp += input() + '\n'
        except EOFError:
            pass
    else:
        if len(cargs) == 0:
            print_help_msg()
        finp = cargs.pop(0)
        with open(finp, "r") as f:
            finp = f.read()
    
    if len(cargs) == 1:
        fout = cargs[0]

    rules = read_rules(raiseOnLeftRecursion=(not "-r" in argv))
    p0 = parse_program(finp, rules, simple_terminal=('-s' in argv))
    p0json = json.dumps(p0)

    if fout is None:
        print(p0json)
    else:
        with open(fout, "w") as f:
            f.write(p0json)
