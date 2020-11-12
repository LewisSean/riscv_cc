lex部分
    keywords = (
        '_BOOL', '_COMPLEX', 'AUTO', 'BREAK', 'CASE', 'CHAR', 'CONST',
        'CONTINUE', 'DEFAULT', 'DO', 'DOUBLE', 'ELSE', 'ENUM', 'EXTERN',
        'FOR', 'GOTO', 'IF', 'INLINE', 'INT', 'LONG',
        'REGISTER', 'OFFSETOF',
        'RESTRICT', 'RETURN', 'SHORT', 'SIGNED', 'SIZEOF', 'STATIC', 'STRUCT',
        'SWITCH', 'TYPEDEF', 'UNION', 'UNSIGNED', 'VOID',
        'VOLATILE', 'WHILE',
    )

        # Identifiers
        'ID',

        # Type identifiers (identifiers previously defined as
        # types with typedef)
        'TYPEID',

        # constants
        'INT_CONST_DEC', 'INT_CONST_OCT', 'INT_CONST_HEX', 'INT_CONST_BIN', 'INT_CONST_CHAR',
        'FLOAT_CONST', 'HEX_FLOAT_CONST',
        'CHAR_CONST',
        'WCHAR_CONST',

        # String literals
        'STRING_LITERAL',
        'WSTRING_LITERAL',

        # Operators
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
        'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT',
        'LOR', 'LAND', 'LNOT',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

        # Assignment
        'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL',
        'PLUSEQUAL', 'MINUSEQUAL',
        'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL',
        'OREQUAL',

        # Increment/decrement
        'PLUSPLUS', 'MINUSMINUS',

        # Structure dereference (->)
        'ARROW',

        # Conditional operator (?)
        'CONDOP',

        # Delimeters
        'LPAREN', 'RPAREN',         # ( )
        'LBRACKET', 'RBRACKET',     # [ ]
        'LBRACE', 'RBRACE',         # { }
        'COMMA', 'PERIOD',          # . ,
        'SEMI', 'COLON',            # ; :

        # Ellipsis (...)
        'ELLIPSIS',

        # pre-processor
        'PPHASH',       # '#'
        'PPPRAGMA',     # 'pragma'
        'PPPRAGMASTR',



--------------------------------------------------------------------------------------
yacc部分


%token ID TYPEID INT_CONST_DEC INT_CONST_OCT INT_CONST_HEX INT_CONST_BIN INT_CONST_CHAR FLOAT_CONST HEX_FLOAT_CONST CHAR_CONST WCHAR_CONST STRING_LITERAL WSTRING_LITERAL
%token PLUS MINUS TIMES DIVIDE MOD OR AND NOT XOR LSHIFT RSHIFT LOR LAND LNOT LT LE GT GE EQ NE 
%token EQUALS TIMESEQUAL DIVEQUAL MODEQUAL PLUSEQUAL MINUSEQUAL LSHIFTEQUAL RSHIFTEQUAL ANDEQUAL XOREQUAL OREQUAL 
%token PLUSPLUS MINUSMINUS 
%token ARROW 
%token CONDOP 
%token LPAREN RPAREN LBRACKET RBRACKET LBRACE RBRACE COMMA PERIOD SEMI COLON 
%token ELLIPSIS STRUCT UNION ENUM
%token CASE DEFAULT IF ELSE SWITCH WHILE DO FOR GOTO CONTINUE BREAK RETURN
%token PPHASH PPPRAGMA PPPRAGMASTR 



%start translation_unit

%%

translation_unit    : external_declaration
;

translation_unit    : translation_unit external_declaration
;

external_declaration    : function_definition
;

external_declaration    : declaration
;

external_declaration    : pp_directive
                                    | pppragma_directive
;

external_declaration    : SEMI
;

pp_directive  : PPHASH
;

pppragma_directive      : PPPRAGMA
                                    | PPPRAGMA PPPRAGMASTR
;

function_definition : id_declarator declaration_list_opt compound_statement
;

function_definition : declaration_specifiers id_declarator declaration_list_opt compound_statement
;

statement   : labeled_statement
                        | expression_statement
                        | compound_statement
                        | selection_statement
                        | iteration_statement
                        | jump_statement
                        | pppragma_directive
