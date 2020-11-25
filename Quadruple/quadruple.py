class Quadruple(object):
    def __init__(self, op, arg1, arg2, dest):

        # 四元组
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.dest = dest

        # 行号
        self.line = -1
        # 四元组类型：0 / 1 / 2 / 3 / 4
        # https://blog.csdn.net/xdz78/article/details/53454685
        self.type = 0

    def is_used(self, arg):
        return self.arg1 == arg or self.arg2 == arg

    def __str__(self):
        line = str(self.line)+'. '
        if self.dest is None:
            return line+'{}, , , '.format(self.op)
        if self.arg1 is None:
            return line+"{}, , , {}".format(self.op, self.dest[0])
        if self.arg2 is None:
            return line+"{}, {}, , {}".format(self.op, self.arg1[0], self.dest[0])
        else:
            return line+"{}, {}, {}, {}".format(self.op, self.arg1[0], self.arg2[0], self.dest[0])

    def __repr__(self):
        return str(self)
