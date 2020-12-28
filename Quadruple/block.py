from pycparser import c_ast
from copy import deepcopy
from symtab import symtab_store, SymTab, SymTabStore, StructSymbol, Symbol, ArraySymbol, BasicSymbol
from Quadruple.quadruple import Quadruple, TmpValue, MyConstant


class RegPool(dict):
    def __init__(self, num=32):
        super().__init__()
        self.num = num
        for i in range(num):
            self["R{}".format(i)] = True

    def get_reg(self, type: str):
        for i in range(self.num):
            if self["R{}".format(i)]:
                self["R{}".format(i)] = False
                return "R{}".format(i), TmpValue("R{}".format(i), type)

    def release_reg(self, reg: str):
        self[reg] = True


class Block(object):
    def __init__(self, id: int, ast_nodes: list, pre = None, suc = None, symtab: SymTabStore = None, reg_pool = None, Quadruples: list = None):
        if Quadruples is None:
            self.Quadruples = []
        self.id = id
        if pre is not None:
            self.pre = deepcopy(pre)
        else:
            self.pre = []

        if suc is not None:
            self.suc = deepcopy(suc)
        else:
            self.suc = []

        self.ast_nodes = ast_nodes
        self.branch = dict()
        self.gen_quadruples(ast_nodes, symtab, self.Quadruples, reg_pool)
        # 在最终产生的四元组列表中的起始与结束行数
        self.begin = 0
        self.end = 0
        # branch是一个字典，branch[1] = True 表示block如果计算为True,后继block的id是1，用于处理iF.cond和while.cond节点
        # 如果当前的block是循环体的stmt中的一个block，则loop_end保存从它跳出循环的下一个block的id，用于break
        self.loop_end = None
        self.loop_cond = None
        # block的命名，cond_id表示是循环体id的判断节点，loop_id表示是循环体id的循环块（多个位于相同循环体内的block共享一个循环体id）
        self.name = ""

    def adjust(self):
        for quad in self.Quadruples:
            if quad.dest and quad.dest[1] == 'loc':
                if quad.dest[0].startswith('B_{}'.format(self.id)):
                    quad.dest[0] = "L_{}".format(int(quad.dest[0][quad.dest[0].rfind('_')+1:])+self.begin)

    def complete_quadruples(self):
        # 为每个单一后继的block的四元组末尾添加跳转
        if len(self.suc) == 1:
            if len(self.Quadruples) == 0 or self.Quadruples[-1].dest[1] != 'loc':
                self.Quadruples.append(Quadruple('j', None, None, ["B_{}_0".format(self.suc[0]), 'loc']))

        line = 0
        for quad in self.Quadruples:
            quad.line = line
            line += 1
            if quad.dest and quad.dest[1] == 'loc':
                if quad.dest[0].startswith("B__"):
                    quad.dest[0] = "B_{}_".format(self.id) + quad.dest[0][3:]
                elif quad.dest[0] == 'Break':
                    quad.dest[0] = "B_{}_0".format(self.loop_end)
                elif quad.dest[0] == 'Continue':
                    quad.dest[0] = "B_{}_0".format(self.loop_cond)

        if len(self.branch) != 0:
            for quad in self.Quadruples:
                if quad.dest[1] == 'loc' and quad.dest[0].startswith("B_{}"):
                    if quad.arg2 is not None and quad.arg2[0] == 'True':
                        quad.dest[0] = 'B_{}_0'.format(self.branch[True])
                    else:
                        quad.dest[0] = 'B_{}_0'.format(self.branch[False])

    def show_quadruples(self):
        print("\nquad for block {} >>>>>>>>>>>>>>>>>>>>>>".format(self.id))
        for item in self.Quadruples:
            print(item)

    def gen_quadruples(self, ast_nodes: list, symtab: SymTabStore, res: list, reg_pool: RegPool):
        """
        四元组： op arg1 arg2 dest
        生成四元组的要求：
        1. arg1和arg2要绑定在符号表中的定位
        2. 四元组的运算符的写法规范
        3. 对数组的翻译等
        4. block内的行号 0开始

        运算
            写法规范
                示例 assignment_operator_MODEQUAL ：赋值运算 %=   unary_operator_MINUS ：单目运算 -
            类别
                二元运算：^异或 / | 取或 / & / > / < / + / - / * /  ...   x  y  z
                赋值运算: = / += / \= / *= /  x  y  x
                单目运算 ++/ --： 翻译为  +=/-= x 1 x

        跳转
            写法规范
                0.跳转的位置用符号 b_x_y 表示，其中x为目的block的id，y表示第几行，默认从0开始 （对于块之间的跳转，默认跳往目的block的第一行）

                1.有条件跳转  j= / j!= / j< / j>= / j>   x   y   b_dest_0

                2.无条件跳转  j  x = None  y = None   b_dest_0      (goto)

                3.c = expr ? a : b的翻译：
                    是个块内的跳转
                    step 1: 计算expr = d
                    step 2:  j=  d   1   b_current_l1     (l1:  assignment_operator_EQUALS a _ c)


        内存操作
            unary_operator_AND (&) x _ z
            unary_operator_TIMES (*)  x _ z
            postfix_expression_ARROW (->) x _ z
            =[] x y z  (z = x[y])

        """
        # 处理函数终点
        if self.id == -1:
            res.append(Quadruple("end", None, None, None))
        # 处理分支节点
        elif len(ast_nodes) == 1 and  \
                isinstance(ast_nodes[0], (c_ast.BinaryOp, c_ast.ID, c_ast.Constant, c_ast.UnaryOp)):
            res_bool = expr(ast_nodes[0], symtab, res, reg_pool)
            res.append(Quadruple('j=', res_bool, ['True', MyConstant('true', 'bool')], ["B_{}_0", 'loc']))
            res.append(Quadruple('j', None, None, ["B_{}_0", 'loc']))

        # 处理常规节点
        else:
            for node in ast_nodes:
                if isinstance(node, c_ast.Assignment):
                    assign(node, symtab, res, reg_pool)
                elif isinstance(node, c_ast.Decl):
                    dec(node, symtab, res, reg_pool)

                elif isinstance(node, c_ast.Return):
                    _return(node, symtab, res, reg_pool)

                elif isinstance(node, c_ast.Break):
                    res.append(Quadruple('j', None, None, ['Break', 'loc']))

                elif isinstance(node, c_ast.Continue):
                    res.append(Quadruple('j', None, None, ['Continue', 'loc']))

                elif isinstance(ast_nodes[0], (c_ast.UnaryOp)):
                    arg1 = expr(node, symtab, res, reg_pool)
                    # 函数结束，释放可能的右值中间变量
                    if isinstance(arg1[1], TmpValue):
                        reg_pool.release_reg(arg1[0])


