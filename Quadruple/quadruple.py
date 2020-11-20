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