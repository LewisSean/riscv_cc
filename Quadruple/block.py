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

class block(object):
    def __init__(self, id: int, Quadruples: list = [], in_live_vals: list = [], out_live_vals: list = []):
        if Quadruples is None:
            Quadruples = []
        self.id = id
        self.Quadruples = Quadruples
        self.in_live_vals = in_live_vals
        self.out_live_vals = out_live_vals


block(1)
