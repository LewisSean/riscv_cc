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

    def CalSize(self,s:symtab.FuncSymbol):
        varList=s.local_symbols





def FunctionAss(s:FunctionStack):
    assList=[]
    assList.append(Assembly('addi','sp','sp',s.size))



    return assList

if __name__=='__main__':
    file = '../c_file/wyb1.c'
    parser = CParser()
    with open(file,'r') as f:
        ast = parser.parse(f.read(), file)
    sts = symtab.symtab_store(ast)
    sts.show(ast)
    t=sts.get_symtab_of(ast)
    tt=t['main'].local_symbols
    for i in tt:
        print(i)