;

pragmacomp_or_statement     : pppragma_directive statement
                                        | statement
;

decl_body : declaration_specifiers init_declarator_list_opt
                      | declaration_specifiers_no_type id_init_declarator_list_opt
;

declaration : decl_body SEMI
;

declaration_list    : declaration
                                | declaration_list declaration
;

declaration_specifiers_no_type  : type_qualifier declaration_specifiers_no_type_opt
;

declaration_specifiers_no_type  : storage_class_specifier declaration_specifiers_no_type_opt
;

declaration_specifiers_no_type  : function_specifier declaration_specifiers_no_type_opt
;

declaration_specifiers  : declaration_specifiers type_qualifier
;

declaration_specifiers  : declaration_specifiers storage_class_specifier
;

declaration_specifiers  : declaration_specifiers function_specifier
;

declaration_specifiers  : declaration_specifiers type_specifier_no_typeid
;

declaration_specifiers  : type_specifier
;

declaration_specifiers  : declaration_specifiers_no_type type_specifier
;

storage_class_specifier : AUTO
                                    | REGISTER
                                    | STATIC
                                    | EXTERN
                                    | TYPEDEF
;

function_specifier  : INLINE
;

type_specifier_no_typeid  : VOID
                                      | _BOOL
                                      | CHAR
                                      | SHORT
                                      | INT
                                      | LONG
                                      | FLOAT
                                      | DOUBLE
                                      | _COMPLEX
                                      | SIGNED
                                      | UNSIGNED
                                      | __INT128
;

type_specifier  : typedef_name
                            | enum_specifier
                            | struct_or_union_specifier
                            | type_specifier_no_typeid
;

type_qualifier  : CONST
                            | RESTRICT
                            | VOLATILE
;

init_declarator_list    : init_declarator
                                    | init_declarator_list COMMA init_declarator
;

init_declarator : declarator
                            | declarator EQUALS initializer
;

id_init_declarator_list    : id_init_declarator
                                       | id_init_declarator_list COMMA init_declarator
;

id_init_declarator : id_declarator
                               | id_declarator EQUALS initializer
;

specifier_qualifier_list    : specifier_qualifier_list type_specifier_no_typeid
;

specifier_qualifier_list    : specifier_qualifier_list type_qualifier
;

specifier_qualifier_list  : type_specifier
;

specifier_qualifier_list  : type_qualifier_list type_specifier
;

struct_or_union_specifier   : struct_or_union ID
                                        | struct_or_union TYPEID
;

struct_or_union_specifier : struct_or_union brace_open struct_declaration_list brace_close
                                      | struct_or_union brace_open brace_close
;

struct_or_union_specifier   : struct_or_union ID brace_open struct_declaration_list brace_close
                                        | struct_or_union ID brace_open brace_close
                                        | struct_or_union TYPEID brace_open struct_declaration_list brace_close
                                        | struct_or_union TYPEID brace_open brace_close
;

struct_or_union : STRUCT
                            | UNION
;

struct_declaration_list     : struct_declaration
                                        | struct_declaration_list struct_declaration
;

struct_declaration : specifier_qualifier_list struct_declarator_list_opt SEMI
;

struct_declaration : SEMI
;

struct_declaration : pppragma_directive
;

struct_declarator_list  : struct_declarator
                                    | struct_declarator_list COMMA struct_declarator
;

struct_declarator : declarator
;

struct_declarator   : declarator COLON constant_expression
                                | COLON constant_expression
;

enum_specifier  : ENUM ID
                            | ENUM TYPEID
;

enum_specifier  : ENUM brace_open enumerator_list brace_close
;

enum_specifier  : ENUM ID brace_open enumerator_list brace_close
                            | ENUM TYPEID brace_open enumerator_list brace_close
;

enumerator_list : enumerator
                            | enumerator_list COMMA
                            | enumerator_list COMMA enumerator
;

enumerator  : ID
                        | ID EQUALS constant_expression
;

declarator  : id_declarator
                        | typeid_declarator
;

xxx_declarator  : direct_xxx_declarator
;

xxx_declarator  : pointer direct_xxx_declarator
;

