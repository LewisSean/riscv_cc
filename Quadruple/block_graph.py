from pycparser import c_ast
from pycparser import CParser
from copy import deepcopy
from symtab import symtab_store, SymTab
from Quadruple.quadruple import Quadruple
from Quadruple.block import Block


class FlowGraph(object):
    """
    获取的是一个函数的流图
    所以入口节点应该是FuncDef
    """
    def __init__(self, node: c_ast.FuncDef, symtab: symtab_store):

        if not isinstance(node, c_ast.FuncDef):
            raise NotImplementedError('当前类型节点非FuncDef节点!')

        # bof 函数体的开始
        self.bof = True
        # 增设entry和exit两个block(不包含实际四元组)，id分别为0和-1
        self.blocks = dict()
        self.blocks[0] = Block(0, [])
        self.blocks[-1] = Block(-1, [])
        self.id_seed = 0
        self.loop_seed = 0
        # 其余四元组的id范围: >= 1
        compound: c_ast.Compound = node.body
        self.symtab = symtab.get_symtab_of(compound)
        self.labels = {}
        self._gen_blocks([compound], [0], [-1])
        self._complete_graph()
        self.show()

    # 包括完善前驱后继以及回填
    def _complete_graph(self):
        for k in self.blocks.keys():
            for pre in self.blocks[k].pre:
                if k not in self.blocks[pre].suc:
                    self.blocks[pre].suc.append(k)
        for k in self.blocks.keys():
            for suc in self.blocks[k].suc:
                if k not in self.blocks[suc].pre:
                    self.blocks[suc].pre.append(k)

        # 回填跳出循环的位置，针对break和continue
        for k in self.blocks.keys():
            for pre in self.blocks[k].pre:
                if self.blocks[pre].name.startswith("cond"):
                    loop_id = self.blocks[pre].name[self.blocks[pre].name.find("_") + 1:]
                    _name = "loop_{}".format(loop_id)

                    for i in self.blocks.keys():
                        if self.blocks[i].name == _name:
                            self.blocks[i].loop_end = k

    def show(self):
        print("\n\nblocks are as follows: \n")
        for k in self.blocks.keys():
            print("id {},  pre: {}, suc: {}".format(self.blocks[k].id, self.blocks[k].pre, self.blocks[k].suc))
            print("name: {}, {}".format(self.blocks[k].name, self.blocks[k].loop_end))
            for node in self.blocks[k].ast_nodes:
                print(str(type(node)))
            print('..................................')

    def _get_id(self):
        """
        :return: 一个新的block的id
        """
        self.id_seed += 1
        return self.id_seed

    def _get_loop_id(self):
        """
        :return: 一个新的loop部分的loopid
        """
        self.loop_seed += 1
        return self.loop_seed

    def _gen_blocks(self, nodes: list, pres: list, sucs: list = None):
        """
        递归函数，产生当前节点(们)的所有block
        :param node: 当前节点列表
        :param pres: 前驱节点id的列表
        :param sucs: 后继节点id的列表
        :return:   返回产生的所有block中的入口blocks和出口blocks的id
        """
        # 如果当前节点数大于1，则说明这些节点是可以组成一个block的
        if len(nodes) > 1:
            new_id = self._get_id()
            self.blocks[new_id] = Block(new_id, nodes, pres, sucs)

            return [new_id], [new_id]

        # 单个节点，且自组成一个block
        elif not self._is_new_block(nodes[0]):
            new_id = self._get_id()
            self.blocks[new_id] = Block(new_id, nodes, pres, sucs)

            return [new_id], [new_id]
        # 处理单个节点，往往需要对子节点递归调用，反例：只有一个四元组的block
        else:
            node = nodes[0]
            # 处理compound节点
            # 注意compound嵌套
            if isinstance(node, c_ast.Compound):
                # 列表为空
                if len(node.block_items) == 0:
                    new_id = self._get_id()
                    self.blocks[new_id] = Block(new_id, [], pres, sucs)

                    return [new_id], [new_id]

                # blocks：存储compound内部所有相同block的节点的列表
                blocks_list = []
                block_nodes = []
                for _block in node.block_items:
                    # print('------------------------')
                    # _block.show()

                    if not (self._is_end(_block) or self._is_new_block(_block)):
                        block_nodes.append(_block)

                    elif self._is_end(_block):
                        block_nodes.append(_block)
                        blocks_list.append(deepcopy(block_nodes))
                        block_nodes.clear()

                    elif self._is_new_block(_block):
                        if len(block_nodes) != 0:
                            blocks_list.append(deepcopy(block_nodes))
                            block_nodes.clear()
                        blocks_list.append([_block])
                    else:
                        pass
                        # raise SyntaxError("node {} can't be dealt with!".format(type(_block)))

                if len(block_nodes) != 0:
                    blocks_list.append(deepcopy(block_nodes))

                """
                print(len(blocks_list))
                for item in blocks_list:
                    print(str(len(item)))
                    for i in item:
                        print(str(type(i)))
                """

                # 对当前列表的每个item，递归调用
                out_stmt = deepcopy(pres)
                flag = True
                for item in blocks_list:
                    tmp, out_stmt = self._gen_blocks(item, out_stmt)
                    if flag:
                        in_stmt = deepcopy(tmp)
                        flag = False
                    print("new blocks for compound are {}".format(str(out_stmt)))

                if sucs is not None:
                    for suc in sucs:
                        self.blocks[suc].pre.extend(out_stmt)

                return in_stmt, out_stmt

            # 处理While
            if isinstance(node, c_ast.While):
                loop_id = self._get_loop_id()
                # 生成cond的block
                cond_in, cond_out = self._gen_blocks([node.cond], pres, sucs)
                self.blocks[cond_in[0]].name = "cond_"+str(loop_id)

                # 生成stmt的block
                # cond 即是stmt的前驱，也是stmt的后继
                stmt_in, stmt_out = self._gen_blocks([node.stmt], cond_out, cond_in)
                _name = "loop_{}".format(loop_id)
                for id in range(stmt_in[0], stmt_out[0] + 1):
                    self.blocks[id].name = _name
                # 分支选择
                self.blocks[cond_out[0]].branch[stmt_in[0]] = True
                # 补充cond的后继
                self.blocks[cond_out[0]].suc.extend(stmt_in)
                return cond_in, cond_out

            # 处理DoWhile
            if isinstance(node, c_ast.DoWhile):
                loop_id = self._get_loop_id()

                in_stmt, out_stmt = self._gen_blocks([node.stmt], pres)
                _name = "loop_{}".format(loop_id)
                for id in range(in_stmt[0], out_stmt[0] + 1):
                    self.blocks[id].name = _name

                cond_in, cond_out = self._gen_blocks([node.cond], out_stmt, in_stmt)
                self.blocks[cond_in[0]].name = "cond_" + str(loop_id)

                # 补充stmt的后继
                self.blocks[out_stmt[0]].suc = cond_in
                # cond的分支选择
                self.blocks[cond_out[0]].branch[in_stmt[0]] = True
                # 补充cond的后继
                if sucs is not None:
                    self.blocks[cond_out[0]].suc.extend(sucs)
                return in_stmt, cond_out

            # 处理If
            if isinstance(node, c_ast.If):
                cond_in, cond_out = self._gen_blocks([node.cond], pres)
                iftrue_in, iftrue_out = self._gen_blocks([node.iftrue], cond_out, sucs)
                iffalse_in, iffalse_out = self._gen_blocks([node.iffalse], cond_out, sucs)
                if_out = iftrue_out + iffalse_out

                # cond的分支选择
                self.blocks[cond_out[0]].branch[iftrue_in[0]] = True
                self.blocks[cond_out[0]].branch[iffalse_in[0]] = False
                return cond_in, if_out

            # Label
            # Label的子节点是紧接着它的一个Node！！！！！！
            if isinstance(node, c_ast.Label):
                in_label, out_label = self._gen_blocks([node.stmt], pres, sucs)
                self.labels[node.name] = in_label
                return in_label, out_label

    def _is_end(self, node: c_ast.Node):
        """
        判断当前节点是否是block的end,包括
        :param node:
        :return:它的下一个block的leaders，list   否则返回None
        """
        if isinstance(node, c_ast.Goto):
            return True
        if isinstance(node, c_ast.Return):
            return True
        return False

    def _is_new_block(self, node: c_ast.Node):
        """
        :param node: 当前遍历ast的节点：c_ast.Node
        :return: bool 是否是leader(一个block的入口语句)
        判断标准：来自王铎，不严格
            1 程序的第一个语句
            2 能有条件转移语句或无条件跳转语句到达的语句
            3 紧跟在条件转移语句后面的语句

        注意：if和while的cond单独作为block
        """
        if self.bof:
            self.bof = False
            return True
        # rule 3  if
        if isinstance(node, c_ast.If):
            return True
        # rule 3 while
        if isinstance(node, c_ast.While):
            return True
        if isinstance(node, c_ast.DoWhile):
            return True
        # rule 2 goto
        if isinstance(node, c_ast.Label):
            return True
        if isinstance(node, c_ast.Compound):
            return True
        return False

def gen_ast_parents(node: c_ast.Node, map: dict):
    if isinstance(node, (tuple, list)):
        for item in node:
            for ch_name, ch in item.children():
                # print(ch_name)
                map[ch] = node
                gen_ast_parents(ch, map)
    else:
        for ch_name, ch in node.children():
            # print(ch_name)
            map[ch] = node
            gen_ast_parents(ch, map)


if __name__ == '__main__':
    file = '../c_file/ls2.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab_store(ast)

    """    
    with open('../c_file/ls2_out.out', 'w') as f:
        f.write(str(ast))
    """


    """
    # python 的 = 对object对象是深拷贝，且连同拷贝子节点
    node = ast.ext[2]
    node.show()
    print("--------------\n\n")
    node = c_ast.IdentifierType(names=[])
    node.show()
    print("--------------\n\n")
    ast.ext[2].show()
    print("--------------\n\n")
    """

    # map记录了ast当中所有节点的父节点：字典类型
    map = {}
    gen_ast_parents(ast, map)
    for item in map.keys():
        print("{} : {}".format(type(item), type(map[item])))

    # 对FuncDef节点建立block有向图
    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('--------------start to get flow graph--------------------')
            blocks = FlowGraph(ch, sts)