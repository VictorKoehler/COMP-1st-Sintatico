class Semantic():
    knowtypes = { 'integer', 'real', 'boolean', 'procedure', 'function', 'program' }

    def __init__(self): pass
    
    def copy(self):
        return self

    def expup(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        ''' Invocado ao iniciar uma interpretação de regra.
        '''
        return self

    def subexpbeg(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, *args, **kargs):
        ''' Invocado ao iniciar um sub-item de uma iterpretação de regra.
        '''
        return self

    def subexpterm(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        ''' Invocado quando um sub-item de uma interpretação de regra é uma folha/terminal.
        '''
        return self

    def subexpder(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        ''' Invocado quando um sub-item de uma interpretação de regra é uma expansão em outras regras.
        '''
        return self

    def subexpfin(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs) -> str:
        ''' Invocado ao terminar a intepretação de uma regra.
        '''
        return None


__exception_handler = { 'switch': False }
def exception_handler(func):
    ''' Se o switch estiver ligado, então todas as exceções serão convertidas em uma mensagem de erro.
    '''
    def func_wrapper(*args, **kwargs):
        if not __exception_handler['switch']:
            return func(*args, **kwargs)
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            from sys import stderr
            line = 'X'
            try:
                line = args[4][args[3]['cursor']]['line']
            except:
                pass
            print('Line {}: {}'.format(line, exc), file=stderr)
            return args[0]
    return func_wrapper




class IdentifiersRegister(Semantic):
    ''' Registra os identificadores e seus tipos, bem como assegura a existência no uso de identificadores.
    '''

    def __init__(self):
        self.type_waiting = []
        self.args_waiting = []
        self.identifiers = {}
        self.level = 0
        self.scope = None
        self.parent = None

    def _add_id(self, ident, t, line=0, auto_assert=True):
        ''' Tenta adicionar um novo identificador de tipo t no level atual.
        '''
        if auto_assert:
            assert t in self.knowtypes
        if self.identifiers.get(ident, (0, -1))[1] >= self.level:
            raise Exception("Line {}: {} {} was already defined.".format(line, t, ident))
        self.identifiers[ident] = (t, self.level)
    
    def copy(self, level=None, scope=None, parent=None):
        ''' Cria um clone do atual mapeamento de identificadores. Útil para sub-escopos.
        '''
        i = IdentifiersRegister()
        i.identifiers = self.identifiers.copy()
        i.level = level or self.level
        i.scope = scope or self.scope
        i.parent = parent or self
        return i

    @exception_handler
    def subexpbeg(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, *args, **kargs):
        if label == 'escopo_de_subprograma': # Escopo de programas são especialmente úteis para identificar argumentos e retorno.
            if r == '@declaracoes_variaveis' and not self.scope is None: # Se estivermos dentro de um procedimento/função
                self._add_id(self.scope + '#args', self.args_waiting, auto_assert=False) # Registramos seus dados básicos.
                self.parent._add_id(self.scope + '#args', self.args_waiting, auto_assert=False)
                rett = self.get_id_type(self.scope + '#ret')
                if not rett is None:
                    self.parent._add_id(self.scope + '#ret', rett, auto_assert=False)
                self.args_waiting = []
            elif r == '@comando_composto': # Quando entramos para o escopo de lógica,
                return TypeSemantic(self) # começamos a fazer a análise de tipos.
        elif label == 'declaracao_de_subprograma' and r == '@argumentos': # Estamos entrando em um novo escopo partindo daqui.
            n = inpdata[cursor['cursor'] - 1]['token'] # Assim, vamos retornar uma cópia desse atual mapeamento para que os
            return self.copy(self.level+1, n) # identificadores locais não sejam vistos por escopos superiores.
        return self

    @exception_handler
    def subexpterm(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        line = inpdata[cursor['cursor']]['line']
        if t['class'] == 'identificador': # Encontramos um identificador!
            if label.startswith('lista_de_identificadores'): # E estamos juntando uma lista deles!
                self.type_waiting.append(t['token']) # Ainda não sabemos o seu tipo => vá para a lista de espera.
            else: # Se não estamos juntando uma lista deles, então seu tipo deve estar imediatamente antes dele.
                self._add_id(t['token'], inpdata[cursor['cursor'] - 1]['token'], line)
        elif label == 'tipo' and t['class'] == 'reservado': # Encontramos um identificador de tipo!
            for i in self.type_waiting: # Se há alguém esperando para receber um tipo, a hora é esta.
                self._add_id(i, t['token'], line)
                self.args_waiting.append((i, t['token']))
            self.type_waiting.clear() # Todos da lista receberam seu tipo, esvazie-a.
        return self
    
    @exception_handler
    def subexpder(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        if label == 'declaracao_de_subprograma' and r == '@tipo': # Um subprograma que possui um tipo de retorno.
            self._add_id(self.scope + '#ret', t['expansion'][0]['token']) # Colocamos seu tipo discriminado.
        return self
    
    def get_id_type(self, idd, v=None):
        return self.identifiers.get(idd, v)




class ProgramSemantic(IdentifiersRegister):
    ''' Uma variante do IdentifiersRegister especializado para o ínicio do programa.
    '''
    def __init__(self):
        super().__init__()

    def subexpterm(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        if t['class'] == 'identificador':
            self._add_id(t['token'], inpdata[cursor['cursor'] - 1]['token'])
        return self.copy()
    



def _is_generic(t):
    return len(t) == 1 and t.upper() == t

def _is_number(tr, t='Number'):
    return t == 'Number' and (tr == 'real' or tr == 'integer')

def _is_lambda(tr, t='Lambda'):
    return t == 'Lambda' and (tr == 'function' or tr == 'procedure')

def _type_eq(t1, t2):
    return _type_eq_strict(t1, t2) or (_is_number(t1) and _is_number(t2)) or (_is_lambda(t1) and _is_lambda(t2))

def _type_eq_strict(t1, t2):
    return t1 == t2


class TypeSemantic(Semantic):
    ''' Uma classe especializada em verificar a semântica de tipos.
    '''

    def __init__(self, identifiers : IdentifiersRegister):
        self.identifiers = identifiers
    
    def solve_type(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs) -> str:
        p = rscoll[0]
        s = rscoll[1][1:]
        if len(s) == 1:
            return s[0]

    def assert_type(self, r : str, type_return : str, throw=False):
        if r[0] != '#' and ':' in r:
            x = r.split(':')[1]
            if x[-1] == '?':
                x = x[:-1]
            e = x == type_return or _is_generic(x) or _is_number(type_return, x) or _is_lambda(type_return, x)
            if not e and throw:
                raise Exception('Invalid type {} on {}'.format(type_return, r))
            return e
        return True

    @exception_handler
    def subexpterm(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        line = inpdata[cursor['cursor']]['line']
        type_return = None

        if t['class'] == 'identificador': # Se a classe da regra é um identificador, então retorna seu tipo.
            typ = self.identifiers.get_id_type(t['token'])
            if typ is None:
                raise Exception("Line {}: {} is not defined.".format(line, t['token']))
            type_return = typ[0]
        elif r[0] == '%': # Se é um símbolo, talvez possamos resolver seu tipo olhando as regras.
            if len(rscoll[1]) > 0:
                type_return = self.solve_type(label, rscoll, cursor, inpdata, applies, r, t, *args, **kargs)
            else:
                type_return = r[1:]

        # Se ao final o tipo é válido, então dizemos que esta regra-sub-item possui um tipo.
        if not type_return is None and type_return in self.knowtypes and self.assert_type(r, type_return):
            t['type'] = type_return
        return self

    @exception_handler
    def subexpder(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, r : str, t : dict, *args, **kargs):
        if r == '@comando_composto':
            t['scope'] = self.identifiers.identifiers

        line = inpdata[cursor['cursor']]['line']
        type_return = t.get('type', None)

        # Aqui verificamos se o tipo que a subexpressão possui é uma lista de Python.
        # Nesse caso, a convenção que se aplica é que esta é uma tupla de uma chamada de procedimento/função,
        # e deve ser decomposta e verificada contra os tipos dos argumentos da função.
        if isinstance(type_return, list):
            if len(applies) == 0:
                t['type'] = type_return
                return self
            if not _is_lambda(applies[0]['type']): # Uma assertiva. É preciso ser um procedimento/função para
                raise Exception('Type <{}> is not callable.'.format(applies[0]['type'])) # ser invocado como tal.
            
            expected = self.identifiers.identifiers[applies[0]['token'] + '#args'][0] # Os tipos esperados
            if len(expected) != len(type_return): # Se o tamanho das listas diferem, então...
                raise Exception('Invalid number of arguments in {}'.format(applies[0]['token']))

            zipped = zip(expected, type_return) # Um zip entre tipos esperados e fornecidos
            for e, o in zipped: # Para cada tipo, verificamos se existe compatibilidade.
                if not _type_eq(e[1], o):
                    raise Exception('Invalid type coercion between <{}> and <{}> in {}'.format(e[1], o, applies[0]['token']))

            if 'type' in t: # Se sim, então removemos a lista do tipo.
                t.pop('type') # Deixemos nula. Outra parte do código verificará o retorno da função/procedimento.
            type_return = None # Aqui estamos interessados apenas na conferência de parâmetros.

        if not type_return is None and type_return in self.knowtypes and self.assert_type(r, type_return, True):
            t['type'] = type_return
        return self


    def mapping_expressao(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        ''' A regra 'expressao' possui apenas dois tipos de retorno possíveis:
        O tipo de @expressao_simples, ou booleano (quando @expressao_term é diferente da expansão vazia).
        '''
        if len(applies) == 1:
            return applies[0]['type']
        elif _type_eq(applies[0]['type'], applies[1]['type']) and not _is_lambda(applies[0]['type']):
            return 'boolean'
        else:
            t = applies[1]['expansion'][0]['expansion'][0]['token']
            t0 = applies[0]['type']
            t1 = applies[1]['type']
            raise Exception("Operator {} doesn't apply to types <{}> and <{}>".format(t, t0, t1))
    
    def mapping_uso_identificador(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        ''' A regra uso_identificador tem dois propósitos:
        - Atribuição: Nesse caso ambos os lados devem ter tipos equivalentes.
            Além disso, são feitos retornos de funções por meio de atribuição,
            e o mesmo deve acontecer dentro do escopo da função que retorna.
        - Chamada de procedimento: Nesse caso, a verificação de parâmetros já ocorreu.
            Basta verificar se o identificador usado é uma função ou procedimento.
            O retorno é descartado (o retorno só é usado na expansão de fator).
        '''
        t0 = applies[0]['type']
        if len(applies) == 1:
            return 'None'
        t1 = applies[1].get('type', None)
        attribuiton = applies[1]['expansion'][0]['symbol'].startswith('@atribuicao_variavel')

        if attribuiton:
            if t0 == 'function':
                if applies[0]['token'] != self.identifiers.scope:
                    raise Exception("Cannot return <{}> in this scope ({}).".format(applies[0]['token'], self.identifiers.scope))
                t0 = self.identifiers.get_id_type(self.identifiers.scope + '#ret')[0]
            if not (t0 == 'real' and _is_number(t1)) and not _type_eq_strict(t0, t1):
                raise Exception('Invalid attribuition between types <{}> := <{}>'.format(t0, t1))
        else:
            if not _is_lambda(t0):
                raise Exception('Type <{}> is not callable.'.format(t0))
        
        return None

    def ativ_proc_reduc(self, s):
        desc = 2 if 'linha' in s['symbol'] else 1
        t = desc - 1
        rt = [s['expansion'][t]['type']]
        if desc < len(s['expansion']):
            return rt + self.ativ_proc_reduc(s['expansion'][desc])
        else:
            return rt

    def mapping_ativ_proc(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        ''' Durante a ativação de procedimento, buscamos os tipos informados nos parâmetros e colocamos numa lista.
        self.subexpder irá analisar a lista posteriormente.
        '''
        types = []
        if len(applies) == 3:
            types = self.ativ_proc_reduc(applies[1])
        return types

    def mapping_fator(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        ''' A expansão de fator possui apenas uma regra que exige código.
        Essa é a primeira, sendo o uso de um identificador simples ou a chamada de uma função.
        '''
        if len(applies) == 2 and applies[0]['class'] == 'identificador' and applies[1]['symbol'] == '@ativacao_de_procedimento':
            if applies[0]['type'] != 'function': # Se é uma ativação de procedimento, tem que ser uma função.
                raise Exception('Token {}, type <{}>, is not a function.'.format(applies[0]['token'], applies[0]['type']))
            return self.identifiers.identifiers[applies[0]['token'] + '#ret'][0] # O tipo é o retorno da função.
        return None

    @exception_handler
    def subexpfin(self, label : str, rscoll : tuple, cursor : dict, inpdata : str, applies : list, *args, **kargs):
        line = inpdata[cursor['cursor']]['line']
        if len(applies) > 0 and 'type' in applies[0] and isinstance(applies[0]['type'], list):
            return applies[0]['type']
        
        # Ao fim do processamento de todos os sub-itens de uma interpretação de regra,
        # vamos fazer a interpretação final do tipo dessa expansão.
        mappings = {
            'expressao': self.mapping_expressao,
            'fator': self.mapping_fator,
            'uso_identificador': self.mapping_uso_identificador,
            'ativacao_de_procedimento': self.mapping_ativ_proc
            }
        type_return = mappings.get(label, None)
        if not type_return is None: # Se a expansão estiver especialmente mapeada, usa o mapa.
            type_return = type_return(label, rscoll, cursor, inpdata, applies, line=line)

        # Aqui interpretamos as regras de sintaxe adicionais do conjunto de regras semânticas.
        generics = { } # Mapeamento entre regras genéricas (isto é, T, U, V, etc...) e os tipos reais.
        def perobj(i, jj):
            ''' Para cada sub-item, verificamos a regra teórica (i) e a regra gerada (jj).
            '''
            if i[0] == '#': # Se a regra é apenas uma expansão sintática, retorna.
                return [i], jj
            else: # Senão, quebra
                r = i.split(':')[1:]
                j = jj
                #if len(r) > 1 and _is_generic(r[1]):
                for p in r: # r contém as regras genéricas e coerções de tipo.
                    if p[-1] == '?':
                        continue
                    if not 'type' in j:
                        raise Exception('Invalid expansion of rule {}: {}'.format(i, j))
                    if not _is_generic(p): # Se p não é uma regra genérica

                        if p == 'Number': # Se a regra é Number,
                            if not _is_number(j['type']): # precisamos forçar o tipo a ser um número.
                                raise Exception('Not a Number, on expansion of rule {}: {}'.format(i, j))
                            if j['type'] == 'real' or not 'Number' in generics: # Se é um número, então
                                generics['Number'] = j['type'] # força a conversão inteiro-real.
                        elif p == 'Lambda': # Se a regra é Lambda,
                            if not _is_lambda(j['type']): # precisamos forçar o tipo a ser um procedimento.
                                raise Exception('Not a Lambda, on expansion of rule {}: {}'.format(i, j))
                            generics['Lambda'] = j['type']
                        elif p in self.knowtypes and not _type_eq_strict(p, j['type']):
                            raise Exception('Unexpected type mismatch expansion on {}: {}'.format(i, j))
                        continue
                    # if str.isdigit(p):
                    #     if not 'expansion' in j or len(j['expansion']) <= int(p):
                    #         raise Exception('Invalid expansion on rule {}'.format(i))
                    #     j = j['expansion'][int(p)]
                    if not _type_eq(generics.get(p, j['type']), j['type']):
                        raise Exception('Unexpected type mismatch expansion on {}: {}'.format(i, j))
                    if j['type'] != 'integer' or generics.get(p, '') != 'real':
                        generics[p] = j['type']
                return r, j
        p = [perobj(i, j) for i, j in zip(rscoll[0], applies)]
        s = [generics.get(x, x) for x in rscoll[1][1:]]

        if len(s) == 1 and type_return is None:
            type_return = s[0] # Se ainda não sabemos o tipo, vamos tentar interpretar as regras.

        if type_return is None and len(applies) == 1 and 'type' in applies[0]:
            type_return = applies[0]['type']

        if not type_return is None and (isinstance(type_return, list) or type_return in self.knowtypes):
            return type_return
        return None