direct_xxx_declarator   : yyy
;

direct_xxx_declarator   : LPAREN xxx_declarator RPAREN
;

direct_xxx_declarator   : direct_xxx_declarator LBRACKET type_qualifier_list_opt assignment_expression_opt RBRACKET
;

direct_xxx_declarator   : direct_xxx_declarator LBRACKET STATIC type_qualifier_list_opt assignment_expression RBRACKET
                                    | direct_xxx_declarator LBRACKET type_qualifier_list STATIC assignment_expression RBRACKET
;

direct_xxx_declarator   : direct_xxx_declarator LBRACKET type_qualifier_list_opt TIMES RBRACKET
;

direct_xxx_declarator   : direct_xxx_declarator LPAREN parameter_type_list RPAREN
                                    | direct_xxx_declarator LPAREN identifier_list_opt RPAREN
;

pointer : TIMES type_qualifier_list_opt
                    | TIMES type_qualifier_list_opt pointer
;

type_qualifier_list : type_qualifier
                                | type_qualifier_list type_qualifier
;

parameter_type_list : parameter_list
                                | parameter_list COMMA ELLIPSIS
;

parameter_list  : parameter_declaration
                            | parameter_list COMMA parameter_declaration
;

parameter_declaration   : declaration_specifiers id_declarator
                                    | declaration_specifiers typeid_noparen_declarator
;

parameter_declaration   : declaration_specifiers abstract_declarator_opt
;

identifier_list : identifier
                            | identifier_list COMMA identifier
;

initializer : assignment_expression
;

initializer : brace_open initializer_list_opt brace_close
                        | brace_open initializer_list COMMA brace_close
;

initializer_list    : designation_opt initializer
                                | initializer_list COMMA designation_opt initializer
;

designation : designator_list EQUALS
;

designator_list : designator
                            | designator_list designator
;

designator  : LBRACKET constant_expression RBRACKET
                        | PERIOD identifier
;

type_name   : specifier_qualifier_list abstract_declarator_opt
;

abstract_declarator     : pointer
;

abstract_declarator     : pointer direct_abstract_declarator
;

abstract_declarator     : direct_abstract_declarator
;

direct_abstract_declarator  : LPAREN abstract_declarator RPAREN
;

direct_abstract_declarator  : direct_abstract_declarator LBRACKET assignment_expression_opt RBRACKET
;

direct_abstract_declarator  : LBRACKET type_qualifier_list_opt assignment_expression_opt RBRACKET
;

direct_abstract_declarator  : direct_abstract_declarator LBRACKET TIMES RBRACKET
;

direct_abstract_declarator  : LBRACKET TIMES RBRACKET
;

direct_abstract_declarator  : direct_abstract_declarator LPAREN parameter_type_list_opt RPAREN
;

direct_abstract_declarator  : LPAREN parameter_type_list_opt RPAREN
;

block_item  : declaration
                        | statement
;

block_item_list : block_item
                            | block_item_list block_item
;

compound_statement : brace_open block_item_list_opt brace_close
;

labeled_statement : ID COLON pragmacomp_or_statement
;

labeled_statement : CASE constant_expression COLON pragmacomp_or_statement
;

labeled_statement : DEFAULT COLON pragmacomp_or_statement
;

selection_statement : IF LPAREN expression RPAREN pragmacomp_or_statement
;

selection_statement : IF LPAREN expression RPAREN statement ELSE pragmacomp_or_statement
;

selection_statement : SWITCH LPAREN expression RPAREN pragmacomp_or_statement
;

iteration_statement : WHILE LPAREN expression RPAREN pragmacomp_or_statement
;

iteration_statement : DO pragmacomp_or_statement WHILE LPAREN expression RPAREN SEMI
;

iteration_statement : FOR LPAREN expression_opt SEMI expression_opt SEMI expression_opt RPAREN pragmacomp_or_statement
;

iteration_statement : FOR LPAREN declaration expression_opt SEMI expression_opt RPAREN pragmacomp_or_statement
;

jump_statement  : GOTO ID SEMI
;

jump_statement  : BREAK SEMI
;

jump_statement  : CONTINUE SEMI
;

