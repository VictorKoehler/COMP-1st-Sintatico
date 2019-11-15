import re

empty_char = '£'

def read_rules(filename='regras', raiseOnLeftRecursion=True):
    plain = None
    with open(filename, 'r') as f:
        plain = f.read()
    plain = re.sub(r'//.*?(\r\n?|\n)|/\*.*?\*/', '', plain, flags=re.S)
    plain = re.sub(r'\s+', ' ', plain)
    matches = re.findall(r'\w+ ?={[^}]*}', plain, flags=re.S)
    
    def map_expression(e):
        ret = {}
        ret['name'] = e[:e.index('={')].strip()
        
        def map_rule(r):
            def map_rule_item(ri):
                specialchars = '#@$%'
                if not ri[0] in specialchars and ri != empty_char:
                    raise Exception('Invalid rule of {}: {} ({})'.format(ret['name'], r, ri))
                return ri
            
            rule = [map_rule_item(ri) for ri in r.split(' ') if len(ri) > 0]
            if rule[0] == '@' + ret['name']:
                msg = '1st-Level Left Recursion in {}: {}'.format(ret['name'], r)
                if raiseOnLeftRecursion:
                    raise Exception(msg)
                else:
                    print(msg)
            return rule
        
        ret['expr_rules'] = [map_rule(r) for r in e[e.index('={')+2:-1].strip().split('|')]
        return ret

    ret = [map_expression(m) for m in matches]
    return { ret[i]['name']: i for i in range(len(ret)) }, ret
