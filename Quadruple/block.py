from pycparser import c_ast
from pycparser import CParser
from copy import deepcopy
from symtab import symtab_store, SymTab, SymTabStore
from Quadruple.quadruple import Quadruple
import re


class MyConstant():
    def __init__(self, value: str, type):
        self.value = value
        self.type = type


class TmpValue():
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.is_addr = False  # 是否保存的是内存地址


class RegPools(dict):
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
    def __init__(self, id: int, ast_nodes: list, pre = None, suc = None, symtab:SymTabStore = None, reg_pool = None, Quadruples: list = None):
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
        self.gen_quadruples(ast_nodes, symtab, self.Quadruples, reg_pool)
        self.in_live_vals = []
        self.out_live_vals = []
        # branch是一个字典，branch[1] = True 表示block如果计算为True,后继block的id是1，用于处理iF.cond和while.cond节点
        self.branch = dict()
        # 如果当前的block是循环体的stmt中的一个block，则loop_end保存从它跳出循环的下一个block的id，用于break
        self.loop_end = None
        # block的命名，cond_id表示是循环体id的判断节点，loop_id表示是循环体id的循环块（多个位于相同循环体内的block共享一个循环体id）
        self.name = ""

    def show_quadruples(self):
        print("block {}:>>>>>>>>>>>>>>>>>>>>>>".format(self.id))
        for item in self.Quadruples:
            print(item)

    def gen_quadruples(self, ast_nodes: list, symtab: SymTabStore, res: list, reg_pool: RegPools):
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
        for node in ast_nodes:
            if isinstance(node, c_ast.Assignment):
                assign(node, symtab, res, reg_pool)
            elif isinstance(node, c_ast.Decl):
                dec(node, symtab, res, reg_pool)


# 处理assignment
def assign(node: c_ast.Assignment, symtab: SymTabStore, res: list, reg_pool: RegPools):

    """
    先处理rvalue，处理lvalue，再执行赋值运算
    ch_name: 
        lvalue  ID/StructRef/ArrayRef/UnaryOp( *k = 100 / ++i: i++不能是左值)
        rvalue  UnaryOp/BinaryOp/Constant/ID/StructRef( p.x  p->x )/ArrayRef( a[100] ) /TernaryOp(= ? a:b)
        注意：枚举类型中的元素都是ID
    """
    # 先处理右值
    arg1 = expr(node.rvalue, symtab, res, reg_pool)
    # 处理左值
    left = node.lvalue
    if isinstance(left, c_ast.ID):
        sym = symtab.get_symtab_of(left).get_symbol(left.name)
        dest = (left.name, sym)
        res.append(Quadruple(node.op, arg1, None, dest))
    else:
        pass


# 处理dec
def dec(node: c_ast.Decl, symtab: SymTabStore, res: list, reg_pool: RegPools):

    # 先处理右值
    if node.init is None:
        return
    if isinstance(node.init, (c_ast.BinaryOp, c_ast.ID, c_ast.Constant, c_ast.UnaryOp, )):
        arg1 = expr(node.init, symtab, res, reg_pool)
    else:
        pass

    # 处理左值
    # 可能的类型：PtrDecl/TypeDecl/ArrayDecl
    left = node.type
    if isinstance(left, c_ast.TypeDecl):
        sym = symtab.get_symtab_of(node).get_symbol(node.name)
        dest = (node.name, sym)

    # 得到四元组
    # 直接赋值
    if not isinstance(node.init, c_ast.InitList):
        res.append(Quadruple('=', arg1, None, dest))
    # 连续赋值，对于struct和array
    else:
        pass

# 处理右值！！！！
def expr(node: c_ast.Node, symtab: SymTabStore, res: list, reg_pool: RegPools, dest = None):
    if isinstance(node, (c_ast.Constant,)):
        node.show(attrnames=True, nodenames=True, showcoord=True)
        return node.value, MyConstant(node.value, node.type)

    elif isinstance(node, (c_ast.ID,)):
        t: SymTab = symtab.get_symtab_of(node)
        sym = t.get_symbol(node.name)
        print(sym)
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

        # 此处我们默认无*(a+3)这种情况，有就将其替换为a[3]
        # 新产生的tmp保存内存地址
        elif node.op == '*' or  node.op == '&':
            arg1 = expr(node.expr, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            tmp[1].is_addr = True
            res.append(Quadruple(node.op, arg1, None, tmp))
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            return tmp

        # - + ~(按位取反) !(逻辑非)
        else:
            arg1 = expr(node.expr, symtab, res, reg_pool)
            tmp = reg_pool.get_reg(arg1[1].type)
            res.append(Quadruple(node.op, arg1, None, tmp))
            if isinstance(arg1[1], TmpValue):
                reg_pool.release_reg(arg1[0])
            return tmp

    elif isinstance(node, (c_ast.BinaryOp, )):
        arg1 = expr(node.left, symtab, res, reg_pool)
        arg2 = expr(node.right, symtab, res, reg_pool)
        tmp = reg_pool.get_reg(arg1[1].type)
        print(">>>>>>>>>>>>>>>>>>  ", tmp[0])
        res.append(Quadruple(node.op, arg1, arg2, tmp))
        if isinstance(arg1[1], TmpValue):
            reg_pool.release_reg(arg1[0])
        if isinstance(arg2[1], TmpValue):
            reg_pool.release_reg(arg2[0])
        return tmp



