def _return(node: c_ast.Return, symtab: SymTabStore, res: list, reg_pool: RegPool):
    arg1 = expr(node.expr, symtab, res, reg_pool)
    res.append(Quadruple('return', None, None, arg1))
    # 函数结束，释放可能的右值中间变量
    if isinstance(arg1[1], TmpValue):
        reg_pool.release_reg(arg1[0])


# 处理assignment
def assign(node: c_ast.Assignment, symtab: SymTabStore, res: list, reg_pool: RegPool):

    """
    先处理rvalue，处理lvalue，再执行赋值运算
    ch_name: 
        lvalue  ID/StructRef/ArrayRef/UnaryOp( *k = 100 / ++i: i++不能是左值)
        rvalue  UnaryOp/BinaryOp/Constant/ID/StructRef( p.x  p->x )/ArrayRef( a[100] ) /TernaryOp(= ? a:b)
        注意：枚举类型中的元素都是ID
    """
    # 先处理右值
    arg1 = expr(node.rvalue, symtab, res, reg_pool)

    # 再处理左值
    left = node.lvalue
    if isinstance(left, c_ast.ID):
        sym = symtab.get_symtab_of(left).get_symbol(left.name)
        dest = (left.name, sym)
        res.append(Quadruple(node.op, arg1, None, dest))

    elif isinstance(left, c_ast.UnaryOp):
        """
        处理指针的说明，如果一个符号是指针，那么它的symbol的type是pointer，其类型是target_type
        """
        if left.op == '*':
            # case: *p = 100
            if isinstance(left.expr, c_ast.ID):
                sym = get_sym_by_node(left.expr, symtab)
                dest = [left.expr.name, sym]
                res.append(Quadruple('[]=', arg1, ['0', MyConstant('0', sym.target_type)], dest))

            # case: *(p + 1) = 100
            elif isinstance(left.expr, c_ast.BinaryOp):
                _expr = left.expr
                if isinstance(_expr.left, c_ast.ID):
                    sym = get_sym_by_node(_expr.left, symtab)
                    dest = [_expr.left.name, sym]
                    arg2 = expr(_expr.right, symtab, res, reg_pool)
                    res.append(Quadruple('[]=', arg1, arg2, dest))

    elif isinstance(left, c_ast.ArrayRef):
        get_ArrayRef(left, 1, arg1, symtab, res, reg_pool)

    elif isinstance(left, c_ast.StructRef):
        get_structRef(left, 1, arg1, symtab, res, reg_pool)

    # 函数结束，释放可能的右值中间变量
    if isinstance(arg1[1], TmpValue):
        reg_pool.release_reg(arg1[0])


