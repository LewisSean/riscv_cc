class Quadruple(object):
    def __init__(self, op, arg1, arg2, dest, type1, type2):

        # 四元组
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.dest = dest
        self.type1 = type1
        self.type2 = type2

        # 行号
        self.line = -1
        # 四元组类型：0 / 1 / 2 / 3 / 4
        # https://blog.csdn.net/xdz78/article/details/53454685
        self.type = 0

    def is_used(self, arg):
        return self.arg1 == arg or self.arg2 == arg