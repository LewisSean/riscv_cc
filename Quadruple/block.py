from pycparser import c_ast
from pycparser import CParser
from riscv_cc.symtab import symtab_store, SymTab

class Quadruple(object):
    def __init__(self, type, op, arg1, arg2, dest):
        # 四元组类型：0 / 1 / 2 / 3 / 4
        # https://blog.csdn.net/xdz78/article/details/53454685
        self.type = type
        # 四元组
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.dest = dest

    def is_used(self, arg):
        return self.arg1 == arg or self.arg2 == arg



class block(object):
    def __init__(self, id: int, pre = None, suc = None, Quadruples: list = [], in_live_vals: list = [], out_live_vals: list = []):
        if Quadruples is None:
            Quadruples = []
        self.id = id
        self.pre = pre
        self.suc = suc
        self.Quadruples = Quadruples
        self.in_live_vals = in_live_vals
        self.out_live_vals = out_live_vals


class flow_graph(object):
    """
    获取的是一个函数的流图
    所以入口节点应该是FuncDef
    """
    def __init__(self, node: c_ast.FuncDef, symtab: symtab_store):

        if not isinstance(node, c_ast.FuncDef):
            raise NotImplementedError('当前类型节点非FuncDef节点!')

        # 增设entry和exit两个block(不包含实际四元组)，id分别为0和-1
        self.blocks = dict()
        self.blocks[0] = block(0)
        self.blocks[-1] = block(-1)
        self.id_seed = 1
        # 其余四元组的id范围: >= 1
        self._get_blocks(node, symtab)

    def _get_id(self):
        """
        :return: 一个新的block的id
        """
        self.id_seed += 1
        return self.id_seed

    def _get_blocks(self, node: c_ast.FuncDef, symtab):
        """
        找到并生成一个函数内的所有block
        :param ast: c_ast 语法树
        :return: blocks有向图，以entry开始，exit结束
        """
        compound:c_ast.Compound = node.body
        st_fun = symtab.get_symtab_of(compound)
        print(st_fun)

        # 注意，compound.block_items的粒度太小！！！
        for _block in compound.block_items:
            print('------------------------')
            _block.show()

        # 函数体内为空
        if len(compound.block_items) == 0:
            self.blocks[0].suc = self.blocks[-1].id
            self.blocks[-1].pre = self.blocks[0].id
            return

        next_leaders, cur_id = self.gen_block(compound.block_items[0])
        self.blocks[0].suc = cur_id
        self.blocks[cur_id].pre = self.blocks[0].id

        # 函数体仅一个节点，无后继
        if len(next_leaders) == 0:
            self.blocks[cur_id].suc = self.blocks[-1].id
            self.blocks[-1].pre = self.blocks[cur_id].id

        # 函数体有多个节点
        else:
            next_leaders = [[leader, cur_id] for leader in next_leaders]
            # bfs
            while len(next_leaders) != 0:
                total_next_leaders = []
                for leader, parent_id in next_leaders:
                    # 由parent_id的block产生的后继
                    new_leaders, cur_id = self.gen_block(leader)
                    self.blocks[parent_id].suc = cur_id
                    self.blocks[cur_id].pre = parent_id
                    # 新产生的cur_id的block无后继
                    if len(new_leaders) == 0:
                        self.blocks[cur_id].suc = self.blocks[-1].id
                        self.blocks[-1].pre = cur_id
                    # cur_id的block有后继
                    else:
                        total_next_leaders.extend([[leader, cur_id] for leader in new_leaders])
                next_leaders = total_next_leaders

    def _is_leader(self, node: c_ast.Node):
        """
        :param node: 当前遍历ast的节点：c_ast.Node
        :return: bool 是否是leader(一个block的入口语句)
        判断标准：来自王铎
            1 程序的第一个语句
            2 能有条件转移语句或无条件跳转语句到达的语句
            3 紧跟在条件转移语句后面的语句
        """
        pass

    def gen_block(self, u: c_ast.Node):
        """
        当前节点是一个block的leader，顺序产生一个block，并返回后继leaders和生成的block的id
        :param u: node
        :return: list<Node>, id  因为一个block的出口可能有多个，用list
        """

        return [], -1


if __name__=='__main__':
    file = '../c_file/ls1.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab_store(ast)
    # sts.show(ast)

    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('----------------------------------')
            blocks = flow_graph(ch, sts)