# 处理 a[x][y]
def get_ArrayRef(node:c_ast.ArrayRef, mode, pass_arg, symtab: SymTabStore, res: list, reg_pool: RegPool):
    # mode 1 写地址 arg是arg1   0 读地址 arg是dest
    # 确定维度
    # array[2][3] dims = [2,3]
    # arr[x][y][z]  ----> i * y * z + j * z + k  递推关系
    '''
    sym = get_sym_by_id(node, symtab)
    dest = [sym.name, sym]

    ks = sym.ks
    index = 0
    offset = reg_pool.get_reg(sym.element_type)
    res.append(Quadruple('=', ["0", MyConstant("0", sym.element_type)], None, offset))
    while not isinstance(node.name, str):
        arg = expr(node.subscript, symtab, res, reg_pool)
        tmp = reg_pool.get_reg(sym.element_type)
        res.append(Quadruple('*', arg, [str(ks[index]), MyConstant(str(ks[index]), sym.element_type)], tmp))
        res.append(Quadruple('+=', tmp, None, offset))
        if isinstance(arg[1], TmpValue):
            reg_pool.release_reg(arg[0])
        reg_pool.release_reg(tmp[0])
        node = node.name
        index += 1
    if mode == 1:
        res.append(Quadruple('[]=', pass_arg, offset, dest))
    elif mode == 0:
        res.append(Quadruple('=[]', dest, offset, pass_arg))
    reg_pool.release_reg(offset[0])
    '''
    subscripts = []
    cur = node
    offset = 0
    sym = None
    sym_struct = None
    while not isinstance(cur.name, str):
        tmp = expr(cur.subscript, symtab, res, reg_pool)
        subscripts.append(tmp)

        if isinstance(cur.name, c_ast.StructRef):
            # sym_pre是结构体的sym，sym_struct是结构体的全局定义sym
            offset, sym_struct, sym = get_structRef(cur.name, mode, pass_arg, symtab, res, reg_pool, is_array=True)
            break
        cur = cur.name

    if sym == None:
        sym = get_sym_by_node(cur, symtab)
    arrayRef(subscripts, sym, mode, pass_arg, symtab, res, reg_pool, str(offset), base=sym_struct)


