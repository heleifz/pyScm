# -*- coding: utf-8 -*-

"""\
pyScm : yet another Scheme interpreter

Author : Lei He
Date : 2014/7
"""

import re
import sys

# Lexer + Parser

def parse(code):
    """Transform Scheme code to Python list"""
    pieces = re.split(r'(\s|\(|\)|\')', code)
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
            if not ast[-1] or ast[-1][-1] != "'":
                ast[-1].append(p)
            # deal with quoting
            else:
                ast[-1].pop()
                ast[-1].append(['quote', p])
    ast = ast[0]
    ast.insert(0, 'begin')
    return ast

# Convert nested list to pairs

def pylist_to_pairs(lst):
    if not isinstance(lst, list):
        if is_primitive(lst):
            return eval_primitive(lst)
        else:
            return make_symbol(lst)
    elif len(lst) == 0:
        return []
    else:
        return [pylist_to_pairs(lst[0]), pylist_to_pairs(lst[1:])]

def map_recursively(lst, func):
    if not isinstance(lst, list):
        return func(lst)
    elif lst == []:
        return lst
    else:
        result = [map_recursively(lst[0], func)]
        result.extend(map_recursively(lst[1:], func))
        return result

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

def is_application(exp):
    return isinstance(exp, list) and len(exp) > 0

def is_lambda(exp):
    return is_tagged_list(exp, 'lambda')

def is_definition(exp):
    return is_tagged_list(exp, 'define')

def is_set(exp):
    return is_tagged_list(exp, 'set!')

def is_sequence(exp):
    return is_tagged_list(exp, 'begin')

def is_quote(exp):
    return is_tagged_list(exp, 'quote')

def is_if(exp):
    return is_tagged_list(exp, 'if')

def is_let(exp):
    return is_tagged_list(exp, 'let')

def is_cond(exp):
    return is_tagged_list(exp, 'cond')

# Primitive functions

def display(args):
    sys.stdout.write(str(map_recursively(args[0], str)))

def add(args):
    return reduce(lambda x,y:x+y, args, 0)

def sub(args):
    return reduce(lambda x,y:x-y, args)

def mul(args):
    return reduce(lambda x,y:x*y, args, 1)

def div(args):
    return reduce(lambda x,y:x/y, args)

def lt(args):
    return make_boolean(args[0] < args[1])

def gt(args):
    return make_boolean(args[0] > args[1])

def le(args):
    return make_boolean(args[0] <= args[1])

def ge(args):
    return make_boolean(args[0] >= args[1])

def eq(args):
    return make_boolean(args[0] == args[1])

def eq_question_mark(args):
    if (args[0] == [] and args[1] == []):
        return make_boolean(True)
    return make_boolean(args[0] is args[1])

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

class Symbol(object):

    def __init__(self, name):
        self.__name = name

    def __str__(self):
        return self.__name

def make_symbol(name, symbol_table={}):
    if not name in symbol_table:
        symbol_table[name] = Symbol(name)
    return symbol_table[name]

def make_boolean(is_true):
    if is_true:
        return make_symbol('#t')
    else:
        return make_symbol('#f')

# Metacircular evaluator

def eval_primitive(exp):
    if is_number(exp):
        return eval(exp)
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

def eval_set(exp, env, eval_env):
    if exp[1] in env:
        env[exp[1]] = evaluate(exp[2], eval_env)
    else:
        eval_set(exp, env['**parent**'], eval_env)

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

# Expand derived structure

def let_to_lambda(exp):
    bindings = zip(*exp[1])
    paras = list(bindings[0])
    args = bindings[1]
    body = exp[2:]
    f = [['lambda', paras] + body]
    f.extend(args)
    return f

def evaluate(exp, env):
    """Evaluate parsed Scheme list in an environment"""
    while True:
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
        elif is_set(exp):
            return eval_set(exp, env, env)
        elif is_sequence(exp):
            eval_sequence(exp[1:-1], env)
            exp = exp[-1]
        elif is_if(exp):
            condition = evaluate(exp[1], env)
            # type 1 : (if cond exp1 exp2)
            if len(exp) == 4:
                if condition is make_boolean(True):
                    exp = exp[2]
                else:
                    exp = exp[3]
            elif len(exp) == 3:
                if condition is make_boolean(True):
                    exp = exp[2]
                else:
                    return None
        elif is_cond(exp):
            clauses = exp[1:]
            for c in clauses:
                if c[0] != 'else':
                    cond = evaluate(c[0], env)
                    if cond is make_boolean(True):
                        exp = c[1]
                        break
                else:
                    exp = c[1]
                    break
            else:
                return None
        elif is_let(exp):
            exp = let_to_lambda(exp)
        # must be the last clause
        elif is_application(exp):
            args = [evaluate(arg, env) for arg in exp]
            proc = args[0]
            args = args[1:]
            if isinstance(proc, PrimitiveFunction):
                return proc.apply(args)
            elif isinstance(proc, Lambda):
                new_env = dict(zip(proc.get_paras(), args))
                new_env['**parent**'] = proc.get_parent_env()
                env = new_env
                exp = proc.get_body()[:]
                exp.insert(0, 'begin')
        else:
            return

# Make base Environment

def make_base():
    env = {}

    # Primitive functions
    env['display'] = PrimitiveFunction(display)
    env['cons'] = PrimitiveFunction(cons)
    env['car'] = PrimitiveFunction(car)
    env['cdr'] = PrimitiveFunction(cdr)
    env['+'] = PrimitiveFunction(add)
    env['-'] = PrimitiveFunction(sub)
    env['*'] = PrimitiveFunction(mul)
    env['/'] = PrimitiveFunction(div)
    env['>'] = PrimitiveFunction(gt)
    env['>='] = PrimitiveFunction(gt)
    env['<'] = PrimitiveFunction(lt)
    env['<='] = PrimitiveFunction(le)
    env['='] = PrimitiveFunction(eq)
    env['eq?'] = PrimitiveFunction(eq_question_mark)

    # Constants
    env['#f'] = make_boolean(False)
    env['#t'] = make_boolean(True)

    return env

def run(code, env):
    return evaluate(parse(code), env)

if __name__ == "__main__":
    pass