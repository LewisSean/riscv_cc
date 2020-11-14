# 接口

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

# 如要从符号表t中获取名为'x'的符号(包含了向祖先节点查询),使用下面的语句
x = t.get_symbol('x')
# x的类型是Symbol,Symbol类目前还没有设计,看后续有哪些需要再说
# 如果找不到返回None

```

# 约定

## 函数

代表函数的符号的offset是0,size是返回值的size,void的size是0.

代表函数的符号有一个成员变量param_k,表示该函数接收几个参数.

函数的返回值offset是0,然后从1开始是参数,参数结束后才是局部变量.