# 处理 *(*(arr+1)+1)   *(p+1) 等*对数组的运算
def get_ArrayRef_by_star(node:c_ast.UnaryOp, mode, pass_arg, symtab: SymTabStore, res: list, reg_pool: RegPool, init_offset='0', base=None):
    subscripts = []
    cur = node
    while isinstance(cur, c_ast.UnaryOp) or isinstance(cur, c_ast.BinaryOp):
        if isinstance(cur, c_ast.UnaryOp):
            # subscripts.append(['0', MyConstant('0', None)])
            cur = cur.expr
        elif isinstance(cur, c_ast.BinaryOp):
            tmp = expr(cur.right, symtab, res, reg_pool)
            subscripts.append(tmp)
            cur = cur.left

    sym = get_sym_by_node(cur, symtab)
    arrayRef(subscripts, sym, mode, pass_arg, symtab, res, reg_pool, init_offset)


def arrayRef(subscripts, sym, mode, pass_arg, symtab: SymTabStore, res: list, reg_pool: RegPool, init_offset='0', base=None):
    if base == None:
        dest = [sym.name, sym]
    else:
        dest = [base.name, base]
    # 传递的是地址
    if len(subscripts) != len(sym.dims):
        is_addr = True
    else:
        is_addr = False

    index = -1
    offset = reg_pool.get_reg('int')
    res.append(Quadruple('=', ['0', MyConstant('0', 'int')], None, offset))
    for i in range(len(subscripts)):
        tmp = reg_pool.get_reg('int')
        subscripts[index][1].type = 'int'
        res.append(
            Quadruple('*', subscripts[index], [str(sym.ks[index]), MyConstant(str(sym.ks[index]), 'int')], tmp))
        res.append(Quadruple('+=', tmp, None, offset))
        reg_pool.release_reg(tmp[0])
        index -= 1

    _size = str(sym.element_size)
    res.append(Quadruple('*', offset, [_size, MyConstant(_size, 'int')], offset))
    if init_offset != '0':
        res.append(Quadruple('+=', [init_offset, MyConstant(init_offset, 'int')], None, offset))

    for item in subscripts:
        if isinstance(item[1], TmpValue):
            reg_pool.release_reg(item[0])

    if not is_addr:
        if mode == 1:
            res.append(Quadruple('[]=', pass_arg, offset, dest))
        elif mode == 0:
            res.append(Quadruple('=[]', dest, offset, pass_arg))

    else:
        if mode == 0:
            tmp = reg_pool.get_reg('int')
            res.append(Quadruple('+', dest, offset, tmp))
            res.append(Quadruple('=', tmp, None, pass_arg))
            reg_pool.release_reg(tmp[0])
    reg_pool.release_reg(offset[0])


def get_sym_by_node(node, symtab):
    t: SymTab = symtab.get_symtab_of(node)
    while not isinstance(node.name, str):
        node = node.name
    if isinstance(node, c_ast.Struct) and not node.name.startswith('struct'):
        node.name = 'struct ' + node.name
    sym = t.get_symbol(node.name)
    return sym


def get_sym_by_name(node, name: str, symtab):
    t: SymTab = symtab.get_symtab_of(node)
    sym = t.get_symbol(name)
    return sym