jump_statement  : RETURN expression SEMI
                            | RETURN SEMI
;

expression_statement : expression_opt SEMI
;

expression  : assignment_expression
                        | expression COMMA assignment_expression
;

typedef_name : TYPEID
;

assignment_expression   : conditional_expression
                                    | unary_expression assignment_operator assignment_expression
;

assignment_operator : EQUALS
                                | XOREQUAL
                                | TIMESEQUAL
                                | DIVEQUAL
                                | MODEQUAL
                                | PLUSEQUAL
                                | MINUSEQUAL
                                | LSHIFTEQUAL
                                | RSHIFTEQUAL
                                | ANDEQUAL
                                | OREQUAL
;

constant_expression : conditional_expression
;

conditional_expression  : binary_expression
                                    | binary_expression CONDOP expression COLON conditional_expression
;

binary_expression   : cast_expression
                                | binary_expression TIMES binary_expression
                                | binary_expression DIVIDE binary_expression
                                | binary_expression MOD binary_expression
                                | binary_expression PLUS binary_expression
                                | binary_expression MINUS binary_expression
                                | binary_expression RSHIFT binary_expression
                                | binary_expression LSHIFT binary_expression
                                | binary_expression LT binary_expression
                                | binary_expression LE binary_expression
                                | binary_expression GE binary_expression
                                | binary_expression GT binary_expression
                                | binary_expression EQ binary_expression
                                | binary_expression NE binary_expression
                                | binary_expression AND binary_expression
                                | binary_expression OR binary_expression
                                | binary_expression XOR binary_expression
                                | binary_expression LAND binary_expression
                                | binary_expression LOR binary_expression
;

cast_expression : unary_expression
;

cast_expression : LPAREN type_name RPAREN cast_expression
;

unary_expression    : postfix_expression
;

unary_expression    : PLUSPLUS unary_expression
                                | MINUSMINUS unary_expression
                                | unary_operator cast_expression
;

unary_expression    : SIZEOF unary_expression
                                | SIZEOF LPAREN type_name RPAREN
;

unary_operator  : AND
                            | TIMES
                            | PLUS
                            | MINUS
                            | NOT
                            | LNOT
;

postfix_expression  : primary_expression
;

postfix_expression  : postfix_expression LBRACKET expression RBRACKET
;

postfix_expression  : postfix_expression LPAREN argument_expression_list RPAREN
                                | postfix_expression LPAREN RPAREN
;

postfix_expression  : postfix_expression PERIOD ID
                                | postfix_expression PERIOD TYPEID
                                | postfix_expression ARROW ID
                                | postfix_expression ARROW TYPEID
;

postfix_expression  : postfix_expression PLUSPLUS
                                | postfix_expression MINUSMINUS
;

postfix_expression  : LPAREN type_name RPAREN brace_open initializer_list brace_close
                                | LPAREN type_name RPAREN brace_open initializer_list COMMA brace_close
;

primary_expression  : identifier
;

primary_expression  : constant
;

primary_expression  : unified_string_literal
                                | unified_wstring_literal
;

primary_expression  : LPAREN expression RPAREN
;

primary_expression  : OFFSETOF LPAREN type_name COMMA offsetof_member_designator RPAREN
;

offsetof_member_designator : identifier
                                         | offsetof_member_designator PERIOD identifier
                                         | offsetof_member_designator LBRACKET expression RBRACKET
;

argument_expression_list    : assignment_expression
                                        | argument_expression_list COMMA assignment_expression
;

identifier  : ID
;

constant    : INT_CONST_DEC
                        | INT_CONST_OCT
                        | INT_CONST_HEX
                        | INT_CONST_BIN
                        | INT_CONST_CHAR
;

constant    : FLOAT_CONST
                        | HEX_FLOAT_CONST
;

constant    : CHAR_CONST
                        | WCHAR_CONST
;

unified_string_literal  : STRING_LITERAL
                                    | unified_string_literal STRING_LITERAL
;

unified_wstring_literal : WSTRING_LITERAL
                                    | unified_wstring_literal WSTRING_LITERAL
;

brace_open  :   LBRACE
;

brace_close :   RBRACE
;

%%
