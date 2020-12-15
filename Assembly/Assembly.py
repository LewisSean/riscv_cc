from pycparser import c_ast
from pycparser import CParser
import symtab

class Assembly:
    def __init__(self,op=None,arg1=None,arg2=None,arg3=None):
        self.op=op
        self.arg1=arg1
        self.arg2=arg2
        self.arg3=arg3

    def __repr__(self):
        ans=' '*4
        ans+=str(self.op)+' '*4
        ans+=str(self.arg1)
        if self.arg2 is not None:
            ans+=','+str(self.arg2)
        if self.arg3 is not None:
            if str(self.arg3)[0] !='(':
                ans += ',' + str(self.arg2)
            else:
                ans +=str(self.arg2)
        return ans

class GlobalVar:
    def __init__(self,name=None,align=0,type=None,size=0,word=None):
        self.name=name
        self.align=align
        self.type=type
        self.size=size
        self.word=word

    def __repr__(self):
        ans=' '*4
        ans+='.global'+' '*2+str(self.name)+'\n'
        ans += '.align' + ' ' * 2 + str(self.align)+'\n'
        ans += '.type' + ' ' * 2 + str(self.name)+','+str(self.type)+'\n'
        ans += '.size' + ' ' * 2 + str(self.name)+','+str(self.size)+'\n'
        ans+=str(self.name)+':\n'
        for i in range(len(self.word)):
            if i !=len(self.word)-1:
                ans+='.word'+' '*2  +self.word[i]+'\n'
            else:
                ans += '.word' + ' ' * 2 + self.word[i]
        return ans


class FunctionStack():
    def __init__(self,size=0):
        self.size=size
        self.funstack={}

def CalSize(s:symtab.FuncSymbol)->FunctionStack:
    varList=s.local_symbols
    f=FunctionStack()
    loc=-16
    funstack={}
    csremain=0#处理char和short部分
    for var in varList:
        #变量部分
        if(isinstance(var,symtab.BasicSymbol)):
            #4字节 int,long int,long,signed,unsigned
            if(var.type=='int' or var.type=='long int'
                or var.type=='long' or var.type=='signed'
                    or var.type == 'unsigned'):
                csremain = 0
                loc-=4
                funstack[var.name]=[loc]
            #8字节 long long,long long int
            elif(var.type=='long long'
                 or var.type=='long long int'):
                csremain=0
                loc -= 8
                #低位数据存在地位上
                funstack[var.name] = [loc,loc+4]
            #2字节 short int,short
            elif (var.type == 'short int'
                    or var.type == 'short'):
                if csremain==0 or csremain==1:
                    csremain=4
                    loc-=4
                    csremain-=2
                    funstack[var.name] = [loc+csremain]
                # elif csremain==2:
                #     csremain -= 2
                #     funstack[var.name] = [loc]
                else:
                    csremain=0
                    funstack[var.name] = [loc]
            #1字节 char
            elif var.type == 'char':
                if csremain == 0:
                    csremain = 4
                    loc -= 4
                csremain -= 1
                funstack[var.name] = [loc + csremain]
        elif(isinstance(var, symtab.ArraySymbol)):
            print('arr')
        elif(isinstance(var, symtab.StructSymbol)):
            print('struct')


    f.funstack=funstack
    f.size=-loc
    return f





def FunctionAss(s:FunctionStack):
    assList=[]
    assList.append(Assembly('addi','sp','sp',s.size))



    return assList

if __name__=='__main__':
    file = '../c_file/zc2.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab.symtab_store(ast)
    sts.show(ast)
    t=sts.get_symtab_of(ast)
    tt=t['main']

    f=CalSize(tt)
    for i in f.funstack.items():
        print(i)