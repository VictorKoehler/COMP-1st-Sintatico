import json

class LogTree():
    def __init__(self):
        self.log = []

    def append(self, path, desc, ret, args):
        r = {
            'path': [j for j in path.split('->') if not j.startswith('@')],
            'desc': desc,
            'ret': ret,
            'args': args
        }
        #r['desc'] += " #" + str(len(self.log))
        self.log.append(r)
        return r


    def __logtreeset_node(self, name : str, descendents : list):
        logTreeSetNode = {
            'text': {
                'name': name
            }
        }
        childs = {}
        newcontext = ''
        
        for d, cont, dret, args in descendents:
            if len(d) <= 1:
                newcontext = cont
                if dret != None:
                    logTreeSetNode['HTMLclass'] = 'choosen-node'
            if d:
                child = d[0]
                if not child in childs:
                    childs[child] = []
                childs[child].append((d[1:], cont, dret, args))
            else:
                if isinstance(dret, list):
                    logTreeSetNode['HTMLclass'] = logTreeSetNode.get('HTMLclass', '') + ' leaf-node'
                    #logTreeSetNode['text']['data-foo'] = args
        logTreeSetNode['text']['title'] = newcontext
        logTreeSetNode['children'] = [self.__logtreeset_node(k, v) for k, v in childs.items()]

        if len(childs) == 1: 
            onlychild = logTreeSetNode['children'][0]
            ochildt = onlychild['text']

            if ochildt['name'].isnumeric():
                if ochildt['title'] != logTreeSetNode['text']['title']:
                    logTreeSetNode['text']['title'] += ' / ' + ochildt['title']
                logTreeSetNode['children'] = onlychild['children']

        return logTreeSetNode
    
    def __save(self, path, exp):
        with open(path, 'w') as fh:
            fh.write('var simple_chart_config = \n' + json.dumps(exp) + ';')
        return exp

    def export(self, keep=None):
        treekeys = [(i['path'], i['desc'], i['ret'], i['args']) for i in self.log if not keep or i['path'][0] in keep]
        treestruct = self.__logtreeset_node('Inicio', treekeys)
        return {'chart': {'container': "#OrganiseChart-simple"},'nodeStructure': treestruct}
    
    def export_last_tree(self):
        return self.export(keep=[self.log[-1]['path'][0]])
        #return self.export(keep=['0'])

    def save_export(self, path, *args, **kwargs):
        return self.__save(path, self.export(*args, **kwargs))

    def save_export_last_tree(self, path, *args, **kwargs):
        return self.__save(path, self.export_last_tree(*args, **kwargs))