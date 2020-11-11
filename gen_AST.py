from pycparser.c_lexer import CLexer
from pycparser.c_parser import CParser
from lex.preprocess import preprocess_cmd


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

"""
s = preprocess_cmd(r'C:/users/Sean/Desktop/pycparser-master/examples/c_files/year.c',
                   'gcc', ['-nostdinc', '-E', r'-IC:/users/Sean/Desktop/pycparser-master/utils/fake_libc_include'])


with open('../lex/gcc_E_file.out', 'w') as f:
    f.write(s)


parser = CParser()
ast = parser.parse(s, r'C:/users/Sean/Desktop/pycparser-master/examples/c_files/year.c')
ast.show()
print(ast)

"""

with open('./test.c', 'r') as f:
    s = f.read()
parser = CParser()
ast = parser.parse(s, './test.c')
print(ast)


