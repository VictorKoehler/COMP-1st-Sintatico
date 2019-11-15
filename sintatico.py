from rules_reader import read_rules
from sys import argv

def parse_rule(inpc, rules, rule):
    rules[1][rules[0][rule]]['expr_rules']

def parse_program(inp, rules):
    inpc = {'data': inp.strip().split('\n'), 'cursor': 0}
    return parse_rule(inpc, rules, 'program')

if __name__ == "__main__":
    '''Por padrão, ou recebe o arquivo de entrada como argumento da linha de comando, ou lê o caminho da entrada padrão.
    '''
    rules = read_rules(raiseOnLeftRecursion= (not '-r' in argv))
    inp = argv[1] if len(argv) >= 2 else input()
    with open(inp, 'r') as f:
        inp = f.read()
    p0 = parse_program(inp, rules)
    
    # if '-u' in argv:
    #     for i in p0:
    #         print('{}|{}|{}'.format(i['token'], i['state'], i['linecounter']))
    # else:
    #     beauty_print(p0)