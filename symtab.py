from pycparser import c_ast
from pycparser import CParser

class OFFSET():
    GLOBAL = 'global' # 全局偏移 (一个c源文件中的全局变量)
    LOCAL = 'local' # 局部偏移 (局部变量\struct成员变量)

class Symbol():
    def __init__(self, name, size=0, offset=0, offset_type=OFFSET.GLOBAL, type_str=None):
        self.name = name
        self.size = size # 以byte计
        self.offset = offset # 以byte计
        self.offset_type = offset_type # 取值为OFFSET中的常量
        self.type = type_str
        self.Reg=None
        self.isChange=False
        self.inMem=False

    def __repr__(self):
        return '\033[1;33m%s\033[0m,sz=%d,off=%d(%s),type=%s'%(
            self.name,self.size,self.offset,self.offset_type,self.type)

class BasicSymbol(Symbol):
    '''
    基本类型 int short long bool char 等
    '''
    SIZE_OF = {
        'long long':8,
        'long long int':8,
        'long':4,
        'long int':4,
        'signed':4,
        'unsigned':4,
        'int':4,
        'short int':2,
        'short':2,
        'char':1,
        'bool':1
    }
    
    @staticmethod
    def gen_symbol(name:str, type_str:str):
        '''
        若type_str描述的不是一个基本类型则返回None
        '''
        try:
            return BasicSymbol(name, type_str)
        except NotImplementedError:
            return None

    def __init__(self, name, type_str:str):
        super().__init__(name)
        a = type_str.split(' ')
        self.unsigned = False
        if a[0] == 'unsigned':
            self.unsigned = True
            if len(a) > 1:
                a=a[1:]
        a = ' '.join(a)
        szof = BasicSymbol.SIZE_OF
        if szof.get(a) is None:
            raise NotImplementedError('类型"'+a+'"尚不支持')
        self.size = szof[a]
        self.type = a

    def __repr__(self):
        ans = super().__repr__()
        if self.unsigned:
            ans+='(u)'
        return ans

    

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

    def __iter__(self):
        return iter(self.values())