# 前闭后开
def variable_init(node: c_ast.Decl, dest, arg1, res, symtab, reg_pool, offset=None, arr_sym=None, struct_arr=False, arr_struct=False, struct_sym=None, start_index=0, end_index=None):
    if offset is None:
        offset = 0
    if end_index is None:
        end_index = len(arg1)

    if not isinstance(node.init, c_ast.InitList):
        res.append(Quadruple('=', arg1, None, dest))
        return

    # 连续赋值，对于struct和array
    elif isinstance(node.init, c_ast.InitList):
        if arr_sym[1].type == 'array':
            # 数组元素不是结构体
            if not arr_sym[1].element_type.startswith("struct"):
                interval = arr_sym[1].element_size
                if offset == 0:
                    for i, arg in enumerate(arg1[start_index:end_index]):
                        res.append(
                            Quadruple('[]=', arg, [str(i * interval), MyConstant(str(i * interval), "int")], dest))
                        offset += interval
                else:
                    my_interval = [str(interval), MyConstant(str(interval), "int")]
                    addr = reg_pool.get_reg('int')
                    res.append(Quadruple('=', [str(offset), MyConstant(str(offset), 'int')], None, addr))
                    for arg in arg1[start_index:end_index]:
                        res.append(Quadruple('[]=', arg, addr, dest))
                        res.append(Quadruple('+=', my_interval, None, addr))
                        offset += interval
                    reg_pool.release_reg(addr[0])
                return offset
            # 数组元素是结构体
            else:
                if not struct_sym:
                    struct_sym: StructSymbol = get_sym_by_name(node, dest[1].element_type, symtab)
                    if len(struct_sym.element_paths) == 0:
                        pre = []
                        sequence_struct(struct_sym, [0], node, struct_sym.element_paths, symtab, pre)
                        get_struct_atoms(struct_sym, symtab.get_symtab_of(node))

                for i in range(arr_sym[1].len):
                    offset = variable_init(node, dest, arg1, res, symtab, reg_pool, offset=offset, arr_sym=[struct_sym.name, struct_sym], arr_struct=True,
                                           struct_sym=struct_sym, start_index=start_index, end_index=start_index+struct_sym.atoms)
                    start_index += struct_sym.atoms
                return offset

        # 结构体
        elif isinstance(node.type.type, c_ast.Struct) or arr_struct:
            # struct中含有数组时，如果数组是struct最后一个元素，则可以不用预定义长度，由编译器计算
            # 否则必须有长度，我们默认定义的数组都有长度
            if not arr_struct:
                sym = get_sym_by_node(node.type.type, symtab)
            else:
                sym = struct_sym
            if len(sym.element_paths) == 0:
                pre = []
                sequence_struct(sym, [0], node, sym.element_paths, symtab, pre)
                get_struct_atoms(sym, symtab.get_symtab_of(node))

            i = start_index
            for index in range(len(sym.element_paths)):
                # struct当前的元素不是数组
                if len(sym.element_paths[index]) == 4:
                    addr = reg_pool.get_reg('int')
                    res.append(Quadruple('=', [str(offset), MyConstant(str(offset), 'int')], None, addr))
                    res.append(Quadruple('[]=', arg1[i], addr, dest))

                    # res.append(Quadruple('+=', [str(sym.element_paths[index][3]),
                    #                            [str(sym.element_paths[index][3]), 'int']], None, addr))
                    offset += sym.element_paths[index][3]
                    reg_pool.release_reg(addr[0])
                    i += 1
                # struct当前元素是数组

                else:
                    offset = variable_init(node, dest, arg1, res, symtab, reg_pool, offset, struct_arr=True, arr_sym=sym.element_paths[index][1],
                                           start_index=i, end_index=i+sym.element_paths[index][3])
                    i += sym.element_paths[index][3]

            return offset


