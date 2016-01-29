from collections import namedtuple

Node = namedtuple('Node', ['type'])


reserved = {
    'while': 'WHILE',
    'if': 'IF',
    'else': 'ELSE',
    'fn': 'FN',
    'print': 'PRINT',
}

tokens = [
    'NAME', 'ASSIGN', 'NUMBER',
    'COMP',
    'PLUS','MINUS','TIMES','DIVIDE',
    'LPAREN', 'RPAREN', 'LCURL', 'RCURL',
    'SEMICOLON', 'COMMA', 'RETURN'
]

tokens.extend(reserved.values())

t_ASSIGN  = r':='
# t_NUMBER  = r'\d+'
t_COMP    = r'==|!=|<|<=|>|>='

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
# t_EQUALS  = r'='

t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LCURL   = r'{'
t_RCURL   = r'}'
t_SEMICOLON = r';'
t_COMMA = r','

t_RETURN = r'\^'


t_ignore = ' \t\n'

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'NAME')    # Check for reserved words
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

import ply.lex as lex
lexer = lex.lex()

precedence = (
    ('left','COMP'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE'),
    # ('right','UMINUS'),
)


CONST_INT = namedtuple('CONST_INT', ['value'])
BINOP = namedtuple('BINOP', ['type', 'left', 'right'])
COMP = namedtuple('COMP', ['type', 'left', 'right'])
ASSIGN = namedtuple('ASSIGN', ['name', 'value'])
LOAD_VAR = namedtuple('LOAD_VAR', ['name'])
LOOP = namedtuple('LOOP', ['condition', 'body'])
COND = namedtuple('COND', ['condition', 'body', 'alt'])
CALL = namedtuple('CALL', ['name', 'args'])
FUNC = namedtuple('FUNC', ['name', 'args', 'body'])
RET = namedtuple('RET', ['expression'])
PRINT = namedtuple('PRINT', ['expression'])

def p_statements(p):
    '''statements : statements statement
                  | statement
    '''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_statement(p):
    '''statement : assignment SEMICOLON
                 | return SEMICOLON
                 | expression SEMICOLON
                 | print SEMICOLON
                 | if
                 | while
                 | func
    '''
    p[0] = p[1]


def p_assignment(p):
    '''assignment : NAME ASSIGN expression'''
    p[0] = ASSIGN(name=p[1], value=p[3])

def p_empty(p):
    'empty :'
    pass

def p_expression_list(p):
    '''expression_list : expression_list COMMA expression
                  | expression
                  | empty
    '''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])

def p_name_list(p):
    '''name_list : NAME COMMA NAME
            | NAME
            | empty
    '''

    return p_expression_list(p)

def p_func_def(p):
    '''func : FN NAME name_list block'''

    p[0] = FUNC(
        name=p[2],
        args=p[3],
        body=p[4]
        )

def p_return(p):
    '''return : RETURN expression'''
    p[0] = RET(p[2])


def p_print(p):
    '''print : PRINT expression'''
    p[0] = PRINT(p[2])

def p_expression_call(p):
    '''expression : expression LPAREN expression_list RPAREN
    '''
    p[0] = CALL(name=p[1], args=p[3])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
    '''

    p[0] = BINOP(
        type=p[2],
        left=p[1],
        right=p[3],
    )

def p_expression_comp(p):
    'expression : expression COMP expression'
    p[0] = COMP(type=p[2],
        left=p[1],
        right=p[3],
    )

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = CONST_INT(p[1])

def p_expression_name(p):
    'expression : NAME'
    p[0] = LOAD_VAR(p[1])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_while(p):
    'while : WHILE expression block'
    p[0] = LOOP(
        condition=p[2],
        body=p[3])

def p_if(p):
    '''if : IF expression block ELSE block
          | IF expression block ELSE if
          | IF expression
    '''
    # else if
    if len(p) == 6:
        if type(p[5]) != list:
            p[5] = [p[5]]
        p[0] = COND(
            condition=p[2],
            body=p[3],
            alt=p[5])
    else:
        p[0] = COND(
            condition=p[2],
            body=p[3],
            alt=None)

def p_block(p):
    'block : LCURL statements RCURL'
    p[0] = p[2]

def p_error(t):
    print("Syntax error at '%s'" % t.value)
    raise ValueError("Syntax error at '%s'" % t)

from pprint import pprint
import ply.yacc as yacc
parser = yacc.yacc()

parse = parser.parse