from pycparser.c_lexer import CLexer
from pycparser.c_parser import CParser
from preprocess import preprocess_cmd


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

mode = 0

if mode == 0:
    s = preprocess_cmd(r'./c_file/year.c',
                       'gcc', ['-nostdinc', '-E', r'-I./c_file/fake_libc_include'])

    with open('./gcc_E_file.out', 'w') as f:
        f.write(s)

    parser = CParser()
    ast = parser.parse(s, './c_file/year.c')
    ast.show()
    print(ast)

else:
    with open('./c_file/test.c', 'r') as f:
        s = f.read()
    parser = CParser()
    ast = parser.parse(s, './c_file/test.c')
    print(ast)
