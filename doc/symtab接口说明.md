symtab是符号表模块

预期的使用方法如下:

```python
import symtab

# 假定ast是解析.c得到的语法树根节点
# 用下面的语句初始化语法树每个节点的符号表,存储在sts中
sts = symtab.symtab_store(ast)

# 假定u是语法树的任意节点(类型是c_ast.Node),用下面的语句获取该节点的符号表
t = sts.get_symtab_of(u)
# t的类型是SymTab

# 如要从符号表t中获取名为'x'的符号,使用下面的语句
x = t.get_symbol('x')
# x的类型是Symbol,Symbol类目前还没有设计,看后续有哪些需要再说

```