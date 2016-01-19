from collections import namedtuple

Node = namedtuple('Node', ['type'])


reserved = {
    'while': 'WHILE'
}

tokens = [
    'NAME', 'ASSIGN', 'NUMBER',
    'COMP',
    'PLUS','MINUS','TIMES','DIVIDE',
    'LPAREN', 'RPAREN', 'LCURL', 'RCURL',
    'SEMICOLON', 'COLON'
]

tokens.extend(reserved.values())

t_ASSIGN  = r':='
# t_NUMBER  = r'\d+'
t_COMP    = r'<'

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
t_COLON = r','


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


# lexer.input(text)

# while True:
#     token = lexer.token()
#     if token is None:
#         break

#     print token


CONST_INT = namedtuple('CONST_INT', ['value'])
BINOP = namedtuple('BINOP', ['type', 'left', 'right'])
ASSIGN = namedtuple('ASSIGN', ['name', 'value'])
LOAD_VAR = namedtuple('LOAD_VAR', ['name'])
LOOP = namedtuple('LOOP', ['condition', 'body'])
CALL = namedtuple('CALL', ['name', 'args'])

def p_statements(p):
    '''statements : statement statement
                  | statement
    '''

    p[0] = []
    p[0].append(p[1])

    if len(p) == 3:
        p[0].append(p[2])


def p_statement(p):
    '''statement : assignment SEMICOLON
                 | expression SEMICOLON
                 | while
    '''
    p[0] = p[1]

def p_assignment(p):
    '''assignment : NAME ASSIGN expression'''
    p[0] = ASSIGN(name=p[1], value=p[3])

def p_empty(p):
    'empty :'
    pass

def p_expression_list(p):
    '''expression_list : expression COLON expression
                  | expression
                  | empty
    '''

    p[0] = []
    for e in p[1:]:
        p[0].append(e)

def p_expression_call(p):
    '''expression : expression LPAREN expression_list RPAREN
    '''
    p[0] = CALL(name=p[1], args=p[3])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression COMP expression
    '''

    p[0] = BINOP(
        type=p[2],
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

def p_block(p):
    'block : LCURL statements RCURL'
    p[0] = p[2]

def p_error(t):
    print("Syntax error at '%s'" % t.value)

from pprint import pprint
import ply.yacc as yacc
parser = yacc.yacc()

parse = parser.parse