import sys
sys.path.append('..')
from pycparser import c_ast
from pycparser import CParser
from copy import deepcopy
from symtab import symtab_store, SymTab, SymTabStore
from Quadruple.block import Block, RegPool
import queue

class FlowGraph(object):
    """
    获取的是一个函数的流图
    所以入口节点应该是FuncDef
    """
    def __init__(self, node: c_ast.FuncDef, symtab: SymTabStore):

        if not isinstance(node, c_ast.FuncDef):
            raise NotImplementedError('当前类型节点非FuncDef节点!')

        self.reg_pool = RegPool()
        # bof 函数体的开始，用于判断是否是一个新的block开始，_is_new_block()用到
        self.bof = True
        # 增设entry和exit两个block(不包含实际四元组)，id分别为0和-1
        self.blocks = dict()
        self.if_counts = dict()
        self.blocks[0] = Block(0, [])
        self.blocks[-1] = Block(-1, [])
        # block的id生成种子，自增生成id
        self.id_seed = 0
        # 一个循环体内的同级block共享相同的循环体id
        # （注：循环嵌套，则内循环block共享一个id1，外循环中非内循环的其他block共享另一个id2，为了break的正确跳出）
        self.loop_seed = 0
        # 其余四元组的id范围: >= 1
        compound: c_ast.Compound = node.body
        self.symtab = symtab
        # 字典，保存goto的label的映射，如labels['L1'] = 10 表示 goto L1是跳转到block 10
        self.labels = {}
        # 生成block有向图的核心函数
        self._gen_blocks([compound], [0], [-1])
        self._complete_graph()
        self.quad_list = []
        offset = self.gen_quad_list(finished=set())
        self.gen_quad_list(finished=set(), cur_block=-1, offset=offset)
        self._complete_quad_list()
        self.show()

    def _complete_quad_list(self):
        # 查找有分支的block，对分支block进行确定
        # 默认最后两行为分支跳转
        for k in self.blocks.keys():
            if len(self.blocks[k].branch) != 0:
                index = len(self.blocks[k].Quadruples) - 1
                dest_id = int(self.blocks[k].Quadruples[index].dest[0][2:self.blocks[k].Quadruples[index].dest[0].rfind('_')])
                self.blocks[k].Quadruples[index].dest[0] = 'L_{}'.format(self.blocks[dest_id].begin)
                index = len(self.blocks[k].Quadruples) - 2
                dest_id = int(self.blocks[k].Quadruples[index].dest[0][2:self.blocks[k].Quadruples[index].dest[0].rfind('_')])
                self.blocks[k].Quadruples[index].dest[0] = 'L_{}'.format(self.blocks[dest_id].begin)
            elif k != -1:
                index = len(self.blocks[k].Quadruples) - 1
                dest_id = int(self.blocks[k].Quadruples[index].dest[0][2:self.blocks[k].Quadruples[index].dest[0].rfind('_')])
                self.blocks[k].Quadruples[index].dest[0] = 'L_{}'.format(self.blocks[dest_id].begin)

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
                            self.blocks[i].loop_cond = pre

        # 回填branch
        for k in self.blocks.keys():
            if len(self.blocks[k].branch) != 0:
                for b in self.blocks[k].suc:
                    if b not in self.blocks[k].branch.keys():
                        self.blocks[k].branch[False] = b

        # 回填四元组的跳转位置
        for k in self.blocks.keys():
            self.blocks[k].complete_quadruples()

    # dfs
    def gen_quad_list(self, finished: set, cur_block=0, offset=0, end_block=-1):
        # 返回 self.blocks[cur_block].end
        print("--> {}".format(cur_block))
        if cur_block in finished:
            return offset
        for quad in self.blocks[cur_block].Quadruples:
            quad.line += offset

        self.blocks[cur_block].begin = offset
        self.blocks[cur_block].end = offset = offset + len(self.blocks[cur_block].Quadruples)

        self.blocks[cur_block].adjust()
        self.quad_list.extend(self.blocks[cur_block].Quadruples)
        # offset是每个后继block的起始行
        finished.add(cur_block)

        # 处理if分支
        if self.blocks[cur_block].is_if:
            # 找到if出口
            exit_id = self.find_if_exit(cur_block)
            print("if exit: {}".format(exit_id))
            end_block = exit_id
            if end_block not in self.if_counts.keys():
                self.if_counts[end_block] = 2
            else:
                self.if_counts[end_block] += 1

        flag = False
        for _suc in self.blocks[cur_block].suc:
            if _suc == end_block:
                flag = True
                continue
            offset = self.gen_quad_list(finished, _suc, offset, end_block)
        if flag and end_block != -1:
            if self.if_counts[end_block] == 1:
                offset = self.gen_quad_list(finished, end_block, offset, -1)
            self.if_counts[end_block] -= 1

        return offset

    def find_if_exit(self, id):
        ifTrue = self.blocks[id].branch[True] # ifTrue
        path = set()
        que = queue.Queue()
        que.put(ifTrue)
        while not que.empty():
            cur = que.get()
            if cur in path:
                continue
            else:
                path.add(cur)
            for _suc in self.blocks[cur].suc:
                que.put(_suc)

        ifFalse = self.blocks[id].branch[False]  # ifFalse
        path2 = set()
        que2 = queue.Queue()
        que2.put(ifFalse)
        while not que2.empty():
            cur = que2.get()
            if cur in path2:
                continue
            else:
                path2.add(cur)
            for _suc in self.blocks[cur].suc:
                if _suc in path:
                  return _suc
                que2.put(_suc)

        return -2

    # bfs
    # 需要解决的问题，如何优先处理if else 里面的if的block
    def gen_quad_list_bfs(self, offset=0, end=-1):

        to_show = []

        cur_block = 0
        finished = set()
        # 返回 self.blocks[cur_block].end
        que = queue.Queue()
        que.put(cur_block)
        while not que.empty():
            cur_block = que.get()

            to_show.append(cur_block)

            if cur_block in finished:
                continue

            # 对if情况特殊处理
            if self.blocks[cur_block].is_if == True:
                # 找到if出口
                exit_id = self.find_if_exit(cur_block)
                print("if exit: {}".format(exit_id))


            for quad in self.blocks[cur_block].Quadruples:
                quad.line += offset

            self.blocks[cur_block].begin = offset
            self.blocks[cur_block].end = offset = offset + len(self.blocks[cur_block].Quadruples)

            self.blocks[cur_block].adjust()
            self.quad_list.extend(self.blocks[cur_block].Quadruples)
            # offset是每个后继block的起始行
            finished.add(cur_block)

            for _suc in self.blocks[cur_block].suc:
                if _suc == end:
                    continue
                que.put(_suc)

        print("//////////////////////////////////////")
        for i in to_show:
            print(i)

        return offset

    def show(self):
        print("\n\nblocks are as follows: \n")
        for k in self.blocks.keys():
            print("id {},  pre: {}, suc: {}".format(self.blocks[k].id, self.blocks[k].pre, self.blocks[k].suc))
            if self.blocks[k].name != "":
                print("name: {}, {}".format(self.blocks[k].name, self.blocks[k].loop_end))
            if self.blocks[k].branch != dict():
                print("branch>>>>")
                for key in self.blocks[k].branch:
                    print("if {}: goto block {}".format(key, self.blocks[k].branch[key]))
            # print("nodes>>>>")
            # for node in self.blocks[k].ast_nodes:
            #     print(str(type(node)))
            self.blocks[k].show_quadruples()
            print('..................................')

        print("\n\ntotal quads >>>>>>>>>>>>>>>>>>>>>>>>>>")
        for quad in self.quad_list:
            print(quad)

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

    def _gen_blocks(self, nodes: list, pres: list, sucs: list = None, loop_id=-1, is_if=False):
        """
        递归函数，产生当前节点(们)的所有block
        :param nodes: 当前节点列表
        :param pres: 前驱节点id的列表
        :param sucs: 后继节点id的列表
        :param loop_id: 传递进入循环的loop_id
        :return:   返回产生的所有block中的入口blocks和出口blocks的id
        """
        # 如果当前节点数大于1，则说明这些节点是可以组成一个block的
        if len(nodes) > 1:
            new_id = self._get_id()
            self.blocks[new_id] = Block(new_id, nodes, pres, sucs, self.symtab, self.reg_pool)
            if loop_id != -1:
                self.blocks[new_id].name = "loop_{}".format(loop_id)
            if is_if:
                self.blocks[new_id].is_if = True

            return [new_id], [new_id]

        # 单个节点，且自组成一个block
        elif not self._is_new_block(nodes[0]):
            new_id = self._get_id()
            self.blocks[new_id] = Block(new_id, nodes, pres, sucs, self.symtab, self.reg_pool)
            if loop_id != -1:
                self.blocks[new_id].name = "loop_{}".format(loop_id)
            if is_if:
                self.blocks[new_id].is_if = True

            return [new_id], [new_id]
        # 处理单个节点，往往需要对子节点递归调用，反例：只有一个四元组的block
        else:
            node = nodes[0]

            # 处理compound节点
            # 注意compound嵌套
            if isinstance(nodes[0], c_ast.Compound):
                # 列表为空
                if len(nodes[0].block_items) == 0:
                    new_id = self._get_id()
                    self.blocks[new_id] = Block(new_id, [], pres, sucs, self.symtab, self.reg_pool)
                    if is_if:
                        self.blocks[new_id].is_if = True

                    return [new_id], [new_id]

                # blocks：存储compound内部所有相同block的节点的列表
                # blocks_list = []
                block_nodes = []
                out_stmt = deepcopy(pres)
                flag = True
                for _block in nodes[0].block_items:
                    # print('------------------------')
                    # _block.show()

                    if not (self._is_end(_block) or self._is_new_block(_block)):
                        block_nodes.append(_block)

                    elif self._is_end(_block):
                        block_nodes.append(_block)
                        tmp, out_stmt = self._gen_blocks(block_nodes, out_stmt, loop_id=loop_id)
                        if flag:
                            in_stmt = deepcopy(tmp)
                            flag = False
                        # blocks_list.append(deepcopy(block_nodes))
                        block_nodes.clear()

                    elif self._is_new_block(_block):
                        if len(block_nodes) != 0:
                            tmp, out_stmt = self._gen_blocks(block_nodes, out_stmt, loop_id=loop_id)
                            if flag:
                                in_stmt = deepcopy(tmp)
                                flag = False
                            block_nodes.clear()
                        tmp, out_stmt = self._gen_blocks([_block], out_stmt, loop_id=loop_id)
                        if flag:
                            in_stmt = deepcopy(tmp)
                            flag = False

                    else:
                        pass
                        # raise SyntaxError("node {} can't be dealt with!".format(type(_block)))

                if len(block_nodes) != 0:
                    tmp, out_stmt = self._gen_blocks(block_nodes, out_stmt, loop_id=loop_id)
                    if flag:
                        in_stmt = deepcopy(tmp)
                        flag = False

                # 对当前列表的每个item，递归调用

                if sucs is not None:
                    for suc in sucs:
                        self.blocks[suc].pre.extend(out_stmt)

                return in_stmt, out_stmt

            # 处理While
            if isinstance(nodes[0], c_ast.While):
                loop_id = self._get_loop_id()
                # 生成cond的block
                cond_in, cond_out = self._gen_blocks([nodes[0].cond], pres, sucs, loop_id)
                self.blocks[cond_in[0]].name = "cond_"+str(loop_id)

                # 生成stmt的block
                # cond 即是stmt的前驱，也是stmt的后继
                stmt_in, stmt_out = self._gen_blocks([nodes[0].stmt], cond_out, cond_in, loop_id)
                """
                _name = "loop_{}".format(loop_id)
                for id in range(stmt_in[0], stmt_out[0] + 1):
                    self.blocks[id].name = _name
                """
                # 分支选择
                self.blocks[cond_out[0]].branch[True] = stmt_in[0]
                # 补充cond的后继
                self.blocks[cond_out[0]].suc.extend(stmt_in)
                return cond_in, cond_out

            # 处理DoWhile
            if isinstance(nodes[0], c_ast.DoWhile):
                loop_id = self._get_loop_id()

                in_stmt, out_stmt = self._gen_blocks([nodes[0].stmt], pres, loop_id=loop_id)
                """
                _name = "loop_{}".format(loop_id)
                for id in range(in_stmt[0], out_stmt[0] + 1):
                    self.blocks[id].name = _name
                """

                cond_in, cond_out = self._gen_blocks([nodes[0].cond], out_stmt, in_stmt, loop_id)
                self.blocks[cond_in[0]].name = "cond_" + str(loop_id)

                # 补充stmt的后继
                self.blocks[out_stmt[0]].suc = cond_in
                # cond的分支选择
                self.blocks[cond_out[0]].branch[True] = in_stmt[0]
                # 补充cond的后继
                if sucs is not None:
                    self.blocks[cond_out[0]].suc.extend(sucs)
                return in_stmt, cond_out

            # 处理If
            if isinstance(nodes[0], c_ast.If):
                cond_in, cond_out = self._gen_blocks([nodes[0].cond], pres, loop_id=loop_id, is_if=True)
                iftrue_in, iftrue_out = self._gen_blocks([nodes[0].iftrue], cond_out, sucs, loop_id=loop_id)
                iffalse_in, iffalse_out = self._gen_blocks([nodes[0].iffalse], cond_out, sucs, loop_id=loop_id)
                if_out = iftrue_out + iffalse_out

                # cond的分支选择
                self.blocks[cond_out[0]].branch[True] = iftrue_in[0]
                self.blocks[cond_out[0]].branch[False] = iffalse_in[0]
                return cond_in, if_out

            # 处理Label
            # Label的子节点是紧接着它的一个Node！！！！！！
            if isinstance(nodes[0], c_ast.Label):
                in_label, out_label = self._gen_blocks([nodes[0].stmt], pres, sucs, loop_id=loop_id)
                self.labels[nodes[0].name] = in_label
                return in_label, out_label

            # Switch 未完待续
            if isinstance(node, c_ast.Switch):
                
                pass

    def _is_end(self, node: c_ast.Node):
        """
        判断当前节点是否是block的end,包括
        :param node:
        :return:它的下一个block的leaders，list   否则返回None
        """
        if isinstance(node, (c_ast.Goto, c_ast.Return, c_ast.Continue, c_ast.Break)):
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
    test_file = 'demo_code.c'
    file = '../c_file/'+test_file
    parser = CParser()
    with open(file, 'r') as f:
        ast = parser.parse(f.read(), file)
        # ast.show()
        with open('../c_file/{}_out.out'.format(test_file[:-2]), 'w') as f:
           f.write(str(ast))

    sts = symtab_store(ast)
    sts.show(ast)

    # map记录了ast当中所有节点的父节点：字典类型
    pc_map = {}
    gen_ast_parents(ast, pc_map)

    # 对FuncDef节点建立block有向图
    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('--------------start to get flow graph--------------------')
            flowGraph = FlowGraph(ch, sts)

