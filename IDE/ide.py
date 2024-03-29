import sys
sys.path.append('..')
import tkinter as tk
from tkinter import filedialog, messagebox
import builtins
import tkinter.font as tkfont
from pycparser import c_ast
from pycparser import CParser
from pycparser.plyparser import ParseError
from symtab import symtab_store
from Quadruple.block_graph import FlowGraph
from Assembly.Assembly import GenAss

# a notepad for c ide
class YScrollBar(tk.Scrollbar):

    def __init__(self, parent, *args, **kwargs):
        tk.Scrollbar.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.grid(column=2, row=0, sticky="nesw")


class XScrollBar(tk.Scrollbar):

    def __init__(self, parent, *args, **kwargs):
        tk.Scrollbar.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(orient=tk.HORIZONTAL)
        self.grid(columnspan=2,column=0, row=1, sticky="nesw")


class SyntaxHighlighter:

    def __init__(self, parent, *args, **kwargs):
        self.keywordList = [
            'break', 'case','const', 'continue', 'do',
            'else', 'enum', 'for', 'goto', 'if', 'register', 'return',   'sizeof',
            'static', 'switch', 'union',
            'while',
        ]
        self.constantList = ["true", "false"]
        self.built_in_names = ['float ', 'int ', 'long ', 'short ', 'signed ', 'unsigned ', 'void ', 'struct ', 'char ', 'double ', ]
        self.keywordHightlight = "red"
        self.builtinHightlight = "blue"
        self.stringHighlight = "green"
        self.constantHighlight = "gold2"
        self.parent = parent

        self.status = True

        self.parent.textArea.tag_configure('highlight-keyword', foreground=self.keywordHightlight)
        self.parent.textArea.tag_configure('highlight-builtins', foreground=self.builtinHightlight)
        self.parent.textArea.tag_configure('highlight-string', foreground=self.stringHighlight)
        self.parent.textArea.tag_configure('highlight-constant', foreground=self.constantHighlight)

    def toggle_highlight(self):

        if self.status:
            self.clearHighlight()
            self.status = False
        else:
            self.status = True
            self.HighlightText()

    def clearHighlight(self):
        cursorPos = self.parent.textArea.index(tk.INSERT)
        yviewTextArea = self.parent.textArea.yview()[0]
        yviewLineNum = self.parent.lineNumber.yview()[0]
        text = self.parent.textArea.get("1.0", 'end-1c')
        self.parent.textArea.delete("1.0", tk.END)
        self.parent.textArea.insert(tk.END, text)
        self.parent.textArea.mark_set("insert", cursorPos)
        self.parent.textArea.yview(tk.MOVETO, yviewTextArea)
        self.parent.lineNumber.yview(tk.MOVETO, yviewLineNum)

    def HighlightText(self):
        # Still work that could be done by using regex instead of simple search methods.
        if not self.status:
            return

        # first we need to clear all previous highlighting.
        self.clearHighlight()
        # keyword loop
        for keyword in self.keywordList:
            start = 0.0
            while True:
                pos = self.parent.textArea.search(keyword, start, stopindex=tk.END)
                if not pos:
                    break

                self.parent.textArea.delete(pos, pos+"+" + str(len(keyword)) + "c")
                self.parent.textArea.insert(pos, keyword, 'highlight-keyword')
                start = pos + "+1c"
        # Builtins loop
        for built_in_name in self.built_in_names:
            start = 0.0
            while True:
                pos = self.parent.textArea.search(built_in_name, start, stopindex=tk.END)
                if not pos:
                    break
                self.parent.textArea.delete(pos, pos+"+" + str(len(built_in_name)) + "c")
                self.parent.textArea.insert(pos, built_in_name, 'highlight-builtins')
                start = pos + "+1c"

        # constant loop
        for constant in self.constantList:
            start = 0.0
            while True:
                pos = self.parent.textArea.search(constant, start, stopindex=tk.END)
                if not pos:
                    break

                self.parent.textArea.delete(pos, pos+"+" + str(len(constant)) + "c")
                self.parent.textArea.insert(pos, constant, 'highlight-constant')
                start = pos + "+1c"

        # string loop
        # Need to find beginning quote, then go to next quote, and use pos of both to tag the stuff inbetween
        start = 0.0
        while True:
            pos = self.parent.textArea.search("\"", start, stopindex=tk.END)
            # we have the pos of the first quote, now need to find the second one.
            if not pos:
                break
            start = pos + "+1c"
            pos2 = self.parent.textArea.search("\"", start, stopindex=tk.END)
            if not pos2:
                break
            # once we have the pos of both quotes, we take it out, and reinsert and tag.
            pos2 = pos2 + "+1c"
            cursorPos = self.parent.textArea.index(tk.INSERT)
            stringText = self.parent.textArea.get(pos, pos2)
            self.parent.textArea.delete(pos, pos2)
            self.parent.textArea.insert(pos, stringText, 'highlight-string')
            self.parent.textArea.mark_set("insert", cursorPos)
            start = pos2 + "+1c"


