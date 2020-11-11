class variable(object):
    def __init__(self, name, offset, len, signed, type, value, inM, inR):
        self.offset = offset  # 相对于基地址的偏移字节数
        self.len = len  # 占用的字节数
        self.signed = signed  # 是否有符号
        self.name = name
        # long long/long long int  8
        # long/long int/int/signed/unsigned 4
        # short int/short/wchar_t(unsigned) 2
        # (unsigned)char/bool 1
        self.type = type
        self.value = value
        self.inM = inM  # 在内存中
        self.inR = inR  # 在寄存器中 具体数值对应寄存器号，-1表示不在寄存器中


# struct / function_decl / block
class symbol_table(object):
    def __init__(self, id, name):
        self.id = id  # global id and key for hash_table as well
        self.type = type  # block func struct
        self.table = set()


class func_symbols(symbol_table):
    def __init__(self, return_size, param_offset):
        self.return_size = return_size  # 函数返回值的字节数
        self.paramOffset = param_offset  # 函数传参的总字节数


class Quadruple(object):
    def __init__(self, type, op, arg1, arg2, dest):
        # 四元组类型：
        self.type = type
        # 四元组
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.dest = dest



