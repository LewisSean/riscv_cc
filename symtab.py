from pycparser import c_ast

class Symbol():
    def __init__(self,name):
        self.name=name

class SymTab(dict):
    def __init__(self,parent=None):
        self.parent=parent
        self.parent.chidlren.append(self)
        self.children=[]

    def get_symbol(self, name:str) -> Symbol:
        for sym in self.values():
            if sym.name == name:
                return sym
        if self.parent is None:
            return None
        return self.parent.get_symbol(name)

class SymTabStore():
    def __init__(self):
        self._symtab={} # dict[c_ast.Node]->SymTab

    def get_symtab_of(self, node:c_ast.Node) -> SymTab:
        return self._symtab.get(node)
    
    def add_symtab(self, node:c_ast.Node, symtab:SymTab):
        self._symtab[node]=symtab

def symtab_store(ast:c_ast.Node) -> SymTabStore:
    '''
    给定一棵语法树,生成该语法树的所有符号表,存储在一个SymTabStore对象中,
    可以从中查询需要的符号表.
    实现方法是dfs遍历.
    '''
    sts = SymTabStore()

    







    return sts














print('hello')
