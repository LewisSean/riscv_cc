from pycparser import c_ast
from pycparser import CParser
from copy import deepcopy
from symtab import symtab_store, SymTab
from Quadruple.quadruple import Quadruple


class Block(object):
    def __init__(self, id: int, ast_nodes: list, pre = None, suc = None, Quadruples: list = [], in_live_vals: list = [], out_live_vals: list = []):
        if Quadruples is None:
            Quadruples = []
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
        self.Quadruples = self.gen_quadruples(ast_nodes)
        self.in_live_vals = in_live_vals
        self.out_live_vals = out_live_vals
        # branch是一个字典，branch[1] = True 表示block如果计算为True,后继block的id是1，用于处理iF.cond和while.cond节点
        self.branch = dict()
        # 如果当前的block是循环体的stmt中的一个block，则loop_end保存从它跳出循环的下一个block的id，用于break
        self.loop_end = None
        # block的命名，cond_id表示是循环体id的判断节点，loop_id表示是循环体id的循环块（多个位于相同循环体内的block共享一个循环体id）
        self.name = ""

    def gen_quadruples(self, ast_nodes):
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
        return []









