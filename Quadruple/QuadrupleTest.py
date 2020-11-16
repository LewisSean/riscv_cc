from pycparser.c_parser import CParser
from preprocess import preprocess_cmd
from pycparser import c_ast
from Quadruple.block import Quadruple
'''
def error_func(msg, location0, location1):
    print(msg, location0, location1)
    pass


def on_lbrace_func():
    pass


def on_rbrace_func():
    pass


def type_lookup_func(val):
    pass


lex = CLexer(error_func, on_lbrace_func, on_rbrace_func, type_lookup_func)
lex.build()
# delete float
lex.keywords = (
        '_BOOL', '_COMPLEX', 'AUTO', 'BREAK', 'CASE', 'CHAR', 'CONST',
        'CONTINUE', 'DEFAULT', 'DO', 'DOUBLE', 'ELSE', 'ENUM', 'EXTERN',
        'FOR', 'GOTO', 'IF', 'INLINE', 'INT', 'LONG',
        'REGISTER', 'OFFSETOF',
        'RESTRICT', 'RETURN', 'SHORT', 'SIGNED', 'SIZEOF', 'STATIC', 'STRUCT',
        'SWITCH', 'TYPEDEF', 'UNION', 'UNSIGNED', 'VOID',
        'VOLATILE', 'WHILE', '__INT128',
    )

print(lex.tokens)
'''

mode = 1

if mode == 0:
    s = preprocess_cmd(r'../c_file/year.c',
                       'gcc', ['-nostdinc', '-E', r'-I./c_file/fake_libc_include'])

    with open('../gcc_E_file.out', 'w') as f:
        f.write(s)

    parser = CParser()
    ast = parser.parse(s, './c_file/year.c')
    ast.show()
    print(ast)

else:
    with open('../c_file/test_decl.c', 'r') as f:
        s = f.read()
    parser = CParser()
    ast = parser.parse(s, './c_file/test_decl.c')
    with open('../decls.out', 'w') as f:
        f.write(str(ast))
    ast.show()
    print("ast completed");
"""    for node in ast.ext:
        if isinstance(node, (c_ast.Decl, c_ast.FuncDecl, c_ast.Struct,)):
            pass"""
class block():
    # 入口 出口  符号表   四元组的列表
    pass

# blocks = dict()
# seed = 0
# seed+=1
# blocks[seed] = block()


def GenDecl(node):
    declList=[]
    if(node.init==None):
        declList.append(Quadruple(0, '=', 0, '_', node.type.declname))
    elif isinstance(node.init,c_ast.Constant):
        declList.append(Quadruple(0,'=',node.init.value,'_',node.type.declname))
    else:
        asssignList,rec=GenAssignment(node.init,1)
        declList+=asssignList
        declList.append(Quadruple(0,'=','t'+str(rec),'_',node.type.declname))
    return declList

def GenAssignment(node,mode=0):
    rec = 0
    def GenAss(node):
        nonlocal rec
        assignmentList=[]
        if isinstance(node,c_ast.Assignment):
            assignmentList += GenAss(node.rvalue)[0]
            assignmentList.append(Quadruple(0, '=', "t" + str(rec), '_', node.lvalue.name))
            return assignmentList,rec

        if isinstance(node,c_ast.ID):
            rec += 1
            assignmentList.append(Quadruple(0,'=',node.name,'_',"t"+str(rec)))
            return assignmentList,rec

        if isinstance(node,c_ast.UnaryOp):
            rec += 1
            if isinstance(node.expr,c_ast.ID):
                assignmentList.append(GenUnaryOp(1, node.op, node.expr.name, '_', "t" + str(rec)))
            elif isinstance(node.expr, c_ast.Constant):
                assignmentList.append(GenUnaryOp(1, node.op, node.expr.value, '_', "t" + str(rec)))
            return assignmentList,rec

        if isinstance(node,c_ast.BinaryOp):
            lassignmentList,lrec= GenAss(node.left)
            rassignmentList,rrec = GenAss(node.right)
            assignmentList+=lassignmentList+rassignmentList
            rec += 1
            assignmentList.append(Quadruple(2, node.op, "t" + str(lrec), "t" + str(rrec), "t" + str(rec)))
            return assignmentList,rec
    if mode:
        return GenAss(node)
    else:
        return GenAss(node)[0]

def GenUnaryOp(type,op,arg1,arg2,dest):
    if op=='p++' or '++':
        return Quadruple(type,'+=',1,arg2,arg1)
    elif op=='p--'or '--':
        return Quadruple(type, '-=', 1, arg2, arg1)
    else:
        return Quadruple(type,op,arg1,arg2,dest)




tmp=ast.ext[0].body.block_items
print("tmp completed")
ans=[]

for i in tmp:
    if isinstance(i,c_ast.Assignment):
        ans+=GenAssignment(i)
    elif isinstance(i,c_ast.Decl):
        ans+=GenDecl(i)
    elif isinstance(i,c_ast.UnaryOp):
        ans.append(GenUnaryOp(0, i.op, i.expr.name,'_','_'))
for i in ans:
    print(i)
for i in ans:
    if i.arg2=='_':
        if i.op=='=':
            print(i.dest,i.op,i.arg1)
        elif i.op=='+=' or '-=':
             print(i.dest,i.op,i.arg1)
        else:
            print(i.dest,'=',i.op,i.arg1)
    else:
        print(i.dest,'=',i.arg1,i.op,i.arg2)