class StructSymbol(Symbol):
    '''
    结构体符号,特别之处是它自身持有一张符号表,记录成员变量信息.
    size: 结构体的总大小
    member_symtab: 成员变量符号表
    '''
    def __init__(self, name, **kwarg):
        super().__init__(name, offset_type=OFFSET.LOCAL, type_str='struct', **kwarg)
        self.member_symtab = SymTab(None)
        self.element_paths = []
        self.atoms = 0

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
    local_symbols: list, 存储了所有局部变量的symbol
    '''
    def __init__(self, name):
        super().__init__(name)
        self.params_symtab = SymTab(None)
        self.frame_size = None
        self.local_symbols = []

    def add_param_symbol(self, sym:Symbol):
        self.params_symtab.add_symbol(sym)

    def __repr__(self):
        ans = super().__repr__()
        params=''
        for name in self.params_symtab.keys():
            params += name+','
        ans+=',params=['+params[:-1]+'],frame_sz='+str(self.frame_size)
        locals=''
        for sym in self.local_symbols:
            locals += sym.name+','
        ans+=',locals=['+locals[:-1]+']'
        return ans

class PointerSymbol(Symbol):
    '''
    指针符号
    size: 指针的大小,所有指针的大小都是固定的4byte
    target_size: 最终指向的元素的大小
    target_type: 最终指向的元素的类型名,str类型
    level: 指针级数 从1开始
    '''
    def __init__(self, name, target_size, target_type=None, level=1, **kwarg):
        super().__init__(name, size=4, type_str='pointer', **kwarg)
        self.target_size = target_size
        self.target_type = target_type
        self.level = level
    
    def __repr__(self):
        ans = super().__repr__()
        ans += '(%d),t_sz=%d,t_type=%s'%(self.level,self.target_size,self.target_type)
        return ans

class ArraySymbol(Symbol):
    '''
    数组符号
    size: 数组的总大小
    element_type: 基本元素的类型
    dims: list, 维度列表dim[i]是从左到右第i维
    '''
    def __init__(self, name, element_type, dims, **kwarg):
        super().__init__(name, type_str = 'array', **kwarg)
        self.element_type = element_type
        self.dims = dims

        self.ks = [1]
        for i in range(len(self.dims)-1, 0, -1):
            self.ks.append(self.ks[-1] * self.dims[i])
        self.len = 1
        for item in self.dims:
            self.len *= item

        if element_type in BasicSymbol.SIZE_OF.keys():
            self.element_size = BasicSymbol.SIZE_OF[element_type]
        else:
            self.element_size = int(self.size / self.len)

    def __repr__(self):
        total = 1
        dims_str=''
        for d in self.dims:
            total *= d
            dims_str += '%d,'%d
        dims_str = '['+dims_str[:-1]+']'
        ans = super().__repr__()+',e_sz=%d,e_type=%s,dims=%s'%(
            self.size//total,self.element_type,dims_str)
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
    
    def get_offset_type():
        if in_func:
            return OFFSET.LOCAL
        else:
            return OFFSET.GLOBAL
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
            if res.get('symbol') is not None:
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
        nonlocal offset, get_offset_type

        if u.init is not None:
            dfs(u.init)

        type_name = type(u.type).__name__
        if type_name == 'FuncDecl':
            return dfs(u.type)

        if type_name == 'PtrDecl':
            res = dfs(u.type)
            x = PointerSymbol(u.name, res['target_size'], res['target_type'],level=res['level'],
                offset=offset, offset_type=get_offset_type()
            )
            offset += x.size
            return {'symbol':x}

        if type_name == 'ArrayDecl':
            res = dfs(u.type)
            size = res['size']
            dims = res['dims']
            total = res['total']
            type_str = res['type']
            x = ArraySymbol(u.name, type_str, dims, 
                size=size*total, offset=offset, offset_type=get_offset_type())
            offset += x.size
            return {'symbol':x}

        res = dfs(u.type)

        x = None

        # 仅定义结构体而不声明变量则name=None
        if u.name is not None:
            x = BasicSymbol.gen_symbol(u.name, res['type'])
            if x is None:
                x = Symbol(u.name, size=res['size'], type_str=res['type'])
            else:
                a = 'haha'
            x.offset = offset
            offset += x.size
            if in_func: x.offset_type = OFFSET.LOCAL

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
        type_str = 'struct '+u.name
        if u.decls is None:
            sym = t.get_symbol(type_str)
            return {'size':sym.size,'type':type_str}

        # 定义一个struct
        saved_offset = offset
        offset = 0 # struct内部成员变量的offset是独立的,和函数一样,因而先置零
        in_struct = True

        size = 0
        struct_symbol = StructSymbol(type_str)
        for d in u.decls:
            res = dfs(d) 
            if res.get('struct_symbol') is not None:
                t.add_symbol(res['struct_symbol'])
            x = res['symbol']
            x.offset_type = OFFSET.LOCAL
            struct_symbol.add_member_symbol(x)
            size += x.size

        struct_symbol.size = size

        in_struct = False
        offset = saved_offset

        return {'size':size, 'struct_symbol':struct_symbol, 'type':type_str}

    @register('TypeDecl')
    def type_decl(u:c_ast.TypeDecl) -> dict:
        return dfs(u.type)

    @register('IdentifierType')
    def identifier_type(u:c_ast.IdentifierType) -> dict:
        '''
        return:
            size: 符号的size,以byte计
            type: 符号的type(str),不忽略unsigned
        '''
        type_str = ' '.join(u.names)

        x = BasicSymbol.gen_symbol('test',type_str)

        if x is None:
            raise NotImplementedError('类型"'+type_str+'"尚不支持')

        return {'size' : x.size, 'type' : type_str}

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
            x = dfs(d)['symbol']
            x.offset_type = OFFSET.LOCAL
            symbols.append(x)
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

        local_symbols = []
        def local_dfs(u:c_ast.Node):
            t = sts.get_symtab_of(u)
            if t is None:
                return 
            for sym in t:
                local_symbols.append(sym)
            for v_name, v in u.children():
                local_dfs(v)
        local_dfs(u.body)
        x.local_symbols = local_symbols

        x.frame_size = offset
        
        offset = saved_offset
        in_func = False
        return {'symbol':x}


    @register('If')
    def if_else(u:c_ast.If):
        dfs(u.cond)
        dfs(u.iftrue)
        dfs(u.iffalse)

    @register('PtrDecl')
    def ptr_decl(u:c_ast.PtrDecl):
        '''
        返回
        target_size: 指向元素的size
        target_type: 指向元素的type
        size: 4(指针的大小)
        type: 'pointer'
        '''
        res = dfs(u.type)
        if res.get('target_size') is not None: # 说明下一级仍然是指针
            target_size = res['target_size']
            target_type = res['target_type']
            level = res['level'] + 1
        else:
            target_size = res['size']
            target_type = res['type']
            level = 1

        return {'target_size': target_size,'target_type': target_type,'size':4,'type':'pointer','level':level}
        
    @register('ArrayDecl')
    def array_decl(u:c_ast.ArrayDecl):
        '''
        返回
        size: 基本元素的size
        type: 基本元素的type(str)
        total: 基本元素的总个数
        dim: 本维度大小
        '''
        dim = int(u.dim.value) # u.dim:Constant
        res = dfs(u.type)
        size = res['size']
        type_str = res['type']
        if isinstance(u.type, c_ast.ArrayDecl):
            total = dim * res['total']
            dims = [dim] + res['dims']
        else:
            total = dim
            dims = [dim]
        
        return {'size':size,'type':type_str,'dims':dims,'total':total}


    @register('Assignment')
    def assign(u):
        dfs(u.rvalue)
        dfs(u.lvalue)

    @register('While')
    def While(u:c_ast.While):
        dfs(u.cond)
        dfs(u.stmt)

    @register('DoWhile')
    def DoWhile(u):
        dfs(u.cond)
        dfs(u.stmt)

    @register('Return')
    def Return(u):
        pass

    @register('Label')
    def Label(u:c_ast.Label):
        dfs(u.stmt)

    @register('Goto')
    def goto(u):
        pass

    @register('UnaryOp')
    def unaryOp(u: c_ast.UnaryOp):
        dfs(u.expr)


    @register('ID')
    def id(u:c_ast.ID):
        pass

    @register('Constant')
    def Constant(u):
        pass

    @register('TernaryOp')
    def TernaryOp(u: c_ast.TernaryOp):
        dfs(u.cond)
        dfs(u.iftrue)
        dfs(u.iffalse)

    @register('BinaryOp')
    def BinaryOp(u: c_ast.BinaryOp):
        dfs(u.left)
        dfs(u.right)

    @register('Cast')
    def Cast(u:c_ast.Cast):
        dfs(u.to_type)
        dfs(u.expr)

    @register('InitList')
    def Cast(u:c_ast.InitList):
        for expr in u.exprs:
            dfs(expr)

    @register('ArrayRef')
    def Cast(u:c_ast.ArrayRef):
        dfs(u.name)
        dfs(u.subscript)

    @register('StructRef')
    def Cast(u:c_ast.StructRef):
        dfs(u.name)
        dfs(u.field)

    @register('Break')
    def Cast(u:c_ast.Break):
        pass

    @register('Continue')
    def Cast(u:c_ast.Continue):
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
