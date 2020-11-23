from pycparser import c_ast
from pycparser import CParser

class Symbol():
    def __init__(self, name):
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
        '''
        '''
        self[sym.name] = sym

    def __repr__(self):
        ans = type(self.node).__name__ 
        len_name = len(ans)
        for i,x in enumerate(self.values()):
            if i>0:
                ans += '\n' + ' '*len_name
            ans += ' ['+repr(x)+']'

        return ans

class StructSymbol(Symbol):
    '''
    结构体符号,特别之处是它自身持有一张符号表,记录成员变量信息.
    size: 结构体的总大小
    member_symtab: 成员变量符号表
    '''
    def __init__(self, name):
        super().__init__(name)
        self.member_symtab = SymTab(None)

    def get_member_symbol(self, name:str) -> Symbol:
        return self.member_symtab.get_symbol(name)
    
    def add_member_symbol(self, sym:Symbol):
        self.member_symtab.add_symbol(sym)

    def __repr__(self):
        ans = super().__repr__()
        members=''
        for name in self.member_symtab.keys():
            members += name+','
        ans+=',members=['+members[:-1]+']'
        return ans

class FuncSymbol(Symbol):
    '''
    函数符号
    size: 返回值的size
    params_symtab: 参数符号表
    frame_size: (返回值+参数列表+所有局部变量)的总大小,以byte计
    '''
    def __init__(self, name):
        super().__init__(name)
        self.params_symtab = SymTab(None)
        self.locals_symtab = SymTab(None)
        self.frame_size = None

    def add_param_symbol(self, sym:Symbol):
        self.params_symtab.add_symbol(sym)

    def __repr__(self):
        ans = super().__repr__()
        params=''
        for name in self.params_symtab.keys():
            params += name+','
        ans+=',params=['+params[:-1]+'],frame_sz='+str(self.frame_size)
        return ans

class SymTabStore():
    def __init__(self):
        self._symtab={} # dict[c_ast.Node]->SymTab

    def get_symtab_of(self, node:c_ast.Node) -> SymTab:
        return self._symtab.get(node)
    
    def add_symtab(self, node:c_ast.Node, symtab:SymTab):
        self._symtab[node]=symtab

    def show(self, root:c_ast.Node):
        def dfs(u:SymTab):
            ans = repr(u)
            for v in u.children:
                tmp = '  ' + dfs(v)
                tmp = '\n  '.join(tmp.split('\n'))
                ans += '\n' + tmp
            return ans
        root_t = self.get_symtab_of(root)
        print(dfs(root_t))

def symtab_store(ast:c_ast.Node) -> SymTabStore:
    '''
    给定一棵语法树,生成该语法树的所有符号表,存储在一个SymTabStore对象中,
    可以从中查询需要的符号表.
    实现方法是dfs遍历.
    '''

    # 符号表仓库 最后要返回的结果
    sts = SymTabStore()

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
    in_struct = False
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
            res = dfs(v)
            t.add_symbol(res['symbol'])
            if res.get('struct_symbol') is not None:
                t.add_symbol(res['struct_symbol'])
    
    @register('Decl')
    def decl(u:c_ast.Decl) -> dict:
        '''
        生成一个符号,并设置该符号的offset和size.
        如果它的type是FuncDecl,那么还设置该符号的参数个数.
        然后返回该符号给Decl的上级.注意,Decl并不修改自己的符号表.
        return:
            symbol: 生成的那个符号
            struct_symbol: symbol总是表示定义的变量符号,struct_symbol表示定义的
                           结构体符号(如果有的话).注意symbol和struct_symbol可能
                           同时存在,即在定义结构体的同时也定义了此类型的变量.
            (其他可能的返回值参见FuncDecl的dfs函数)
        '''
        nonlocal offset

        type_name = type(u.type).__name__
        if type_name == 'FuncDecl':
            return dfs(u.type)

        res = dfs(u.type)

        if u.name is not None:
            x = Symbol(u.name)
            x.size = res['size']
            x.offset = offset
            offset += x.size

        struct_symbol = None
        if res.get('struct_symbol') is not None:
            struct_symbol = res['struct_symbol']
        

        return {'symbol':x, 'struct_symbol':struct_symbol}

    @register('Struct')
    def struct(u:c_ast.Struct):
        '''
        语法树中出现Struct有两种情况(暂时发现两种),
        一是定义一个struct,二是使用一个struct.
        使用struct时,decls=None.

        decls不是None时,返回一个符号,否则只返回size
        '''
        nonlocal sts, offset, in_struct

        # 使用一个struct,而不是定义它
        t = sts.get_symtab_of(u)
        if u.decls is None:
            sym = t.get_symbol('struct '+u.name)
            return {'size':sym.size}

        # 定义一个struct
        saved_offset = offset
        offset = 0 # struct内部成员变量的offset是独立的,和函数一样,因而先置零
        in_struct = True

        size = 0
        struct_symbol = StructSymbol('struct '+u.name)
        for d in u.decls:
            res = dfs(d) 
            if res.get('struct_symbol') is not None:
                t.add_symbol(res['struct_symbol'])
            x = res['symbol']
            struct_symbol.add_member_symbol(x)
            size += x.size

        struct_symbol.size = size

        in_struct = False
        offset = saved_offset

        return {'size':size, 'struct_symbol':struct_symbol}

    @register('TypeDecl')
    def type_decl(u:c_ast.TypeDecl) -> dict:
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
        func_symbol = FuncSymbol(u.type.declname)
        func_symbol.offset = offset
        func_symbol.size = dfs(u.type)['size']
        offset += func_symbol.size
        res = dfs(u.args)
        symbols=[]
        if res.get('param_symbols') is not None:
            symbols = res['param_symbols']
        size = dfs(u.type)['size']
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
                if res is not None:
                    if res.get('symbol') is not None:
                        t.add_symbol(res['symbol'])
                    if res.get('struct_symbol') is not None:
                        t.add_symbol(res['struct_symbol'])


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
        x = res['func_symbol'] # 代表此函数本身的符号,类型是FuncSymbol
        
        for sym in res['param_symbols']: # 此函数的参数的符号
            t.add_symbol(sym)
            x.add_param_symbol(sym)

        dfs(u.body)

        x.frame_size = offset
        
        offset = saved_offset
        in_func = False
        return {'symbol':x}


    @register('If')
    def if_else(u:c_ast.If):
        dfs(u.iftrue)
        dfs(u.iffalse)

    @register('Assignment')
    def assign(u):
        dfs(u.rvalue)
        dfs(u.lvalue)

    @register('While')
    def While(u):
        pass

    @register('DoWhile')
    def DoWhile(u):
        pass

    @register('Return')
    def Return(u):
        pass

    @register('Label')
    def Label(u):
        pass

    @register('Goto')
    def goto(u):
        pass

    @register('UnaryOp')
    def unaryOp(u):
        pass

    @register('ID')
    def id(u):
        pass

    @register('Constant')
    def Constant(u):
        pass

    @register('TernaryOp')
    def TernaryOp(u):
        pass

    @register('BinaryOp')
    def BinaryOp(u):
        pass

    dfs(ast)
    return sts

def gen_ast(file:str) -> c_ast.Node:
    parser = CParser()
    with open(file, 'r') as f:
        ast = parser.parse(f.read(), file)
    return ast

if __name__=='__main__':
    file = './c_file/zc2.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab_store(ast)
    sts.show(ast)