class LineNumberText(tk.Text):
    def __init__(self, parent, *args, **kwargs):
        tk.Text.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=4, relief="flat")
        self.grid(column=0, row=0, sticky=(tk.W, tk.N, tk.S))
        self.tag_configure('tag-right', justify='right')
        self.config(font=("Courier", 10))
        self.config(fg="grey")
        self.numberOfLines = 0
        self.updateLineNumbers(type="key")

    # logic for displaying number of lines in a file.
    def updateLineNumbers(self, type, *args):

        if type == "mouse":
            self.yview(tk.MOVETO, self.parent.textArea.yview()[0])
        else:
            if self.numberOfLines != int(self.parent.textArea.index('end-1c').split('.')[0]):
                self.config(state=tk.NORMAL)
                self.numberOfLines = 0
                lineNumbers = ""
                for x in range(int(self.parent.textArea.index('end-1c').split('.')[0])):
                    if x == int(self.parent.textArea.index('end-1c').split('.')[0])-1:
                        lineNumbers = lineNumbers + str(x+1)
                    else:
                        lineNumbers = lineNumbers + str(x+1) + "\n"
                    self.numberOfLines = self.numberOfLines + 1
                self.delete(1.0, tk.END)
                self.insert(tk.END, lineNumbers, 'tag-right')
                self.config(state=tk.DISABLED)

                self.parent.textArea.see(self.parent.textArea.index(tk.INSERT))

                self.see(self.parent.textArea.index(tk.INSERT))

            else:
                self.yview(tk.MOVETO, self.parent.textArea.yview()[0])



    def set_dark_mode(self, *args):
        self.config(bg="#282c34")
        self.config(fg="grey")
        self.config(insertbackground="white")

    def set_light_mode(self, *args):
        self.config(bg="white")
        self.config(fg="grey")
        self.config(insertbackground="black")


class InfoText(tk.Label):
    def __init__(self, parent, *args, **kwargs):
        tk.Label.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.place(relx=1.0, rely=1.0,x=-17, y=-17,anchor="se")
        self.config(text="", bg="white")

    def set_dark_mode(self, *args):
        self.config(bg="#282c34")
        self.config(fg="white")

    def set_light_mode(self, *args):
        self.config(bg="white")
        self.config(fg="black")


class TextArea(tk.Text):
    def __init__(self, parent, *args, **kwargs):
        tk.Text.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=100, wrap="none")
        self.grid(column=1, row=0, sticky=(tk.E, tk.N, tk.S, tk.W))
        self.config(relief="flat")
        self.config(font=("Courier", 10))

        # 修改tab缩进的空格数
        font = tkfont.Font(font=self['font'])
        tab = font.measure('    ')
        self.config(tabs=tab)


    def set_dark_mode(self, *args):
        self.config(bg="#282c34")
        self.config(fg="white")
        self.config(insertbackground="white")

    def set_light_mode(self, *args):
        self.config(bg="white")
        self.config(fg="black")
        self.config(insertbackground="black")

