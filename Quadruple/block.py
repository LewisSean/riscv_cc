from pycparser import c_ast
from pycparser import CParser
from copy import deepcopy
from riscv_cc.symtab import symtab_store, SymTab
from riscv_cc.Quadruple.quadruple import Quadruple


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
        self.Quadruples = Quadruples
        self.in_live_vals = in_live_vals
        self.out_live_vals = out_live_vals
        self.branch = dict()
        self.loop_end = None
        self.name = ""

    def gen_quadruples(self, ast_nodes):
        return []









