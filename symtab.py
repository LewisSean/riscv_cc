from pycparser import c_ast
from pycparser import CParser

class Symbol():
    def __init__(self,name):
        self.name = name
        self.size = 0 # 以byte计
        self.offset = 0 # 以byte计

    def __repr__(self):
        return '%s,sz=%d,off=%d'%(self.name,self.size,self.offset)
        

class SymTab(dict):
    def __init__(self, node:c_ast.Node, parent=None):
        self.node = node
        self.parent = parent
        if parent is not None:
            self.parent.children.append(self)
        self.children=[]

    def get_symbol(self, name:str) -> Symbol:
        if self.get(name) is not None:
            return self.get(name)
        if self.parent is None:
            return None
        return self.parent.get_symbol(name)
    
    def add_symbol(self, sym:Symbol):
        self[sym.name] = sym

    def __repr__(self):
        ans = '(' + type(self.node).__name__ + ') '
        for x in self.values():
            ans += '['+repr(x)+'] '
        return ans


class SymTabStore():
    def __init__(self, root:c_ast.Node):
        self._symtab={} # dict[c_ast.Node]->SymTab
        self.root = root

    def get_symtab_of(self, node:c_ast.Node) -> SymTab:
        return self._symtab.get(node)
    
    def add_symtab(self, node:c_ast.Node, symtab:SymTab):
        self._symtab[node]=symtab

    def show(self):
        def dfs(u:SymTab):
            ans = repr(u)
            for v in u.children:
                tmp = '  ' + dfs(v)
                tmp = '\n  '.join(tmp.split('\n'))
                ans += '\n' + tmp
            return ans
        root_t = self.get_symtab_of(self.root)
        print(dfs(root_t))

def symtab_store(ast:c_ast.Node) -> SymTabStore:
    '''
    给定一棵语法树,生成该语法树的所有符号表,存储在一个SymTabStore对象中,
    可以从中查询需要的符号表.
    实现方法是dfs遍历.
    '''

    # 符号表仓库 最后要返回的结果
    sts = SymTabStore(ast)

    '''
    辅助函数和变量
    '''

    _dfs_function_pool={}
    
    def register(class_name):
        def _register(f):
            _dfs_function_pool[class_name] = f
        return _register

    offset = 0
    in_func = False
    current_symtab = None 
    # current_symtab是一个动态变化的变量,dfs下降或返回时它的内容发生改变,
    # 它的内容总是当前遍历过程中正在处理的节点的符号表

    def dfs(u:c_ast.Node):
        '''
        此函数将根据u的类型为它选择相应的具体的dfs函数去处理,
        与此同时维护符号表的建立与current_symtab的值
        params:
            u: 要深入遍历的节点
        '''
        nonlocal current_symtab

        if u is None:
            return {}

        t = SymTab(u, parent=current_symtab)
        sts.add_symtab(u, t)

        class_name = type(u).__name__
        if _dfs_function_pool.get(class_name) is None:
            raise NotImplementedError('对于'+class_name+'类型节点的dfs函数尚未实现!')
        dfs_fn = _dfs_function_pool[class_name]

        saved_symtab = current_symtab
        current_symtab = t
        
        res = dfs_fn(u)

        current_symtab = saved_symtab

        return res

    
    '''
    以下是对应到每一种类型的节点的dfs处理函数(加了register注解的这些)
    '''

    @register('FileAST')
    def file_ast(u:c_ast.FileAST):
        nonlocal sts
        t = sts.get_symtab_of(u)
        for v in u.ext:
            symbol = dfs(v)['symbol']
            t.add_symbol(symbol)

    
    @register('Decl')
    def decl(u:c_ast.Decl):
        '''
        生成一个符号,并设置该符号的offset和size.
        如果它的type是FuncDecl,那么还设置该符号的参数个数.
        return:
            symbol: 生成的那个符号
        '''
        nonlocal offset

        if type(u.type).__name__ == 'FuncDecl':
            return dfs(u.type)

        x = Symbol(u.name)
        res = dfs(u.type)
        x.size = res['size']
        x.offset = offset
        offset += x.size
        param_symbols = None
        
        return {'symbol':x}


    @register('TypeDecl')
    def type_decl(u:c_ast.TypeDecl) -> dict:
        '''
        return:
            size: 符号的size,以byte计
        '''
        return dfs(u.type)

    @register('IdentifierType')
    def identifier_type(u:c_ast.IdentifierType) -> dict:
        '''
        return:
            size: 符号的size,以byte计
        '''
        # 将列表中的字符串以空格分割拼接起来s,
        # 若以unsigned开头,则忽略unsigned(因为对计算size来说无所谓)
        id = ' '.join(u.names[1:] if u.names[0]=='unsigned' else u.names) 
        type_size = {
            'void' : 0,
            'char' : 1,
            'short' : 2,
            'int' : 4,
            'long' : 4,
            'long long' : 8
        }
        if type_size.get(id) is None:
            raise NotImplementedError('类型'+id+'尚不支持')

        return {'size' : type_size[id]}

    @register('FuncDecl')
    def func_decl(u:c_ast.FuncDecl):
        nonlocal offset
        func_symbol = Symbol(u.type.declname)
        func_symbol.offset = offset
        func_symbol.size = dfs(u.type)['size']
        offset += func_symbol.size
        res = dfs(u.args)
        symbols=[]
        if res.get('param_symbols') is not None:
            symbols = res['param_symbols']
        size = dfs(u.type)['size']
        func_symbol.param_k = len(symbols)
        return {'func_symbol':func_symbol,'param_symbols':symbols,'size':size}

    @register('ParamList')
    def paramlist(u:c_ast.ParamList):
        symbols = []
        for d in u.params: # d是Decl类型
            symbols.append(dfs(d)['symbol'])
        return {'param_symbols':symbols}
    
    @register('Compound')
    def compound(u:c_ast.Compound):
        nonlocal sts
        t = sts.get_symtab_of(u)
        if u.block_items is not None:
            for v in u.block_items:
                res = dfs(v)
                if res is not None and res.get('symbol') is not None:
                    t.add_symbol(res['symbol'])


    @register('FuncDef')
    def func_def(u:c_ast.FuncDef):
        nonlocal offset, sts
        in_func = True
        saved_offset = offset
        offset = 0

        t = sts.get_symtab_of(u)

        '''
        FuncDef的第一个孩子是Decl.
        在Decl的dfs处理函数中,我们生成一个符号,并设置该符号的offset和size.
        而现在我们令offset=0,那么Decl的dfs处理函数中将生成一个名为此函数名
        的符号,其size是返回值类型的size,offset是0.
        于是,我们约定在函数内部,返回值的offset为0.
        '''
        res = dfs(u.decl)
        x = res['func_symbol'] # 代表此函数本身的符号
        
        for sym in res['param_symbols']: # 此函数的参数的符号
            t.add_symbol(sym)

        dfs(u.body)
        
        offset = saved_offset
        in_func = False
        return {'symbol':x}


    @register('If')
    def if_else(u:c_ast.If):
        dfs(u.iftrue)
        dfs(u.iffalse)

    dfs(ast)
    return sts

if __name__=='__main__':
    file = './c_file/1.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab_store(ast)
    sts.show()