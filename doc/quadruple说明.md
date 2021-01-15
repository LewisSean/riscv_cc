# 关于包Quadruple的说明
## 结构
1. **block_graph.py**生成代码块block的有向图
2. **block_graph.py**调用**block.py**为每一个block生成四元组，保存在**block.Quadruples**属性中。 
## 使用
### FlowGraph
- 调用**Quadruple.block_graph**中的类**FlowGraph**
- 一个**FlowGraph**对象保存一个函数的四元组信息，通过属性**quad_list**查看
```python
# 对文件ls.c中的所有函数生成四元组
from Quadruple.block_graph import FlowGraph
    file = '../c_file/ls.c'
    parser = CParser()
    with open(file, 'r') as f:
        ast = parser.parse(f.read(), file)

    sts = symtab_store(ast)
    sts.show(ast)

    for ch in ast.ext:
        if isinstance(ch, c_ast.FuncDef):
            print('--------------start to get flow graph--------------------')
            flowGraph = FlowGraph(ch, sts)
```

### Quadruple
- **FlowGraph.Quadruple**保存的是一个Quadruple对象的list。
- Quadruple对象：arg1、arg2和dest保存的是 (名称 : name, 类型 ：type(symtab.Symbol\Quadruple.quadruple.TmpValue\Quadruple.quadruple.MyConstant))，
dest还可以保存('L_xx', 'loc')表示要跳转的地址是该四元组列表的第xx行。

##支持的语法
- 目前的数组和结构体初始化，只支持一维初始化，即：
```c
int c[2][3] = {1,2,3,4,5,6};
```
- 支持 [ ]对多维数组的读和写
- 支持使用 *对多维数组进行访问
- 支持结构体嵌套结构体的 .和 ->运算
- 支持结构体内嵌套数组
- 支持goto语法
- 支持while，do while
- 支持if / else if / else
- 支持continue和break
- 支持引用 & 与指针 *
- 支持绝大多数表达式运算
- **暂不支持sizeof和显式类型转换**
- **暂不支持单独的i++和i--运算，可用i=i+1替换**
