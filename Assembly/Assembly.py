from pycparser import c_ast
from pycparser import CParser
import symtab
import re
import math

from Quadruple.block_graph import FlowGraph
from Quadruple.quadruple import MyConstant,TmpValue

class Assembly:
    def __init__(self, op=None, arg1=None, arg2=None, arg3=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

    def __repr__(self):
        ans = ' ' * 4
        ans += str(self.op) + ' ' * 4
        ans += str(self.arg1)
        if self.arg2 is not None:
            ans += ',' + str(self.arg2)
        if self.arg3 is not None:
            if str(self.arg3)[0] != '(':
                ans += ',' + str(self.arg3)
            else:
                ans += str(self.arg3)
        return ans


class Register:
    def __init__(self, name=None, symname=None, value=None):
        if value is None:
            value = []
        self.name = name
        self.symname = symname
        self.isEmpty = True


class Regs:
    def __init__(self):
        self.temporary = {}
        self.saved = {}
        self.funarg = {}
        self.retval = {}
        self.frame = {}
        for i in range(7):
            self.temporary['t' + str(i)] = Register('t' + str(i))
        for i in range(1000):
            self.funarg['a' + str(i)] = Register('a' + str(i))
        for i in range(2):
            self.retval['a' + str(i)] = Register('a' + str(i))
        for i in range(12):
            self.saved['s' + str(i)] = Register('s' + str(i))
        self.frame['s0'] = Register('s0')

    def GetEmptyF(self):
        for i in self.funarg.values():
            if self.funarg[i.name].isEmpty:
                self.funarg[i.name].isEmpty = False
                return i.name

    def ValToReg(self,varlist):
            pass


class GlobalVar:
    def __init__(self, name=None, align=0, type=None, size=0, word=None):
        self.name = name
        self.align = align
        self.type = type
        self.size = size
        self.word = word

    def __repr__(self):
        ans = ' ' * 4
        ans += '.global' + ' ' * 2 + str(self.name) + '\n'
        ans += '.align' + ' ' * 2 + str(self.align) + '\n'
        ans += '.type' + ' ' * 2 + str(self.name) + ',' + str(self.type) + '\n'
        ans += '.size' + ' ' * 2 + str(self.name) + ',' + str(self.size) + '\n'
        ans += str(self.name) + ':\n'
        for i in range(len(self.word)):
            if i != len(self.word) - 1:
                ans += '.word' + ' ' * 2 + self.word[i] + '\n'
            else:
                ans += '.word' + ' ' * 2 + self.word[i]
        return ans

class FunctionStack():
    def __init__(self, size=0):
        self.size = size
        self.stackidx = {}
        self.symList = {}

def SortStack(s: symtab.FuncSymbol):
    basicS = []
    arrayS = []
    structS = []
    for i in s.local_symbols:
        if i.type == 'array':
            arrayS.append(i)
        elif re.match('struct ', i.type) is not None:
            structS.append(i)
        else:
            basicS.append(i)
    return basicS + structS + arrayS

def GetStruct(s: symtab.SymTab):
    ss = {}
    for key, value in s.items():
        if re.match('struct ', key) is not None:
            ss[key] = value
    return ss

def GetStack(s: symtab.FuncSymbol, structlist) -> FunctionStack:
    varList = SortStack(s)
    f = FunctionStack()
    loc = -16  # 空出给帧指针和返回地址
    stackidx = {}
    lasttype = 0
    funstack = {}
    # 处理局部变量
    for var in varList:
        funstack[var.name] = var
        # 局部变量部分
        if var.type != 'array' and re.match('struct', var.type) is None:
            # 4字节 int,long int,long,signed,unsigned
            if (var.type == 'int' or var.type == 'long int'
                    or var.type == 'long' or var.type == 'signed'
                    or var.type == 'unsigned'):
                loc -= 4
                if loc % 4 != 0:
                    loc -= (4 + loc % -4)
                stackidx[var.name] = [loc]
            # 8字节 long long,long long int
            elif (var.type == 'long long'
                  or var.type == 'long long int'):
                csremain = 0
                loc -= 8
                # 低位数据存在地位上
                if loc % 8 != 0:
                    loc -= (8 + loc % -8)
                stackidx[var.name] = [loc, loc + 4]
            # 2字节 short int,short
            elif (var.type == 'short int'
                  or var.type == 'short'):
                loc -= 2
                if loc % 2 != 0:
                    loc -= (2 + loc % -2)
                stackidx[var.name] = [loc]
            # 1字节 char
            elif var.type == 'char':
                loc -= 1
                stackidx[var.name] = [loc]
            lasttype = 1
            # 结构体
        # 结构体
        elif re.match('struct ', var.type) is not None:
            if lasttype == 1:
                loc -= (8 + loc % -8)
            tmpstruct = structlist[var.type]
            temp = []
            for val in tmpstruct.member_symtab.values():
                if (val.type == 'int' or val.type == 'long int'
                        or val.type == 'long' or val.type == 'signed'
                        or val.type == 'unsigned'):
                    loc -= 4
                    if loc % 4 != 0:
                        loc -= (4 + loc % -4)
                    temp.append(loc)
                    # 8字节 long long,long long int
                elif (val.type == 'long long'
                      or val.type == 'long long int'):
                    loc -= 8
                    if loc % 8 != 0:
                        loc -= (8 + loc % -8)
                    temp.append(loc + 4)
                    temp.append(loc)
                # 2字节 short int,short
                elif (val.type == 'short int'
                      or val.type == 'short'):
                    loc -= 2
                    if loc % 2 != 0:
                        loc -= (2 + loc % -2)
                    temp.append(loc)
                # char
                elif val.type == 'char':
                    loc -= 1
                    temp.append(loc)
            stackidx[var.name] = temp
            lasttype = 2
        # 一维数组
        elif var.type == 'array':
            temp = []
            if lasttype == 1:
                loc -= (8 + loc % -8)
            if (var.element_type == 'int'
                    or var.element_type == 'long int'
                    or var.element_type == 'long'
                    or var.element_type == 'signed'
                    or var.element_type == 'unsigned'):
                loc -= var.element_size * var.dims[0]
                temp = []
                for i in range(var.dims[0]):
                    temp.append(loc + var.element_size * i)
                stackidx[var.name] = temp

            elif (var.type == 'long long'
                  or var.type == 'long long int'):
                loc -= var.element_size * var.dims[0]
                temp = []
                for i in range(var.dims[0]):
                    temp.append(loc + var.element_size * i + 4)
                    temp.append(loc + var.element_size * i)
                stackidx[var.name] = temp

            elif (var.type == 'short int'
                  or var.type == 'short'
                  or var.type == 'char'):
                temp = []
                tmpnum = var.element_size * var.dims[0] / 4 + 1
                loc -= tmpnum * 4
                for i in range(tmpnum):
                    temp.append(loc + 4 * i)
            stackidx[var.name] = temp
            lasttype = 3
    if loc % 16 != 0:
        loc -= (16 + loc % -16)

    # 处理函数参数
    for var in s.params_symtab.values():
        if var.type != 'array' and re.match('struct', var.type) is None:
            # 4字节 int,long int,long,signed,unsigned
            if (var.type == 'int' or var.type == 'long int'
                    or var.type == 'long' or var.type == 'signed'
                    or var.type == 'unsigned'):
                loc -= 4
                if loc % 4 != 0:
                    loc -= (4 + loc % -4)
                stackidx[var.name] = [loc]
            # 8字节 long long,long long int
            elif (var.type == 'long long'
                  or var.type == 'long long int'):
                csremain = 0
                loc -= 8
                # 低位数据存在地位上
                if loc % 8 != 0:
                    loc -= (8 + loc % -8)
                stackidx[var.name] = [loc, loc + 4]
            # 2字节 short int,short
            elif (var.type == 'short int'
                  or var.type == 'short'):
                loc -= 2
                if loc % 2 != 0:
                    loc -= (2 + loc % -2)
                stackidx[var.name] = [loc]
            # 1字节 char
            elif var.type == 'char':
                loc -= 1
                stackidx[var.name] = [loc]
    if loc % 16 != 0:
        loc -= (16 + loc % -16)

    f.stackidx = stackidx
    f.size = -loc
    f.symList = funstack
    return f

def FunctionAss(f: FlowGraph, s: symtab.FuncSymbol, structlist):
    r = Regs()
    fs = GetStack(s, structlist)
    varList = fs.symList
    symidx = fs.stackidx
    for i in symidx.items():
        print(i)
    assList = []
    assList.append(Assembly('addi', 'sp', 'sp', -fs.size))  # 分配栈
    assList.append(Assembly('sw', 's0', fs.size - 4, '(sp)'))  # 保存返回地址
    # assList.append(Assembly())#栈指针？
    assList.append(Assembly('addi', 's0', 'sp', fs.size))  # 栈顶地址
    TempReg={}
    TempVal={}
    L=2
    for i in range(len(f.quad_list)):
        q=f.quad_list[i]
        '''
        一元操作符
        goal：
        1.++--四元组存在问题
        '''
        if q.op == '=':
            # 赋值语句
            if (q.arg1[0]=='False' or q.arg1[0]=='True') and isinstance(q.dest[1],TmpValue):
                    TempVal[q.dest[0]]=q.arg1[0]
            if isinstance(q.arg1[1],TmpValue):#临时变量
                if (q.dest[1].type=='int' or q.dest[1].type=='long int' or
                    q.dest[1].type=='signed' or q.dest[1].type=='unsigned' or
                    q.dest[1].type=='int' ):
                    Reg0=TempReg[q.arg1[0]]
                    assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    r.funarg[Reg0].isEmpty=True
                elif (q.dest[1].type=='short' or q.dest[1].type=='short int'):
                    Reg0 = TempReg[q.arg1[0]]
                    assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    r.funarg[Reg0].isEmpty = True
                elif (q.dest[1].type=='long long' or q.dest[1].type=='long long int'):
                    Reg0 = TempReg[q.arg1[0]][0]
                    Reg1 = TempReg[q.arg1[0]][1]
                    assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    assList.append(Assembly('sw', Reg1, symidx[q.dest[0]][1], '(s0)'))
                    r.funarg[Reg0].isEmpty = True
                    r.funarg[Reg1].isEmpty = True
                else:
                    Reg0 = TempReg[q.arg1[0]]
                    assList.append(Assembly('sb', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    r.funarg[Reg0].isEmpty = True
            else:#立即数和变量
                Reg0 = r.GetEmptyF()
                r.funarg[Reg0].symname = q.dest[0]
                if isinstance(q.arg1[1],MyConstant):
                    assList.append(Assembly('li', Reg0, int(q.arg1[0]) % (2 ** 31)))
                    err = symidx.get(q.dest[0], -1)
                    if err == -1:
                        print("未声明变量" + str(q.dest[0]))
                    if (q.dest[1].type=='int' or q.dest[1].type=='long int' or
                    q.dest[1].type=='signed' or q.dest[1].type=='unsigned' or
                    q.dest[1].type=='int' ):
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type=='short' or q.dest[1].type=='short int'):
                        assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type=='long long' or q.dest[1].type=='long long int'):
                        Reg1 = r.GetEmptyF()
                        r.funarg[Reg1].symname = q.dest[0]
                        print(int(q.arg1[0]) / (2 ** 31))
                        assList.append(Assembly('li', Reg1, math.floor(int(q.arg1[0]) / (2 ** 31))))
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        assList.append(Assembly('sw', Reg1, symidx[q.dest[0]][1], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    else:
                        assList.append(Assembly('sb', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                else:
                    assList.append(Assembly('li', Reg0, symidx[q.arg1[0]][0]))
                    err = symidx.get(q.dest[0], -1)
                    if err == -1:
                        print("未声明变量" + str(q.dest[0]))
                    if (q.dest[1].type=='int' or q.dest[1].type=='long int' or
                    q.dest[1].type=='signed' or q.dest[1].type=='unsigned' or
                    q.dest[1].type=='int' ):
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type=='short' or q.dest[1].type=='short int'):
                        assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type=='long long' or q.dest[1].type=='long long int'):
                        Reg1 = r.GetEmptyF()
                        r.funarg[Reg1].symname = q.arg1[0]
                        assList.append(Assembly('li', Reg0, symidx[q.arg1[0]][1]))
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        assList.append(Assembly('sw', Reg1, symidx[q.dest[0]][1], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    else:
                        assList.append(Assembly('sb', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
            '''
            ++--四元组存在问题。暂时不用
            '''
        if q.op=='++' or q.op=='--':
            if (q.dest[1].type=='long long' or q.dest[1].type=='long long int'):
                Reg0 = r.GetEmptyF()
                Reg1 = r.GetEmptyF()
                Reg2 = r.GetEmptyF()
                Reg3 = r.GetEmptyF()
                Reg4 = r.GetEmptyF()
                Reg5 = r.GetEmptyF()
                Reg6 = r.GetEmptyF()
                r.funarg[Reg1].symname = q.arg1[0]
                r.funarg[Reg2].symname = q.arg1[0]
                r.funarg[Reg3].symname = q.arg2[0]
                r.funarg[Reg4].symname = q.arg2[0]
                assList.append(Assembly('lw', Reg3, symidx[q.dest[0]][0], '(s0)'))
                assList.append(Assembly('lw', Reg4, symidx[q.dest[0]][1], '(s0)'))
                if q.op=='++':
                    assList.append(Assembly('li', Reg1, 1))
                    assList.append(Assembly('li', Reg2, 0))
                else:
                    assList.append(Assembly('li', Reg1, -1))
                    assList.append(Assembly('li', Reg2, -1))
                assList.append(Assembly('add', Reg5, Reg3,Reg1))
                assList.append(Assembly('mv', Reg0, Reg5))
                assList.append(Assembly('sltu', Reg0, Reg0,Reg3))
                assList.append(Assembly('add', Reg6, Reg4,Reg2))
                assList.append(Assembly('add', Reg4, Reg0,Reg6))
                assList.append(Assembly('mv', Reg6, Reg4))
            else:
                Reg0 = r.GetEmptyF()
                r.funarg[Reg0].symname = q.arg1[0]
                if (q.dest[1].type=='int' or q.dest[1].type=='long int' or
                    q.dest[1].type=='signed' or q.dest[1].type=='unsigned' or
                    q.dest[1].type=='int' ):
                    assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0],'s0'))
                elif (q.dest[1].type=='short' or q.dest[1].type=='short int'):
                    assList.append(Assembly('lhu', Reg0, symidx[q.arg1[0]][0],'s0'))
                else:
                    assList.append(Assembly('lbu', Reg0, symidx[q.arg1[0]][0],'s0'))

                if q.op=='++':
                    assList.append(Assembly('addi', Reg0, Reg0,1))
                    if varList[q.arg1[0]].size == 2:
                        assList.append(Assembly('slli', Reg0, Reg0, 16))
                        assList.append(Assembly('srli', Reg0, Reg0, 16))
                else:
                    assList.append(Assembly('addi', Reg0, Reg0, -1))
                    if varList[q.arg1[0]].size == 2:
                        assList.append(Assembly('slli', Reg0, Reg0, 16))
                        assList.append(Assembly('srli', Reg0, Reg0, 16))
        '''
         二元操作符
         goal：
         1.<>存疑
         '''
        if (q.op == '+' or q.op=='-' or q.op=='^'or
            q.op=='|'or q.op=='&'or q.op=='<'or
                q.op=='>'or q.op=='+='or q.op=='-='):
            if q.op=='+=':
                q.arg2=q.arg1
                q.arg1=q.dest
                q.op='+'
            if q.op == '-=':
                q.arg2 = q.arg1
                q.arg1 = q.dest
                q.op = '-'
            # 交换位置，保证第二个位置为常量
            if isinstance(q.arg1[1], MyConstant):
                temp = q.arg1
                q.arg1 = q.arg2
                q.arg2 = temp

            #long long后31位放在低位
            if (q.arg1[1].type=='long long' or q.arg1[1].type=='long long int'):
                Reg0 = r.GetEmptyF()
                if isinstance(q.arg1[1],TmpValue):
                    Reg1=TempReg[q.arg1[0]][0]
                    Reg2=TempReg[q.arg1[0]][1]
                else:
                    Reg1 = r.GetEmptyF()
                    Reg2 = r.GetEmptyF()

                if isinstance(q.arg2[1],TmpValue):
                    Reg3=TempReg[q.arg2[0]][0]
                    Reg4=TempReg[q.arg2[0]][1]
                else:
                    Reg3 = r.GetEmptyF()
                    Reg4 = r.GetEmptyF()
                Reg5 = r.GetEmptyF()
                Reg6 = r.GetEmptyF()
                if not isinstance(q.arg1[1], MyConstant):
                    r.funarg[Reg1].symname = q.arg1[0]
                    r.funarg[Reg2].symname = q.arg1[0]
                if not isinstance(q.arg2[1], MyConstant):
                    r.funarg[Reg3].symname = q.arg2[0]
                    r.funarg[Reg4].symname = q.arg2[0]

                TempReg[q.dest[0]]=[Reg5,Reg6]
                if not (isinstance(q.arg1[1], TmpValue) or isinstance(q.arg1[1], MyConstant)):
                    assList.append(Assembly('lw', Reg1, symidx[q.arg1[0]][0], '(s0)'))
                    assList.append(Assembly('lw', Reg2, symidx[q.arg1[0]][1], '(s0)'))
                if not (isinstance(q.arg1[1], TmpValue) or isinstance(q.arg1[1], MyConstant)):
                    assList.append(Assembly('lw', Reg3, symidx[q.arg2[0]][0], '(s0)'))
                    assList.append(Assembly('lw', Reg4, symidx[q.arg2[0]][1], '(s0)'))

                if isinstance(q.arg1[1], MyConstant):
                    assList.append(Assembly('li', Reg1, int(q.arg2[0]) % (2 ** 31)))
                    assList.append(Assembly('li', Reg2, math.floor(int(q.arg2[0]) / (2 ** 31))))

                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('li', Reg3, int(q.arg2[0]) % (2 ** 31)))
                    assList.append(Assembly('li', Reg4, math.floor(int(q.arg2[0]) / (2 ** 31))))

                if q.op=='+':
                    assList.append(Assembly('add', Reg5, Reg3, Reg1))
                    assList.append(Assembly('mv', Reg0, Reg5))
                    assList.append(Assembly('sltu', Reg0, Reg0,Reg3))
                    assList.append(Assembly('add', Reg6, Reg4, Reg2))#加进位
                    assList.append(Assembly('add', Reg4, Reg0, Reg6))
                    assList.append(Assembly('mv', Reg6, Reg4))

                elif q.op=='-':
                    assList.append(Assembly('sub', Reg5, Reg3, Reg1))
                    assList.append(Assembly('mv', Reg0, Reg5))
                    assList.append(Assembly('sgtu', Reg0, Reg0, Reg3))
                    assList.append(Assembly('sub', Reg6, Reg4, Reg2))  # 退位?
                    assList.append(Assembly('sub', Reg4, Reg6, Reg0))
                    assList.append(Assembly('mv', Reg6, Reg4))
                elif q.op=='^':
                    assList.append(Assembly('xor', Reg5, Reg3, Reg1))
                    assList.append(Assembly('xor', Reg6, Reg4, Reg2))
                elif q.op == '|':
                    assList.append(Assembly('or', Reg5, Reg3, Reg1))
                    assList.append(Assembly('or', Reg6, Reg4, Reg2))
                else:
                    assList.append(Assembly('and', Reg5, Reg3, Reg1))
                    assList.append(Assembly('and', Reg6, Reg4, Reg2))
                r.funarg[Reg0].isEmpty= True
                r.funarg[Reg1].isEmpty = True
                r.funarg[Reg2].isEmpty = True
                r.funarg[Reg3].isEmpty = True
                r.funarg[Reg4].isEmpty = True
            else:
                if isinstance(q.arg1[1],TmpValue):
                    Reg0=TempReg[q.arg1[0]]
                elif isinstance(q.arg1[1], MyConstant):
                    Reg0 = q.arg1[0]
                else:
                    Reg0 = r.GetEmptyF()
                if not isinstance(q.arg1[1], MyConstant):
                    r.funarg[Reg0].symname = q.arg1[0]

                if isinstance(q.arg2[1],TmpValue):
                    Reg1=TempReg[q.arg2[0]]
                elif isinstance(q.arg2[1],MyConstant):
                    Reg1=q.arg2[0]
                else:
                    Reg1 = r.GetEmptyF()
                if not isinstance(q.arg2[1],MyConstant):
                    r.funarg[Reg1].symname = q.arg2[0]
                Reg2=r.GetEmptyF()
                TempReg[q.dest[0]]= Reg2

                if (q.arg1[1].type=='int' or q.arg1[1].type=='long int' or
                    q.arg1[1].type=='signed' or q.arg1[1].type=='unsigned' or
                    q.arg1[1].type=='int' ):
                    if not(isinstance(q.arg1[1],TmpValue) or isinstance(q.arg1[1],MyConstant)):
                        assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0],'(s0)'))
                    if not(isinstance(q.arg2[1],TmpValue) or isinstance(q.arg2[1],MyConstant)):
                        assList.append(Assembly('lw', Reg1, symidx[q.arg2[0]][0],'(s0)'))
                elif (q.arg1[1].type=='short' or q.arg1[1].type=='short int'):
                    if not(isinstance(q.arg1[1],TmpValue) or isinstance(q.arg1[1],MyConstant)):
                        assList.append(Assembly('lhu', Reg0, symidx[q.arg1[0]][0],'(s0)'))
                    if not(isinstance(q.arg2[1],TmpValue) or isinstance(q.arg2[1],MyConstant)):
                        assList.append(Assembly('lhu', Reg1, symidx[q.arg2[0]][0],'(s0)'))
                else:
                    if not(isinstance(q.arg1[1],TmpValue) or isinstance(q.arg1[1],MyConstant)):
                        assList.append(Assembly('lbu', Reg0, symidx[q.arg1[0]][0],'(s0)'))
                    if not(isinstance(q.arg2[1],TmpValue) or isinstance(q.arg2[1],MyConstant)):
                        assList.append(Assembly('lbu', Reg1, symidx[q.arg2[0]][0],'(s0)'))

                if q.op=='+':
                    if isinstance(q.arg2[1],MyConstant):
                        assList.append(Assembly('addi', Reg2, Reg0, Reg1))
                    else:
                        assList.append(Assembly('add', Reg2, Reg0, Reg1))
                    if (q.arg1[1].type=='short' or q.arg1[1].type=='short int'):
                        assList.append(Assembly('slli', Reg2, Reg2, 16))
                        assList.append(Assembly('srli', Reg2, Reg2, 16))
                    #TempReg[q.dest[0]]=Reg2
                elif q.op=='-':
                    if isinstance(q.arg2[1],MyConstant):
                        assList.append(Assembly('addi', Reg2, Reg0, '-'+Reg1))
                    else:
                        assList.append(Assembly('sub', Reg2, Reg0, Reg1))
                    if (q.arg1[1].type=='short' or q.arg1[1].type=='short int'):
                        assList.append(Assembly('slli', Reg2, Reg2, 16))
                        assList.append(Assembly('srli', Reg2, Reg2, 16))
                    #TempReg[q.dest[0]] = Reg2
                elif q.op=='^':
                    if isinstance(q.arg2[1],MyConstant):
                        assList.append(Assembly('xori', Reg2, Reg0, Reg1))
                    else:
                        assList.append(Assembly('xor', Reg2, Reg0, Reg1))
                elif q.op=='|':
                    if isinstance(q.arg2[1], MyConstant):
                        assList.append(Assembly('ori', Reg2, Reg0, Reg1))
                    else:
                        assList.append(Assembly('or', Reg2, Reg0, Reg1))
                elif q.op == '&':
                    if isinstance(q.arg2[1], MyConstant):
                        assList.append(Assembly('andi', Reg2, Reg0, Reg1))
                    else:
                        assList.append(Assembly('and', Reg2, Reg0, Reg1))
                elif q.op=='<':
                    if isinstance(q.arg2[1], MyConstant):
                        assList.append(Assembly('slti', Reg2, Reg0, Reg1))
                    else:
                        assList.append(Assembly('slt', Reg2, Reg0, Reg1))
                    assList.append(Assembly('andi', Reg2, Reg2, '0xff'))
                elif q.op == '>':
                    assList.append(Assembly('sgt', Reg2, Reg0, Reg1))
                    assList.append(Assembly('andi', Reg2, Reg2, '0xff'))

                if not (isinstance(q.arg1[1], MyConstant)):
                    r.funarg[Reg0].isEmpty = True
                if not (isinstance(q.arg2[1], MyConstant)):
                    r.funarg[Reg1].isEmpty = True
        '''
         跳转
        '''
        if (q.op=='j<' or q.op=='j>' or q.op=='j=' or
            q.op=='j<='or q.op=='j>='or q.op=='j!='or
            q.op=='j=='):
            Reg0 = r.GetEmptyF()
            if not (isinstance(q.arg1[1],MyConstant) or isinstance(q.arg1[1],TmpValue)):
                if q.arg1[q.type]=='int':
                    r.funarg[Reg0].symname=q.arg1[0]
                    assList.append(Assembly('lw', Reg0,symidx[q.arg1[0]][0],'(s0)'))
            elif isinstance(q.arg1[1],TmpValue):
                Reg0='TmpValue'
            else:
                assList.append(Assembly('li', Reg0, q.arg1[0]))
            Reg1 = r.GetEmptyF()
            assList.append(Assembly('li', Reg1, q.arg2[0]))

            if q.op=='j<':
                assList[-1].arg2=int(q.arg2[0])-1
                #真出口
                assList.append(Assembly('bgt', Reg0, Reg1, '.L'+str(L)))
                L+=1

                assList.append(Assembly())
                #真出口
                assList.append(Assembly())
                pass

            if q.op=='j=':
                pass


        '''
        内存操作

         '''


    assList.append(Assembly('lw', 's0', fs.size - 4, '(sp)'))  # 保存返回地址
    assList.append(Assembly('addi', 'sp', 'sp', fs.size))  # 恢复sp
    assList.append(Assembly('jr', 'ra'))  # 跳转到ra地址
    return assList


if __name__ == '__main__':
    file = '../c_file/wyb1.c'
    parser = CParser()
    with open(file, 'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab.symtab_store(ast)
    sts.show(ast)
    t = sts.get_symtab_of(ast)
    tt = t['main']
    structlist = GetStruct(t)
    fs = GetStack(tt, structlist)

    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('--------------start to get flow graph--------------------')
            flowGraph = FlowGraph(ch, sts)
    temp = FunctionAss(flowGraph, tt, structlist)
    for i in temp:
        print(i)
    print(1)
    print(2 ** 32)