class MainMenu(tk.Menu):
    def __init__(self, parent, *args,  **kwargs):
        self.parent = parent
        tk.Menu.__init__(self, parent, *args, **kwargs)


        self.file_options = tk.Menu(self, tearoff=0)
        self.file_options.add_command(label='{0: <20}'.format('New'))
        self.file_options.add_command(label='{0: <20}'.format('Open') + "Ctrl+O", command=self.parent.open_file)
        self.file_options.add_command(label='{0: <20}'.format('Save')  + "Ctrl+S", command=self.parent.save_file)
        self.file_options.add_command(label='{0: <20}'.format('Save as...'), command=self.parent.save_file_as)
        self.file_options.add_command(label='{0: <20}'.format('Exit'), command=self.parent.save_and_quit)

        #Need to be Implemented
        self.edit_options = tk.Menu(self, tearoff=0)
        self.edit_options.add_command(label='{0: <20}'.format('Copy') + "Ctrl+C")
        self.edit_options.add_command(label='{0: <20}'.format('Cut') + "Ctrl+V")
        self.edit_options.add_command(label='{0: <20}'.format('Select All') + "Ctrl+A")

        self.compile_options = tk.Menu(self, tearoff=0)
        self.compile_options.add_command(label='{0: <20}'.format('Gen quadruples'), command=self.parent.save_qurdruaples)
        self.compile_options.add_command(label='{0: <20}'.format('Gen .asm'), command=self.parent.gen_asm)

        self.add_cascade(label="File", menu=self.file_options)
        self.add_cascade(label="Edit", menu=self.edit_options)
        self.add_cascade(label="Clear all", command=lambda: self.parent.textArea.delete(1.0,tk.END))
        self.add_cascade(label="Dark Mode", command=self.parent.set_dark_mode)
        self.add_cascade(label="Line #\'s", command=self.parent.toggle_line_numbers)
        self.add_cascade(label="C syntax", command=self.parent.toggle_highlight)
        self.add_cascade(label="Compile", menu=self.compile_options)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):

        tk.Frame.__init__(self, parent, *args, **kwargs)

        # 保存一个编译对象
        self.parser = CParser()

        # Varibles
        self.filename = ""
        self.numberOfKeyPresses = 0

        # Setting Parent/Parent config
        self.parent = parent
        self.parent.title("riscv_cc")
        # Setting up grid positioning
        self.grid(column=0, row=0,sticky=(tk.N,tk.W,tk.E,tk.S))
        self.columnconfigure(0,weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(2,weight=0)
        # Creating widgets
        self.textArea = TextArea(self)
        self.lineNumber = LineNumberText(self)
        self.yScrollBar = YScrollBar(self)
        self.xScrollBar = XScrollBar(self)

        self.yScrollBar.config(command=self.update_scrollbarY)
        self.xScrollBar.config(command=self.update_scrollbarX)

        self.textArea.config(yscrollcommand=self.yScrollBar.set, xscrollcommand=self.xScrollBar.set)

        self.main_menu = MainMenu(self)
        self.InfoText = InfoText(self)

        self.syntaxHighlighter = SyntaxHighlighter(self)
        # Setting focus
        self.textArea.focus()
        # Bindings
        self.parent.bind('<Control-s>', self.save_file)
        self.parent.bind('<Key>',  self.updateOnKeyPress)
        self.parent.bind('<Button-1>', self.updateOnMousePress)
        self.parent.bind('<MouseWheel>', self.updateOnMouseWheel)
        # Parent Menu configuration
        self.parent.config(menu=self.main_menu)


    # Functions
    def update_scrollbarY(self, *args):
        self.textArea.yview(*args)
        self.lineNumber.yview(*args)

    def update_scrollbarX(self, *args):
        self.textArea.xview(*args)
        self.lineNumber.xview(*args)

    def toggle_highlight(self, *args):
        self.syntaxHighlighter.toggle_highlight()

    def toggle_line_numbers(self, *args):
        if self.lineNumber.grid_info():
            self.lineNumber.grid_forget()
            self.textArea.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        else:
            self.lineNumber.grid(column=0, row=0, sticky=(tk.N, tk.W,tk.S))
            self.textArea.grid(column=1, columnspan=2,row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    def updateOnMouseWheel(self, *args):
        self.update_info_text()
        self.lineNumber.updateLineNumbers(type="mouse")

    def updateOnMousePress(self, *agrs):
        self.update_info_text()
        self.lineNumber.updateLineNumbers(type="mouse")

    def updateOnKeyPress(self, *args):
        self.update_info_text()
        if self.numberOfKeyPresses == 10:
            self.syntaxHighlighter.HighlightText()
            self.numberOfKeyPresses = 0
        else:
            self.numberOfKeyPresses = self.numberOfKeyPresses + 1
        self.lineNumber.updateLineNumbers(type="key")

    def set_dark_mode(self, *args):
        self.InfoText.set_dark_mode()
        self.textArea.set_dark_mode()
        self.lineNumber.set_dark_mode()
        self.config(bg="#282c34")
        self.main_menu.entryconfig(4, label="Light Mode", command=self.set_light_mode)

    def set_light_mode(self, *args):
        self.InfoText.set_light_mode()
        self.textArea.set_light_mode()
        self.lineNumber.set_light_mode()
        self.config(bg="#282c34")
        self.main_menu.entryconfig(4, label="Dark Mode", command=self.set_dark_mode)

    def clear_info_text(self, *args):
        self.InfoText.config(text="")

    def set_info_text(self, msg, *args):
        self.InfoText.config(text=msg)

    def update_info_text(self, *args):
        coords = self.textArea.index(tk.INSERT).split(".")
        self.set_info_text("Row " + coords[0] + " Col " + coords[1])

    def get_text(self,*args):
            print(self.textArea.get("1.0", 'end-1c'))

    def open_file(self,*args):
        self.filename = filedialog.askopenfilename(initialdir = "./", title = "Select file", filetypes = (("C file", "*.c"),("All files", "*.*")))
        # we can use our filename to open up our text file
        try:
            with open(self.filename, 'r') as file:
                self.textArea.delete('1.0', tk.END)
                self.textArea.insert('1.0', file.read())

        except:
            #Person didn't select a file
            return
        self.parent.title("pyNotePad - Now Editing " + str(self.filename.split('/')[-1]))
        self.set_info_text("File Opened")
        self.updateOnKeyPress()
        self.syntaxHighlighter.HighlightText()

    def save_file_as(self,*args):
        self.filename = filedialog.asksaveasfile(mode='w', defaultextension=".c", filetypes = (("C file","*.c"),("All files","*.*")))
        if self.filename is None:
            return
        text = str(self.textArea.get(1.0, tk.END))
        self.filename.write(text)
        self.filename.close()
        self.set_info_text("File Saved")
        self.updateOnKeyPress()

    def parse_text(self):
        text = str(self.textArea.get(1.0, tk.END))
        try:
            ast = self.parser.parse(text)
            return ast
        except ParseError as e:
            return e

    def save_qurdruaples(self,*args):
        self.filename = filedialog.asksaveasfile(mode='w', defaultextension=".o", filetypes = (("Out file","*.o"), ("All files","*.*")))
        if self.filename is None:
            return

        ast = self.parse_text()
        if not isinstance(ast, c_ast.FileAST):
            # file : line : column
            items = str(ast)[1:].split(':', 2)
            print(items)
            messagebox.showerror('出错了', 'compile error on Line {} Col {}: {}'.format(items[0], items[1], items[2]))
        else:
            # 生成四元组
            sts = symtab_store(ast)
            sts.show(ast)
            for ch in ast.ext:
                if isinstance(ch, c_ast.FuncDef):
                    flowGraph = FlowGraph(ch, sts)
                    self.filename.write('----------quadruples for function: {} ------------'.format(ch.decl.name) + '\n')
                    for qua in flowGraph.quad_list:
                        self.filename.write(str(qua) + '\n')
            self.filename.close()
            self.set_info_text("File Saved")
            self.updateOnKeyPress()

    def gen_asm(self):
        self.filename = filedialog.asksaveasfile(mode='w', defaultextension=".s", filetypes = (("Source file", "*.s"), ("All files", "*.*")))
        if self.filename is None:
            return

        ast = self.parse_text()
        if not isinstance(ast, c_ast.FileAST):
            # file : line : column
            items = str(ast)[1:].split(':', 2)
            print(items)
            messagebox.showerror('出错了', 'compile error on Line {} Col {}: {}'.format(items[0], items[1], items[2]))
        else:
            # 生成汇编文件
            res = GenAss(str(self.textArea.get(1.0, tk.END)), False)
            for i in res:
                self.filename.write(str(i) + "\n")
            self.filename.close()
            self.set_info_text("File Saved")
            self.updateOnKeyPress()

    def save_file(self,*args):
        with open(self.filename, 'w') as file:
            text = str(self.textArea.get(1.0, tk.END))
            file.write(text)
            file.close()
            self.set_info_text("File Saved")
            self.updateOnKeyPress()

    def save_and_quit(self, *args):
        with open(self.filename, 'w') as file:
            text = str(self.textArea.get(1.0, tk.END))
            file.write(text)
            file.close()
            exit()


if __name__ == "__main__":
    root = tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