# 需要重构！！！！！
def dec(node: c_ast.Decl, symtab: SymTabStore, res: list, reg_pool: RegPool):

    # 先处理右值
    if node.init is None:
        return
    if isinstance(node.init, (c_ast.BinaryOp, c_ast.ID, c_ast.Constant, c_ast.UnaryOp,\
                              c_ast.TernaryOp, c_ast.InitList, c_ast.ArrayRef)):
        arg1 = expr(node.init, symtab, res, reg_pool)
    else:
        pass

    # 处理左值
    # 可能的类型：PtrDecl/TypeDecl/ArrayDecl
    left = node.type
    sym = get_sym_by_node(node, symtab)
    dest = [sym.name, sym]

    '''
    if not isinstance(node.init, c_ast.InitList):
        res.append(Quadruple('=', arg1, None, dest))

    # 连续赋值，对于struct和array
    elif isinstance(node.init, c_ast.InitList):
        if isinstance(left, c_ast.ArrayDecl):
            if not dest[1].element_type.startswith("struct"):
                interval = dest[1].element_size
                for i, arg in enumerate(arg1):
                    res.append(Quadruple('[]=', arg, [str(i*interval), MyConstant(str(i*interval), "int")], dest))
            # 数组的元素是结构体
            else:
                struct_sym: StructSymbol = get_sym_by_name(node, dest[1].element_type, symtab)
                if len(struct_sym.element_paths) == 0:
                    pre = []
                    sequence_struct(struct_sym, [0], node, struct_sym.element_paths, symtab, pre)
                    get_struct_atoms(struct_sym, symtab.get_symtab_of(node))
                offset_reg = reg_pool.get_reg('int')
                res.append(Quadruple('=', ['0', MyConstant('0','int')], None, offset_reg))
                interval = dest[1].element_size
                i = 0
                for _ in range(dest[1].len):
                    for index in range(len(struct_sym.element_paths)):
                            if len(struct_sym.element_paths[index]) == 4:
                                res.append(Quadruple('[]=', arg1[i], offset_reg, dest))
                                res.append(Quadruple('+=', [str(struct_sym.element_paths[index][3]),
                                                  MyConstant(str(struct_sym.element_paths[index][3]), "int")], None, offset_reg))
                                i += 1
                            else:
                                # 该元素是数组
                                for ii in range(struct_sym.element_paths[index][3]):
                                    dis = struct_sym.element_paths[index][4]
                                    res.append(Quadruple('[]=', arg1[i + ii], offset_reg, dest))
                                    res.append(Quadruple('+=', [str(dis), MyConstant(str(dis), "int")], None, offset_reg))
                                i += struct_sym.element_paths[index][3]
                reg_pool.release_reg(offset_reg[0])

        if isinstance(left.type, c_ast.Struct):
            # struct中含有数组时，如果数组是struct最后一个元素，则可以不用预定义长度，由编译器计算
            # 否则必须有长度，我们默认定义的数组都有长度
            sym = get_sym_by_node(left.type, symtab)
            if len(sym.element_paths) == 0:
                pre = []
                sequence_struct(sym, [0], node, sym.element_paths, symtab, pre)
                get_struct_atoms(sym, symtab.get_symtab_of(node))
            get_struct_atoms(sym, symtab.get_symtab_of(node))
            i = 0
            for index in range(len(sym.element_paths)):
                if len(sym.element_paths[index]) == 4:
                    res.append(Quadruple('[]=', arg1[i],
                                     [str(sym.element_paths[index][0]), MyConstant(str(sym.element_paths[index][0]), "int")],
                                     dest))
                    i += 1
                else:
                    # 该元素是数组
                    for ii in range(sym.element_paths[index][3]):
                        addr = str(sym.element_paths[index][0] + ii * sym.element_paths[index][4])
                        res.append(Quadruple('[]=', arg1[i+ii],
                                             [str(addr),
                                              MyConstant(str(addr), "int")], dest))
                    i += sym.element_paths[index][3]

    '''
    variable_init(node, dest, arg1, res, symtab, reg_pool, arr_sym=dest)

    # 函数结束，释放可能的右值中间变量
    if isinstance(node.init, c_ast.InitList):
        for arg in arg1:
            if isinstance(arg[1], TmpValue):
                reg_pool.release_reg(arg[0])
    elif isinstance(arg1[1], TmpValue):
        reg_pool.release_reg(arg1[0])


def get_structRef(node: c_ast.StructRef, mode, pass_arg, symtab, res, reg_pool, is_array=None):
    # mode 1 写地址
    path = []
    cur = node
    while not isinstance(cur.name, str):
        path.append(cur.field.name)
        cur = cur.name
    sym = get_sym_by_node(cur, symtab)
    sym_struct = get_sym_by_name(cur, sym.type, symtab)
    path = path[::-1]
    target_item = None
    for item in sym_struct.element_paths:
        if path == item[2]:
            target_item = item
            break
    offset = str(target_item[0])
    if is_array:
        return offset, sym, target_item[1][1]
    if mode == 1:
        res.append(Quadruple('[]=', pass_arg, [offset, MyConstant(offset, 'int')], [sym.name, sym]))

    elif mode == 0:
        res.append(Quadruple('=[]', [sym.name, sym], [offset, MyConstant(offset, 'int')], pass_arg))


