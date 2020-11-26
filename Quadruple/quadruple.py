class TmpValue():
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.is_addr = False  # 是否保存的是内存地址

class MyConstant():
    def __init__(self, value: str, type):
        self.value = value
        self.type = type

class Quadruple(object):
    def __init__(self, op, arg1, arg2, dest):

        # 四元组
        self.op = op
        self.arg1 = arg1  # [name: str, type(Symbol\TmpValue\MyConstant)]
        self.arg2 = arg2
        self.dest = dest  # ['L_xx': str, 'loc':str]

        # 行号
        self.line = -1
        # 四元组类型：0 / 1 / 2 / 3 / 4
        # https://blog.csdn.net/xdz78/article/details/53454685
        self.type = 0

    def is_used(self, arg):
        return self.arg1 == arg or self.arg2 == arg

    def __str__(self):
        line = str(self.line)+'. '+self.op + '  '
        back = '  '
        if self.arg1:
            line += self.arg1[0]
            if isinstance(self.arg1[1], TmpValue) and self.arg1[1].is_addr == True:
                back += '({} is addr) '.format(self.arg1[0])
        line += ', '
        if self.arg2:
            line += self.arg2[0]
            if isinstance(self.arg2[1], TmpValue) and self.arg2[1].is_addr == True:
                back += '({} is addr) '.format(self.arg2[0])
        line += ', '

        if self.dest:
            line += self.dest[0]
            if isinstance(self.dest[1], TmpValue) and self.dest[1].is_addr == True:
                back += '({} is addr) '.format(self.dest[0])

        return line + back

    def __repr__(self):
        return str(self)
