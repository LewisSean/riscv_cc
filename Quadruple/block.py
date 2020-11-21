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
        self.branch = dict()
        # 如果当前的block是循环体的stmt中的一个block，则loop_end保存从它跳出循环的下一个block的id，用于break
        self.loop_end = None
        # block的命名，cond_id表示是循环体id的判断节点，loop_id表示是循环体id的循环块（多个位于相同循环体内的block共享一个循环体id）
        self.name = ""

    def gen_quadruples(self, ast_nodes):
        return []