# 将struct的元素一维化，解决struct嵌套struct问题
# 返回res[arg]
def sequence_struct(sym: StructSymbol, offset, node, res: list, symtab, pre):
    for k in sym.member_symtab.keys():
        if not sym.member_symtab[k].type.startswith('struct'):
            # 正常元素
            if sym.member_symtab[k].type != 'array':
                pre.append(k)
                res.append((offset[-1], [k, sym.member_symtab[k]], deepcopy(pre), sym.member_symtab[k].size))
                pre.pop()
                offset.append(offset[-1]+sym.member_symtab[k].size)
            else:
                # 结构体中的属性数组，元素不是结构体
                if not sym.member_symtab[k].element_type.startswith('struct'):
                    pre.append(k)
                    res.append((offset[-1], [k, sym.member_symtab[k]], deepcopy(pre), sym.member_symtab[k].len,
                                sym.member_symtab[k].element_size))
                    pre.pop()
                    offset.append(offset[-1] + sym.member_symtab[k].size)
                # 结构体中的属性数组，元素是结构体
                else:
                    t: SymTab = symtab.get_symtab_of(node)
                    new_sym = t.get_symbol(sym.member_symtab[k].element_type)
                    pre.append(k)
                    res.append((offset[-1], [k, new_sym], deepcopy(pre), sym.member_symtab[k].len,
                                sym.member_symtab[k].element_size))
                    pre.pop()
                    offset.append(offset[-1] + sym.member_symtab[k].size)
        else:
            t: SymTab = symtab.get_symtab_of(node)
            new_sym = t.get_symbol(sym.member_symtab[k].type)
            pre.append(k)
            sequence_struct(new_sym, offset, node, res, symtab, pre)
            pre.pop()


# 返回一个struct结构的原子变量（非数组和struct）的个数
def get_struct_atoms(struct_sym: StructSymbol, symtab: SymTab):
    if struct_sym.atoms != 0:
        return struct_sym.atoms
    for k in struct_sym.member_symtab.keys():
        if struct_sym.member_symtab[k].type != 'array' and not struct_sym.member_symtab[k].type.startswith('struct'):
            struct_sym.atoms += 1
        elif struct_sym.member_symtab[k].type == 'array':
            if struct_sym.member_symtab[k].element_type in BasicSymbol.SIZE_OF:
                struct_sym.atoms += struct_sym.member_symtab[k].len
            else:
                new_sym: StructSymbol = symtab.get_symbol(struct_sym.member_symtab[k].element_type)
                num = get_struct_atoms(new_sym, symtab)
                struct_sym.atoms += num * struct_sym.member_symtab[k].len
        else:
            new_sym: StructSymbol = symtab.get_symbol(struct_sym.member_symtab[k].type)
            num = get_struct_atoms(new_sym, symtab)
            struct_sym.atoms += num
    print(struct_sym.name + "--------" + str(struct_sym.atoms))
    return struct_sym.atoms


