from pycparser import c_ast
from pycparser import CParser
import symtab
import re
import math

from Quadruple.block_graph import FlowGraph
from Quadruple.quadruple import MyConstant, TmpValue


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
        for i in range(77):
            self.temporary['t' + str(i)] = Register('t' + str(i))
        for i in range(2, 8):
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

    def ValToReg(self, varlist):
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
        self.structidx = {}


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
    return basicS + arrayS + structS

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
    structidx = {}
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
                lasttype = 2
                if (val.type == 'int' or val.type == 'long int'
                        or val.type == 'long' or val.type == 'signed'
                        or val.type == 'unsigned'):
                    loc -= 4
                    if loc % 4 != 0:
                        loc -= (4 + loc % -4)
                    # temp.append(loc)
                    # 8字节 long long,long long int
                elif (val.type == 'long long'
                      or val.type == 'long long int'):
                    loc -= 8
                    if loc % 8 != 0:
                        loc -= (8 + loc % -8)
                    # temp.append(loc + 4)
                    # temp.append(loc)
                # 2字节 short int,short
                elif (val.type == 'short int'
                      or val.type == 'short'):
                    loc -= 2
                    if loc % 2 != 0:
                        loc -= (2 + loc % -2)
                    # temp.append(loc)
                # char
                elif val.type == 'char':
                    loc -= 1
                    # temp.append(loc)
                    lasttype = 1
            tmploc = loc
            structi = {}
            offset = 0
            for val in tmpstruct.member_symtab.values():
                lasttype = 2
                if (val.type == 'int' or val.type == 'long int'
                        or val.type == 'long' or val.type == 'signed'
                        or val.type == 'unsigned'):

                    if tmploc % 4 != 0:
                        tmploc -= (tmploc % -4)
                    structi[str(offset)] = [tmploc]
                    offset += 4
                    temp.append(tmploc)
                    tmploc += 4
                    # 8字节 long long,long long int
                elif (val.type == 'long long'
                      or val.type == 'long long int'):
                    if tmploc % 8 != 0:
                        tmploc -= (tmploc % -8)
                    structi[str(offset)] = [tmploc, tmploc + 4]
                    offset += 8
                    temp.append(tmploc)
                    temp.append(tmploc + 4)
                    tmploc += 8
                # 2字节 short int,short
                elif (val.type == 'short int'
                      or val.type == 'short'):
                    if tmploc % 2 != 0:
                        tmploc -= (tmploc % -2)
                    structi[str(offset)] = [tmploc]
                    offset += 2
                    temp.append(tmploc)
                    tmploc += 2
                # char
                elif val.type == 'char':
                    structi[str(offset)] = [tmploc]
                    offset += 1
                    temp.append(tmploc)
                    tmploc += 1
                    lasttype = 1
            structidx[var.name] = structi
            stackidx[var.name] = temp
        # 数组
        elif var.type == 'array':
            temp = []
            if lasttype == 1:
                loc -= (8 + loc % -8)
            if (var.element_type == 'int'
                    or var.element_type == 'long int'
                    or var.element_type == 'long'
                    or var.element_type == 'signed'
                    or var.element_type == 'unsigned'):
                sumsize = 1
                for i in range(len(var.dims)):
                    sumsize *= var.dims[i]
                loc -= var.element_size * sumsize
                temp = []

                for i in range(sumsize):
                    temp.append(loc + var.element_size * i)
                stackidx[var.name] = temp

            elif (var.element_type == 'long long'
                  or var.element_type == 'long long int'):
                sumsize = 1
                for i in range(len(var.dims)):
                    sumsize *= var.dims[i]
                loc -= var.element_size * sumsize
                temp = []

                for i in range(sumsize):
                    temp.append(loc + var.element_size * i)
                    temp.append(loc + var.element_size * i + 4)
                stackidx[var.name] = temp

            elif (var.element_type == 'short int'
                  or var.element_type == 'short'
                  or var.element_type == 'char'):
                temp = []
                sumsize = 1
                for i in range(len(var.dims)):
                    sumsize *= var.dims[i]

                if var.element_size * sumsize % 4 != 0:

                    tmpnum = var.element_size * sumsize // 4 + 1
                else:
                    tmpnum = var.element_size * sumsize // 4
                loc -= tmpnum * 4
                for i in range(sumsize):
                    temp.append(loc + var.element_size * i)
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
    f.structidx = structidx
    return f


