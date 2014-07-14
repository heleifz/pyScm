# -*- coding: utf-8 -*-

"""\
pyScm : yet another Scheme interpreter

Author : Lei He
Date : 2014/7
"""

import re

# Lexer + Parser

def parse(code):
    """Transform Scheme code to Python list"""
    pieces = re.split(r'(\s|\(|\))', code)
    pieces = [p for p in pieces if not re.match(r'^\s*$', p)]
    ast = [[]]
    for p in pieces:
        if p == '(':
            ast.append([])
        elif p == ')':
            lst = ast.pop() 
            if not ast[-1] or ast[-1][-1] != "'":
                ast[-1].append(lst)
            # deal with quoting
            else:
                ast[-1].pop()
                ast[-1].append(['quote', lst])
        else:
            ast[-1].append(p)
    ast = ast[0]
    ast.insert(0, 'begin')
    return ast

# Convert nested list to pairs

def pylist_to_pairs(lst):
    if not isinstance(lst, list):
        return lst
    elif len(lst) == 0:
        return []
    else:
        return [pylist_to_pairs(lst[0]), pylist_to_pairs(lst[1:])]

# Predicators

def is_number(exp):
    try:
        float(exp)
        return True
    except ValueError:
        return False

def is_string(exp):
    if exp[0] == exp[-1] == '"':
        return True

def is_primitive(exp):
    if not isinstance(exp, basestring):
        return False
    if is_number(exp):
        return True
    elif is_string(exp):
        return True
    return False

def is_tagged_list(exp, tag):
    return isinstance(exp, list) and len(exp) > 0 and exp[0] == tag

def is_variable(exp):
    return not is_primitive(exp) and isinstance(exp, basestring)

def is_lambda(exp):
    return is_tagged_list(exp, 'lambda')

def is_definition(exp):
    return is_tagged_list(exp, 'define')

def is_application(exp):
    return isinstance(exp, list) and len(exp) > 0

def is_sequence(exp):
    return is_tagged_list(exp, 'begin')

def is_quote(exp):
    return is_tagged_list(exp, 'quote')

# Primitive functions

def display(args):
    content = ""
    for a in args:
        content += str(a) + ' '
    print content

def add(args):
    return reduce(lambda x,y:x+y, args, 0)

def sub(args):
    return reduce(lambda x,y:x-y, args)

def mul(args):
    return reduce(lambda x,y:x*y, args, 1)

def div(args):
    return reduce(lambda x,y:x/y, args)

def cons(args):
    return [args[0], args[1]]

def cdr(args):
    return args[0][1]

def car(args):
    return args[0][0]

# Classes

class Lambda(object):
    def __init__(self, paras, body, parent_env):
        self.__paras = paras
        self.__body = body
        self.__parent_env = parent_env

    @staticmethod
    def make(lst, env):
        return Lambda(lst[1], lst[2:], env)

    def apply(self, args):
        env = dict(zip(self.__paras, args))
        env['**parent**'] = self.__parent_env
        return eval_sequence(self.__body, env)

    def get_paras(self):
        return self.__paras 
    def get_body(self):
        return self.__body
    def get_parent_env(self):
        return self.__parent_env

class PrimitiveFunction(object):
    def __init__(self, func):
        self.__func = func

    def apply(self, args):
        return self.__func(args) 

# Metacircular evaluator

def eval_primitive(exp):
    if is_number(exp):
        return float(exp)
    elif is_string(exp):
        return exp.strip('"');

def eval_variable(exp, env):
    if exp in env:
        return env[exp]
    elif '**parent**' in env:
        return eval_variable(exp, env['**parent**'])
    else:
        raise Exception('Undefine variable : ' + exp)

def eval_definition(exp, env):
    if is_variable(exp[1]):
        env[exp[1]] = evaluate(exp[2], env)
    else:
        env[exp[1][0]] = Lambda(exp[1][1:], exp[2:], env)

def eval_application(exp, env):
    args = [evaluate(arg, env) for arg in exp]
    return args[0].apply(args[1:])

def eval_quote(exp):
    return pylist_to_pairs(exp[1])

def eval_sequence(exp, env):
    result = None
    for e in exp:
        result = evaluate(e, env)
    return result

def evaluate(exp, env):
    """Evaluate parsed Scheme list in an environment"""
    if is_primitive(exp):
        return eval_primitive(exp)
    elif is_variable(exp):
        return eval_variable(exp, env)
    elif is_quote(exp):
        return eval_quote(exp)
    elif is_lambda(exp):
        return Lambda.make(exp, env)
    elif is_definition(exp):
        return eval_definition(exp, env)
    elif is_sequence(exp):
        return eval_sequence(exp[1:], env)
    # must be the last clause
    elif is_application(exp):
        return eval_application(exp, env)
    else:
        pass

# Make base Environment

def make_base():
    env = {}
    env['display'] = PrimitiveFunction(display)
    env['cons'] = PrimitiveFunction(cons)
    env['car'] = PrimitiveFunction(car)
    env['cdr'] = PrimitiveFunction(cdr)
    env['+'] = PrimitiveFunction(add)
    env['-'] = PrimitiveFunction(sub)
    env['*'] = PrimitiveFunction(mul)
    env['/'] = PrimitiveFunction(div)
    return env