# 处理右值表达式！！！！
def expr(node: c_ast.Node, symtab: SymTabStore, res: list, reg_pool: RegPool, dest = None):
    if isinstance(node, (c_ast.Constant,)):
        node.show(attrnames=True, nodenames=True, showcoord=True)
        return node.value, MyConstant(node.value, node.type)

    elif isinstance(node, (c_ast.ID,)):
        t: SymTab = symtab.get_symtab_of(node)
        sym = t.get_symbol(node.name)
        return node.name, sym

    elif isinstance(node, (c_ast.UnaryOp, )):
        # ++i
        if node.op == '++' or node.op == '--':
            arg1 = expr(node.expr, symtab, res, reg_pool)
            res.append(Quadruple(node.op, arg1, None, arg1))
            return arg1
        # i++
        elif node.op == 'p++' or node.op == 'p--':
            arg1 = expr(node.expr, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            res.append(Quadruple('=', arg1, None, tmp))
            res.append(Quadruple(node.op[1:], arg1, None, arg1))
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            return tmp

        # 处理指针运算，注意二级指针
        elif node.op == '*':
            # case: tmp = *p
            if isinstance(node.expr, c_ast.ID):
                sym = get_sym_by_node(node.expr, symtab)
                arg1 = [node.expr.name, sym]

                if sym.type == 'pointer':
                    # 处理一级指针
                    if sym.level == 1:
                        tmp = reg_pool.get_reg('int')
                        res.append(Quadruple('=[]', arg1, ['0', MyConstant('0', 'int')], tmp))

                    # 处理二级指针，返回的是指针变量当前保存的地址！！！！
                    elif sym.level == 2:
                        tmp = reg_pool.get_reg('int')
                        res.append(Quadruple('=', arg1, None, tmp))
                        tmp[1].is_addr = True

                # 处理数组 如：p = *array
                if sym.type == 'array':
                    tmp = reg_pool.get_reg('int')
                    get_ArrayRef_by_star(node, 0, tmp, symtab, res, reg_pool)

                return tmp

            # case: tmp = *(p + 1)
            elif isinstance(node.expr, c_ast.BinaryOp):
                tmp = reg_pool.get_reg('int')
                get_ArrayRef_by_star(node, 0, tmp, symtab, res, reg_pool)
                return tmp
        # - + ~(按位取反) !(逻辑非) &(注意！！，保存的是地址)
        else:
            arg1 = expr(node.expr, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            res.append(Quadruple(node.op, arg1, None, tmp))
            if node.op == '&':
                tmp[1].is_addr = True
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            return tmp

    elif isinstance(node, (c_ast.BinaryOp, )):
        if node.op not in ('>=', '>', '==', '<=', '<', '!='):
            arg1 = expr(node.left, symtab, res, reg_pool)
            arg2 = expr(node.right, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            res.append(Quadruple(node.op, arg1, arg2, tmp))
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            if isinstance(arg2[1], TmpValue):
                reg_pool.release_reg(arg2[0])
            return tmp
        # 处理布尔运算
        else:
            arg1 = expr(node.left, symtab, res, reg_pool)
            arg2 = expr(node.right, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            cur_line = len(res)
            res.append(
                Quadruple('j'+node.op, arg1, arg2, ["B__{}".format(cur_line + 3), 'loc']))
            res.append(Quadruple('=', ['False', MyConstant('false', 'bool')], None, tmp))
            res.append(Quadruple('j', None, None, ["B__{}".format(cur_line + 4), 'loc']))
            res.append(Quadruple('=', ['True', MyConstant('true', 'bool')], None, tmp))
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            if isinstance(arg2[1], TmpValue):
                reg_pool.release_reg(arg2[0])
            return tmp

    elif isinstance(node, c_ast.TernaryOp):
        bool_res = expr(node.cond, symtab, res, reg_pool)
        arg1 = expr(node.iftrue, symtab, res, reg_pool)
        arg2 = expr(node.iffalse, symtab, res, reg_pool)
        tmp = reg_pool.get_reg(arg1[1].type)
        cur_line = len(res)
        res.append(Quadruple('j=', bool_res, ['True', MyConstant('true', 'bool')], ["B__{}".format(cur_line + 3), 'loc']))
        res.append(Quadruple('=', arg2, None, tmp))
        res.append(Quadruple('j', None, None, ["B__{}".format(cur_line + 4), 'loc']))
        res.append(Quadruple('=', arg1, None, tmp))
        if isinstance(arg1[1], TmpValue):
            reg_pool.release_reg(arg1[0])
        if isinstance(arg2[1], TmpValue):
            reg_pool.release_reg(arg2[0])
        return tmp

    # 处理右值的数组引用
    elif isinstance(node, c_ast.ArrayRef):
        tmp = reg_pool.get_reg('int')
        get_ArrayRef(node, 0, tmp, symtab, res, reg_pool)
        return tmp

    elif isinstance(node, c_ast.StructRef):
        tmp = reg_pool.get_reg('int')
        get_structRef(node, 0, tmp, symtab, res, reg_pool)
        return tmp

    elif isinstance(node, c_ast.InitList):
        tmps = []
        for _expr in node.exprs:
            tmps.append(expr(_expr, symtab, res, reg_pool))
        return tmps




