def FunctionAss(f: FlowGraph, s: symtab.FuncSymbol, structlist):
    r = Regs()
    fs = GetStack(s, structlist)

    varList = fs.symList
    symidx = fs.stackidx

    LC = 0
    roList = []
    sroList = []
    avis = {}  # 初始化后的数组

    svis = {}  # 初始化后的结构体
    assList = []
    conditionList = {}
    assList.append(Assembly('addi', 'sp', 'sp', -fs.size))  # 分配栈
    assList.append(Assembly('sw', 's0', fs.size - 4, '(sp)'))  # 保存返回地址
    # assList.append(Assembly())#栈指针？
    assList.append(Assembly('addi', 's0', 'sp', fs.size))  # 栈顶地址
    numss = 0
    for ii in symidx.items():
        print(ii)

    for ss in s.params_symtab.keys():
        assList.append(Assembly('sw', 'a' + str(numss), symidx[ss][0], '(s0)'))
        numss += 1

    TempReg = {}
    LList = {}
    L = 2
    i = 0
    retarr = 0
    vis = [0] * len(f.quad_list)
    falsei = []
    hasor = 0
    hascall = 0
    hasret = 0

    while i < len(f.quad_list):
        if i == 251:
            print('hi')
        if len(assList)>455:
            print('hi')
        print(i)
        q = f.quad_list[i]
        if vis[i] == 0:
            vis[i] = 1
        else:
            i = i + 1
            continue

        if i in falsei:
            assList.append('.L' + str(LList['L_' + str(i)]) + ':')

        nexti = i + 1
        if i != len(f.quad_list) - 1:
            nextq = f.quad_list[i + 1]

        # existL=LList.get('L_'+str(i),-1)
        # if existL!=-1:
        #     assList.append('.L'+str(LList['L_'+str(i)]))

        conditionList[i] = len(assList)
        if q.op == 'call':
            hascall = 1
            for farg in range(1, len(q.arg2)):
                if isinstance(q.arg2[farg][1], MyConstant):
                    assList.append(Assembly('li', 'a' + str(farg - 1), q.arg2[farg][0]))
                elif isinstance(q.arg2[farg][1], TmpValue):
                    if TempReg[q.arg2[farg][0]] != 'a' + str(farg - 1):
                        assList.append(Assembly('mv', 'a' + str(farg - 1), TempReg[q.arg2[farg][0]]))
                    r.funarg[TempReg[q.arg2[farg][0]]].isEmpty = True
                else:
                    assList.append(Assembly('lw', 'a' + str(farg - 1), symidx[q.arg2[farg][0]][0], '(s0)'))

            assList.append(Assembly('call', q.arg1[0]))
            Reg0 = r.GetEmptyF()
            assList.append(Assembly('mv', Reg0, 'a0'))
            TempReg[q.dest[0]] = Reg0

        elif q.op == 'j':
            nexti = int(q.dest[0][2:])
            if nexti != (i + 1):
                if nexti < i:
                    assList.insert(conditionList[nexti], '.L' + str(L)+':')
                    LList[q.dest[0]] = L
                    assList.append(Assembly('j', '.L' + str(LList[q.dest[0]])))
                    L += 1
                    rec = 0
                    for k in conditionList.keys():
                        if k == nexti:
                            rec = 1
                        if rec == 1:
                            conditionList[k] += 1

                else:
                    loc = LList.get(q.dest[0], -1)
                    if loc == -1:
                        LList[q.dest[0]] = L
                        L += 1
                        falsei.append(nexti)
                    assList.append(Assembly('j', '.L' + str(LList[q.dest[0]])))
                continue
            else:
                i += 1
                continue

        elif (q.op == 'j<' or q.op == 'j>' or q.op == 'j=' or
              q.op == 'j<=' or q.op == 'j>=' or q.op == 'j!=' or
              q.op == 'j=='):
            if q.op != 'j=':

                vis[i + 1] = 1
                vis[i + 2] = 1
                vis[i + 3] = 1
                Reg0 = r.GetEmptyF()
                if not (isinstance(q.arg1[1], MyConstant) or isinstance(q.arg1[1], TmpValue)):
                    r.funarg[Reg0].symname = q.arg1[0]
                    assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0], '(s0)'))
                elif isinstance(q.arg1[1], TmpValue):
                    r.funarg[Reg0].isEmpty = True
                    Reg0 = TempReg[q.arg1[0]]
                else:
                    r.funarg[Reg0].isEmpty = True
                    assList.append(Assembly('li', Reg0, q.arg1[0]))

                Reg1 = r.GetEmptyF()
                if not (isinstance(q.arg2[1], MyConstant) or isinstance(q.arg2[1], TmpValue)):
                    r.funarg[Reg1].symname = q.arg2[0]
                    assList.append(Assembly('lw', Reg1, symidx[q.arg2[0]][0], '(s0)'))
                elif isinstance(q.arg2[1], TmpValue):
                    r.funarg[Reg0].isEmpty = True
                    Reg1 = TempReg[q.arg2[0]]
                else:
                    r.funarg[Reg0].isEmpty = True
                    assList.append(Assembly('li', Reg1, q.arg2[0]))

                tmpi = i
                while tmpi < len(f.quad_list):
                    if f.quad_list[tmpi].op == 'j=':
                        break
                    if f.quad_list[tmpi].op == '||':
                        if hasor == 0:
                            hasor = 1
                        elif hasor == 1:
                            hasor = 2
                    tmpi += 1
                nexti = int(q.dest[0][2:])
                orq = f.quad_list[tmpi]
                tmpq = f.quad_list[tmpi + 1]
                if hasor == 1:
                    LList[orq.dest[0]] = L
                    L += 1
                    falsei.append(int(orq.dest[0][2:]))
                loc = LList.get(tmpq.dest[0], -1)
                if loc == -1:
                    LList[tmpq.dest[0]] = L
                    tmpnexti = int(tmpq.dest[0][2:])
                    if tmpnexti < i:
                        assList.insert(conditionList[tmpnexti], '.L' + str(L)+':')
                        LList[q.dest[0]] = L

                        L += 1
                        rec = 0
                        for k in conditionList.keys():
                            if k == tmpnexti:
                                rec = 1
                            if rec == 1:
                                conditionList[k] += 1
                    else:
                        L += 1
                if hasor == 1:
                    if q.op == 'j<':
                        assList.append(Assembly('ble', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                    elif q.op == 'j>':
                        assList.append(Assembly('bge', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                    elif q.op == 'j!=':
                        assList.append(Assembly('bne', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                    elif q.op == 'j==':
                        assList.append(Assembly('beq', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                    elif q.op == 'j<=':
                        assList.append(Assembly('bgt', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                    elif q.op == 'j>=':
                        assList.append(Assembly('blt', Reg0, Reg1, '.L' + str(LList[orq.dest[0]])))
                else:
                    if q.op == 'j<':
                        assList.append(Assembly('bge', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))
                    elif q.op == 'j>':
                        assList.append(Assembly('ble', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))
                    elif q.op == 'j!=':
                        assList.append(Assembly('beq', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))
                    elif q.op == 'j==':
                        assList.append(Assembly('bne', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))
                    elif q.op == 'j<=':
                        assList.append(Assembly('bgt', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))
                    elif q.op == 'j>=':
                        assList.append(Assembly('blt', Reg0, Reg1, '.L' + str(LList[tmpq.dest[0]])))

                if Reg0 in r.funarg.keys():
                    r.funarg[Reg0].isEmpty = True
                if Reg1 in r.funarg.keys():
                    r.funarg[Reg1].isEmpty = True
            else:
                nexti = int(q.dest[0][2:])
                if nexti < i:
                    assList.insert(conditionList[nexti], '.L' + str(L)+':')
                    LList[q.dest[0]] = L
                    assList.append(Assembly('j', '.L' + str(LList[q.dest[0]])))
                    L += 1
                    rec = 0
                    for k in conditionList.keys():
                        if k == nexti:
                            rec = 1
                        if rec == 1:
                            conditionList[k] += 1
                falsei.append(int(nextq.dest[0][2:]))
                vis[i + 1] = 1
        elif q.op == '||':
            hasor = 0

        elif q.op == '=':
            # 赋值语句
            if (q.arg1[0] == 'False' or q.arg1[0] == 'True'):
                i = i + 1
                continue
            if f.quad_list[i + 1].op == '++' or f.quad_list[i + 1].op == '--':
                i += 1
                continue

            # 处理赋值
            if isinstance(q.arg1[1], MyConstant) and isinstance(q.dest[1], TmpValue):
                '''
                tmpretarr=i
                while tmpretarr<len(f.quad_list):
                    if f.quad_list[tmpretarr].op=='[]=' or f.quad_list[tmpretarr].op=='=[]':
                        break
                    tmpretarr+=1
                retarr=i
                i=tmpretarr
                continue
                '''
                Reg0 = r.GetEmptyF()
                TempReg[q.dest[0]] = Reg0
                assList.append(Assembly('li', Reg0, q.arg1[0]))
                i += 1
                continue
            if isinstance(q.arg1[1], TmpValue):  # 临时变量
                if (q.dest[1].type == 'int' or q.dest[1].type == 'long int' or
                        q.dest[1].type == 'signed' or q.dest[1].type == 'unsigned' or
                        q.dest[1].type == 'int'):
                    Reg0 = TempReg[q.arg1[0]]
                    assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    r.funarg[Reg0].isEmpty = True
                elif (q.dest[1].type == 'short' or q.dest[1].type == 'short int'):
                    Reg0 = TempReg[q.arg1[0]]
                    assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                    r.funarg[Reg0].isEmpty = True
                elif (q.dest[1].type == 'long long' or q.dest[1].type == 'long long int'):
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
            else:  # 立即数和变量
                Reg0 = r.GetEmptyF()
                r.funarg[Reg0].symname = q.dest[0]
                if isinstance(q.arg1[1], MyConstant):
                    assList.append(Assembly('li', Reg0, int(q.arg1[0]) % (2 ** 31)))
                    if (q.dest[1].type == 'int' or q.dest[1].type == 'long int' or
                            q.dest[1].type == 'signed' or q.dest[1].type == 'unsigned' or
                            q.dest[1].type == 'int'):
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type == 'short' or q.dest[1].type == 'short int'):
                        assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type == 'long long' or q.dest[1].type == 'long long int'):
                        Reg1 = r.GetEmptyF()
                        r.funarg[Reg1].symname = q.dest[0]

                        assList.append(Assembly('li', Reg1, math.floor(int(q.arg1[0]) / (2 ** 31))))

                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        assList.append(Assembly('sw', Reg1, symidx[q.dest[0]][1], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    else:
                        assList.append(Assembly('sb', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                else:
                    assList.append(Assembly('li', Reg0, symidx[q.arg1[0]][0], '(s0)'))
                    if (q.dest[1].type == 'int' or q.dest[1].type == 'long int' or
                            q.dest[1].type == 'signed' or q.dest[1].type == 'unsigned' or
                            q.dest[1].type == 'int'):
                        assList.append(Assembly('sw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type == 'short' or q.dest[1].type == 'short int'):
                        assList.append(Assembly('sh', Reg0, symidx[q.dest[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif (q.dest[1].type == 'long long' or q.dest[1].type == 'long long int'):
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
        elif q.op == '++' or q.op == '--':

            Reg0 = r.GetEmptyF()
            r.funarg[Reg0].symname = q.arg1[0]
            assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0], 's0'))
            if q.op == '++':
                assList.append(Assembly('addi', Reg0, Reg0, 1))
            else:
                assList.append(Assembly('addi', Reg0, Reg0, -1))
            assList.append(Assembly('sw', Reg0, symidx[q.arg1[0]][0], 's0'))
            i += 2
            continue
        elif q.op=='-=' or q.op=='+=':

            if isinstance(q.arg1[1],MyConstant):
                Reg0=r.GetEmptyF()
                assList.append(Assembly('li', Reg0, q.arg1[0]))
            elif isinstance(q.arg1[1],TmpValue):
                Reg0=TempReg[q.arg1[0]]
            else:
                Reg0=r.GetEmptyF()
                assList.append(Assembly('lw',Reg0,symidx[q.arg1[0]][0],'(s0)'))

            if isinstance(q.dest[1],MyConstant):
                Reg1=r.GetEmptyF()
                assList.append(Assembly('li', Reg1, q.dest[0]))
            elif isinstance(q.dest[1],TmpValue):
                Reg1=TempReg[q.dest[0]]
            else:
                Reg1=r.GetEmptyF()
                assList.append(Assembly('lw',Reg1,symidx[q.dest[0]][0],'(s0)'))

            if q.op=='+=':
                assList.append(Assembly('add', Reg1,Reg0,Reg1))
            else:
                assList.append(Assembly('sub', Reg1, Reg0, Reg1))

            if isinstance(q.arg1[1],TmpValue):
                r.funarg[TempReg[q.arg1[0]]].isEmpty = True
            else:
                r.funarg[Reg0].isEmpty = True

            if not isinstance(q.dest[1], TmpValue):
                assList.append(Assembly('sw', Reg1, symidx[q.dest[0]][0], '(s0)'))
                r.funarg[Reg1].isEmpty = True

        elif (q.op == '+' or q.op == '-' or q.op == '^' or
              q.op == '|' or q.op == '&' or q.op == '<' or
              q.op == '>' or q.op == '*' or q.op == '/' or
              q.op=='%'):

            haschange = 0
            # 交换位置，保证第二个位置为常量
            if isinstance(q.arg1[1], MyConstant):
                temp = q.arg1
                q.arg1 = q.arg2
                q.arg2 = temp
                haschange = 1

            if isinstance(q.arg1[1], TmpValue):
                Reg0 = TempReg[q.arg1[0]]
            elif isinstance(q.arg1[1], MyConstant):
                Reg0 = q.arg1[0]
            else:
                Reg0 = r.GetEmptyF()
            if not isinstance(q.arg1[1], MyConstant):
                r.funarg[Reg0].symname = q.arg1[0]

            if isinstance(q.arg2[1], TmpValue):
                Reg1 = TempReg[q.arg2[0]]
            elif isinstance(q.arg2[1], MyConstant):
                Reg1 = q.arg2[0]
            else:
                Reg1 = r.GetEmptyF()

            if not isinstance(q.arg2[1], MyConstant):
                r.funarg[Reg1].symname = q.arg2[0]

            dest_arg=0
            if q.dest[0]==q.arg1[0]:
                Reg2 = TempReg[q.dest[0]]
                dest_arg = 1
            elif q.dest[0]==q.arg2[0]:
                Reg2 = TempReg[q.dest[0]]
                dest_arg = 2
            else:
                Reg2 = r.GetEmptyF()
                TempReg[q.dest[0]] = Reg2

            if not (isinstance(q.arg1[1], TmpValue) or isinstance(q.arg1[1], MyConstant)):
                assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0], '(s0)'))
            if not (isinstance(q.arg2[1], TmpValue) or isinstance(q.arg2[1], MyConstant)):
                assList.append(Assembly('lw', Reg1, symidx[q.arg2[0]][0], '(s0)'))

            if q.op == '+':

                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('addi', Reg2, Reg0, Reg1))
                else:
                    assList.append(Assembly('add', Reg2, Reg0, Reg1))
                if (q.arg1[1].type == 'short' or q.arg1[1].type == 'short int'):
                    assList.append(Assembly('slli', Reg2, Reg2, 16))
                    assList.append(Assembly('srli', Reg2, Reg2, 16))
            elif q.op == '-':

                if haschange == 1:
                    assList.append(Assembly('sub', Reg2, Reg1, Reg0))
                else:
                    assList.append(Assembly('sub', Reg2, Reg0, Reg1))
            elif q.op == '*':
                if isinstance(q.arg1[1],MyConstant):
                    Reg0=r.GetEmptyF()
                    assList.append(Assembly('li', Reg0,q.arg1[0]))
                if isinstance(q.arg2[1], MyConstant):
                    Reg1 = r.GetEmptyF()
                    assList.append(Assembly('li', Reg1,q.arg2[0]))
                assList.append(Assembly('mul', Reg2, Reg0, Reg1))
                if isinstance(q.arg1[1],MyConstant):
                    r.funarg[Reg0].isEmpty=True
                if isinstance(q.arg2[1], MyConstant):
                    r.funarg[Reg1].isEmpty=True

            elif q.op == '/':
                assList.append(Assembly('div', Reg2, Reg0, Reg1))
            elif q.op == '^':
                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('xori', Reg2, Reg0, Reg1))
                else:
                    assList.append(Assembly('xor', Reg2, Reg0, Reg1))
            elif q.op == '|':
                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('ori', Reg2, Reg0, Reg1))
                else:
                    assList.append(Assembly('or', Reg2, Reg0, Reg1))
            elif q.op == '&':
                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('andi', Reg2, Reg0, Reg1))
                else:
                    assList.append(Assembly('and', Reg2, Reg0, Reg1))
            elif q.op == '<':
                if isinstance(q.arg2[1], MyConstant):
                    assList.append(Assembly('slti', Reg2, Reg0, Reg1))
                else:
                    assList.append(Assembly('slt', Reg2, Reg0, Reg1))
                assList.append(Assembly('andi', Reg2, Reg2, '0xff'))
            elif q.op == '>':
                assList.append(Assembly('sgt', Reg2, Reg0, Reg1))
                assList.append(Assembly('andi', Reg2, Reg2, '0xff'))
            elif q.op=='%':
                if isinstance(q.arg2[1],MyConstant):
                    Reg1=r.GetEmptyF()
                    assList.append(Assembly('li',Reg1,q.arg2[0]))
                    assList.append(Assembly('rem',Reg2,Reg0,Reg1))
                    r.funarg[Reg1].isEmpty=True
                else:
                    assList.append(Assembly('rem', Reg2, Reg0, Reg1))
            if not (isinstance(q.arg1[1], MyConstant)):
                if (isinstance(q.arg1[1], TmpValue)) :
                    if dest_arg!=1:
                        r.funarg[TempReg[q.arg1[0]]].isEmpty = True
                else:
                    r.funarg[Reg0].isEmpty = True


            if not (isinstance(q.arg2[1], MyConstant)):
                if (isinstance(q.arg2[1], TmpValue)):
                    if dest_arg!=2:
                        r.funarg[TempReg[q.arg2[0]]].isEmpty = True
                else:
                    r.funarg[Reg1].isEmpty = True
        # 给数组赋值
        elif q.op == '[]=':
            if q.dest[1].type == 'array':
                arrayidx = symidx[q.dest[0]]
                if isinstance(q.arg2[1], TmpValue):
                    if isinstance(q.arg1[1], MyConstant):
                        Reg0 = r.GetEmptyF()
                        assList.append(Assembly('li', Reg0, q.arg1[0]))
                        assList.append(Assembly('add', TempReg[q.arg2[0]], 's0', TempReg[q.arg2[0]]))
                        assList.append(Assembly('sw', Reg0, arrayidx[0], '(' + TempReg[q.arg2[0]] + ')'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[TempReg[q.arg2[0]]].isEmpty = True
                    elif isinstance(q.arg1[1], TmpValue):
                        assList.append(Assembly('add', TempReg[q.arg2[0]], 's0', TempReg[q.arg2[0]]))
                        assList.append(Assembly('sw', TempReg[q.arg1[0]], arrayidx[0],
                                                '(' + TempReg[q.arg2[0]] + ')'))
                        r.funarg[TempReg[q.arg1[0]]].isEmpty = True
                        r.funarg[TempReg[q.arg2[0]]].isEmpty = True
                    else:
                        Reg0 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0],'(s0)'))
                        assList.append(Assembly('add',TempReg[q.arg2[0]],'s0',TempReg[q.arg2[0]]))
                        assList.append(Assembly('sw', Reg0, arrayidx[0], '(' + TempReg[q.arg2[0]] + ')'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[TempReg[q.arg2[0]]].isEmpty = True
                    i += 1
                    continue
                if q.dest[0] not in avis.keys():
                    Reg0 = r.GetEmptyF()
                    if q.dest[1].element_size == 4:
                        roList.append('.LC' + str(LC) + ':')
                        roList[-1]+='    .word ' + q.arg1[0]
                        #roList.append('    .word ' + q.arg1[0])
                        assList.append(Assembly('lui', Reg0, '%hi(.LC' + str(LC) + ')'))
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, '%lo(.LC' + str(LC) + ')', '(' + Reg0 + ')'))
                        Reg2 = r.GetEmptyF()
                        assList.append(Assembly('sw', Reg1, arrayidx[int(q.arg2[0]) // 4], '(s0)'))
                        assList.append(Assembly('addi', Reg2, Reg0, '%lo(.LC' + str(LC) + ')'))

                        avis[q.dest[0]] = [LC, Reg2]
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    elif q.dest[1].element_size == 2:
                        roList.append('.LC' + str(LC) + ':')
                        roList.append('    .half ' + q.arg1[0])
                        assList.append(Assembly('lui', Reg0, '%hi(.LC' + str(LC) + ')'))
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, '%lo(.LC' + str(LC) + ')', '(' + Reg0 + ')'))
                        Reg2 = r.GetEmptyF()
                        assList.append(Assembly('sh', Reg1, arrayidx[int(q.arg2[0]) // 2], '(s0)'))
                        assList.append(Assembly('addi', Reg2, Reg0, '%lo(.LC' + str(LC) + ')'))
                        avis[q.dest[0]] = [LC, Reg2]
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    elif q.dest[1].element_size == 1:
                        sroList.append('.LC' + str(LC) + ':')
                        sroList.append('    .byte ' + q.arg1[0])
                        assList.append(Assembly('lui', Reg0, '%hi(.LC' + str(LC) + ')'))
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, '%lo(.LC' + str(LC) + ')', '(' + Reg0 + ')'))
                        Reg2 = r.GetEmptyF()
                        assList.append(Assembly('sb', Reg1, arrayidx[int(q.arg2[0]) // 2], '(s0)'))
                        assList.append(Assembly('addi', Reg2, Reg0, '%lo(.LC' + str(LC) + ')'))
                        avis[q.dest[0]] = [LC, Reg2]
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                    else:
                        roList.append('.LC' + str(LC) + ':')

                        roList.append('    .word ' + str(int(q.arg1[0]) % (2 ** 31)))
                        roList.append('    .word ' + str(math.floor(int(q.arg1[0]) / (2 ** 31))))
                        assList.append(Assembly('lui', Reg0, '%hi(.LC' + str(LC) + ')'))
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, '%lo(.LC' + str(LC) + ')', '(' + Reg0 + ')'))

                        Reg2 = r.GetEmptyF()
                        Reg3 = r.GetEmptyF()
                        assList.append(Assembly('addi', Reg2, Reg0, '%lo(.LC' + str(LC) + ')'))
                        avis[q.dest[0]] = [LC, Reg2]
                        assList.append(Assembly('lw', Reg3, 4, '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('sw', Reg1, arrayidx[1], '(s0)'))
                        assList.append(Assembly('sw', Reg3, arrayidx[1], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                        r.funarg[Reg1].isEmpty = True
                        r.funarg[Reg3].isEmpty = True
                    LC += 1
                else:
                    if q.dest[1].element_size == 4:
                        roList[-1]+=','+q.arg1[0]
                        #roList.append('    .word ' + q.arg1[0])
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, q.arg2[0], '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('sw', Reg1, arrayidx[int(q.arg2[0]) // 4], '(s0)'))
                        r.funarg[Reg1].isEmpty = True
                        if nextq.op != '[]=' or nextq.dest[0] != q.dest[0]:
                            r.funarg[avis[q.dest[0]][1]].isEmpty = True
                    elif q.dest[1].element_size == 2:
                        roList.append('    .half ' + q.arg1[0])
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lhu', Reg1, q.arg2[0], '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('sh', Reg1, arrayidx[int(q.arg2[0]) // 2], '(s0)'))
                        r.funarg[Reg1].isEmpty = True
                        if nextq.op != '[]=' or nextq.dest[0] != q.dest[0]:
                            r.funarg[avis[q.dest[0]][1]].isEmpty = True
                    elif q.dest[1].element_size == 1:
                        sroList.append('    .byte ' + q.arg1[0])
                        Reg1 = r.GetEmptyF()
                        assList.append(Assembly('lbu', Reg1, q.arg2[0], '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('sb', Reg1, arrayidx[int(q.arg2[0]) // 2], '(s0)'))
                        r.funarg[Reg1].isEmpty = True
                        if nextq.op != '[]=' or nextq.dest[0] != q.dest[0]:
                            r.funarg[avis[q.dest[0]][1]].isEmpty = True
                    else:
                        roList.append('    .word ' + str(int(q.arg1[0]) % (2 ** 31)))
                        roList.append('    .word ' + str(math.floor(int(q.arg1[0]) / (2 ** 31))))
                        Reg1 = r.GetEmptyF()
                        Reg2 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg1, int(q.arg1[0]) % (2 ** 31), '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('lw', Reg2, math.floor(int(q.arg1[0]) / (2 ** 31)),
                                                '(' + avis[q.dest[0]][1] + ')'))
                        assList.append(Assembly('sw', Reg1, arrayidx[int(q.arg2[0]) // 4], '(s0)'))
                        assList.append(Assembly('sw', Reg2, arrayidx[int(q.arg2[0]) // 4 + 1], '(s0)'))
                        r.funarg[Reg1].isEmpty = True
                        r.funarg[Reg2].isEmpty = True
                        if nextq.op != '[]=' or nextq.dest[0] != q.dest[0]:
                            r.funarg[avis[q.dest[0]][1]].isEmpty = True
            else:
                sidx = fs.structidx[q.dest[0]]
                if isinstance(q.arg2[1], MyConstant):
                    if isinstance(q.arg1[1], MyConstant):
                        Reg0 = r.GetEmptyF()
                        assList.append(Assembly('li', Reg0, q.arg1[0]))
                        assList.append(Assembly('sw', Reg0, sidx[q.arg2[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    elif isinstance(q.arg1[1], TmpValue):
                        assList.append(Assembly('sw', TempReg[q.arg1[0]], sidx[q.arg2[0]][0], '(s0)'))
                    else:
                        Reg0 = r.GetEmptyF()
                        assList.append(Assembly('lw', Reg0, symidx[q.arg1[0]][0], '(s0)'))
                        assList.append(Assembly('sw', Reg0, sidx[q.arg2[0]][0], '(s0)'))
                        r.funarg[Reg0].isEmpty = True
                    i += 1
                    continue
                if q.dest[0] not in svis.keys():
                    Reg0 = r.GetEmptyF()
                    roList.append('.LC' + str(LC) + ':')
                    roList.append('    .word ' + q.arg1[0])
                    assList.append(Assembly('lui', Reg0, '%hi(.LC' + str(LC) + ')'))
                    Reg1 = r.GetEmptyF()
                    assList.append(Assembly('lw', Reg1, '%lo(.LC' + str(LC) + ')', '(' + Reg0 + ')'))
                    Reg2 = r.GetEmptyF()
                    assList.append(Assembly('sw', Reg1, sidx[f.quad_list[i - 1].arg1[0]][0], '(s0)'))
                    assList.append(Assembly('addi', Reg2, Reg0, '%lo(.LC' + str(LC) + ')'))
                    svis[q.dest[0]] = [LC, Reg2]
                    r.funarg[Reg0].isEmpty = True
                    r.funarg[Reg1].isEmpty = True
                    LC += 1
                else:
                    roList.append('    .word ' + q.arg1[0])
                    Reg1 = r.GetEmptyF()
                    assList.append(Assembly('lw', Reg1, sidx[f.quad_list[i - 1].arg1[0]][0] - sidx['0'][0],
                                            '(' + svis[q.dest[0]][1] + ')'))
                    assList.append(Assembly('sw', Reg1, sidx[f.quad_list[i - 1].arg1[0]][0], '(s0)'))
                    r.funarg[Reg1].isEmpty = True
                    if i + 2 < len(f.quad_list):
                        if (f.quad_list[i + 2].op == '[]=' and isinstance(nextq.dest[1], TmpValue)
                                and f.quad_list[i + 2].dest[0] == q.dest[0]):
                            i += 1
                            continue
                        else:
                            r.funarg[svis[q.dest[0]][1]].isEmpty = True
                    else:
                        r.funarg[svis[q.dest[0]][1]].isEmpty = True
        # 数组赋值给变量
        elif q.op == '=[]':
            if q.arg1[0] in avis.keys():
                arrayidx = symidx[q.arg1[0]]
                if isinstance(q.arg2[1], TmpValue):
                    Reg0 = r.GetEmptyF()
                    assList.append(Assembly('add', TempReg[q.arg2[0]], 's0', TempReg[q.arg2[0]]))
                    assList.append(Assembly('lw', Reg0, arrayidx[0], '(' + TempReg[q.arg2[0]] + ')'))
                    r.funarg[TempReg[q.arg2[0]]].isEmpty = True
                    TempReg[q.dest[0]]=Reg0
                    #r.funarg[Reg0].isEmpty=True
                # if isinstance(q.dest[1], TmpValue):
                #     Reg1= r.GetEmptyF()
                #     TempReg[q.dest[0]]=Reg1
            i = i + 1
            continue
        elif q.op == 'return':
            hasret = 1
            if isinstance(q.dest[1], MyConstant):
                Reg0 = r.GetEmptyF()
                assList.append(Assembly('li', Reg0, q.dest[0]))
                assList.append(Assembly('mv', 'a0', Reg0))
                r.funarg[Reg0].isEmpty = True
            elif isinstance(q.dest[1], TmpValue):
                assList.append(Assembly('mv', 'a0', TempReg[q.dest[0]]))
            else:
                Reg0 = r.GetEmptyF()
                assList.append(Assembly('lw', Reg0, symidx[q.dest[0]][0], '(s0)'))
                assList.append(Assembly('mv', 'a0', Reg0))
                r.funarg[Reg0].isEmpty = True
        elif q.op == 'end':
            if hasret == 0:
                Reg0 = r.GetEmptyF()
                assList.append(Assembly('li', Reg0, 0))
                assList.append(Assembly('mv', 'a0', Reg0))
                r.funarg[Reg0].isEmpty = True
        if nexti != (i + 1):
            i = nexti
        else:
            i += 1

    assList.append(Assembly('lw', 's0', fs.size - 4, '(sp)'))  # 保存返回地址
    assList.append(Assembly('addi', 'sp', 'sp', fs.size))  # 恢复sp
    assList.append(Assembly('jr', 'ra'))  # 跳转到ra地址
    if hascall == 1:
        assList[1].arg2 = fs.size - 8
        assList.insert(1, Assembly('sw', 'ra', fs.size - 4, '(sp)'))
        assList[1].arg2 = fs.size - 8
        assList.insert(-3, Assembly('lw', 'ra', fs.size - 4, '(sp)'))
    for i in symidx.items():
        print(i)
    return sroList, roList, assList


def GenAss(file, flag=True):
    parser = CParser()
    if flag:
        with open(file, 'r') as f:
            ast = parser.parse(f.read(), file)
    else:
        ast = parser.parse(file)
    sts = symtab.symtab_store(ast)
    sts.show(ast)
    t = sts.get_symtab_of(ast)
    structlist = GetStruct(t)

    text = []
    data = []
    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('--------------start to get flow graph--------------------')
            flowGraph = FlowGraph(ch, sts)
            tt = t[ch.decl.name]
            text.append(ch.decl.name + ':')
            sroList, roList, assList = FunctionAss(flowGraph, tt, structlist)
            text += assList
            data = data + sroList + roList
    num = 0
    res = []
    if data:
        res.append('.data')
        res += data
        res.append('.dataend')
    else:
        res += data
    res += text
    print('--------------start to get assembly--------------------')
    num=0
    for i in res:
        num += 1
        print(num,'  ',i)
    return res


if __name__ == '__main__':
    filename = '../c_file/global.c'
    # filename = '../c_file/function.c'
    res = GenAss(filename)
    with open('output.txt', 'w') as f:
        for i in res:
            f.write(str(i) + "\n")
"""
以下内容由于架构问题，编写.c时应当做一定修改:
1. a=fun1(arg)+b 应改写为 int temp=fun1(arg); a=temp+b
2. 条件判断只能出现一次&&或者一次||，如果出现多个，需要分开判断条件，例如:
if(a<b||a>c&&a<d){
    a+=1;
}
else{a+=2;}
--->
if(a<b){
    a+=1; 
}
else{
    if(a>c&&a<d)
        a+=1;
    else
        a+=2;
}
3. 数组不能用变量寻址,例如a=b[a]，只能用立即数a=b[2];
4.函数参数不要超越7个
"""
