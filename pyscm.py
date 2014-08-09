# -*- coding: utf-8 -*-

"""\
pyScm : yet another Scheme interpreter

Author : Lei He
Date : 2014/7

I NEED A JOB!

"""

import re
import sys

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

def pylist_to_pairs(lst):
    """Convert nested list to pairs"""
    if not isinstance(lst, list):
        # violate SRP, but I dont care
        if is_primitive(lst):
            return eval_primitive(lst)
        else:
            return make_symbol(lst)
    elif len(lst) == 0:
        return []
    else:
        return [pylist_to_pairs(lst[0]), pylist_to_pairs(lst[1:])]

def map_recursively(lst, func):
    """Map recursively"""
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
    """Are you a number?"""
    try:
        float(exp)
        return True
    except ValueError:
        return False

def is_string(exp):
    """Are you a string?"""
    if exp[0] == exp[-1] == '"':
        return True

def is_primitive(exp):
    """Are you a number or string?"""
    if not isinstance(exp, basestring):
        return False
    if is_number(exp):
        return True
    elif is_string(exp):
        return True
    return False

def is_tagged_list(exp, tag):
    """Is your first element 'tag'?"""
    return isinstance(exp, list) and len(exp) > 0 and exp[0] == tag

def is_variable(exp):
    """Are you a variable?"""
    return not is_primitive(exp) and isinstance(exp, basestring)

def is_application(exp):
    """Are you a function application?"""
    return isinstance(exp, list) and len(exp) > 0

def is_lambda(exp):
    """Are you a function declaration?"""
    return is_tagged_list(exp, 'lambda')

def is_definition(exp):
    """Are you a definition?"""
    return is_tagged_list(exp, 'define')

def is_set(exp):
    """Are you a set?"""
    return is_tagged_list(exp, 'set!')

def is_sequence(exp):
    """Are you a sequence?"""
    return is_tagged_list(exp, 'begin')

def is_quote(exp):
    """Are you a quote?"""
    return is_tagged_list(exp, 'quote')

def is_if(exp):
    """Are you a if?"""
    return is_tagged_list(exp, 'if')

def is_let(exp):
    """Are you a let?"""
    return is_tagged_list(exp, 'let')

def is_cond(exp):
    """Are you a cond?"""
    return is_tagged_list(exp, 'cond')

# Primitive functions

def display(args):
    """Output to stdout"""
    sys.stdout.write(str(map_recursively(args[0], str)))

def add(args):
    """+"""
    return reduce(lambda x,y:x+y, args, 0)

def sub(args):
    """-"""
    return reduce(lambda x,y:x-y, args)

def mul(args):
    """*"""
    return reduce(lambda x,y:x*y, args, 1)

def div(args):
    """/"""
    return reduce(lambda x,y:x/y, args)

def lt(args):
    """<"""
    return make_boolean(args[0] < args[1])

def gt(args):
    """>"""
    return make_boolean(args[0] > args[1])

def le(args):
    """<="""
    return make_boolean(args[0] <= args[1])

def ge(args):
    """>="""
    return make_boolean(args[0] >= args[1])

def eq(args):
    """="""
    return make_boolean(args[0] == args[1])

def eq_question_mark(args):
    """eq?"""
    if (args[0] == [] and args[1] == []):
        return make_boolean(True)
    return make_boolean(args[0] is args[1])

def cons(args):
    """cons"""
    return [args[0], args[1]]

def cdr(args):
    """cdr"""
    return args[0][1]

def car(args):
    """car"""
    return args[0][0]

# Classes

class Lambda(object):
    """Lambda function object"""

    def __init__(self, paras, body, parent_env):
        """Initialize with parameters, body, and parent environment"""
        self.__paras = paras
        self.__body = body
        self.__parent_env = parent_env

    @staticmethod
    def make(lst, env):
        """Simple factory"""
        return Lambda(lst[1], lst[2:], env)

    def get_paras(self):
        """Get parameters"""
        return self.__paras 

    def get_body(self):
        """Get function body"""
        return self.__body

    def get_parent_env(self):
        """Get parent environment"""
        return self.__parent_env

class PrimitiveFunction(object):
    """Simply invoke python function"""

    def __init__(self, func):
        """Initialize with python function object"""
        self.__func = func

    def apply(self, args):
        """Same interface with Lambda"""
        return self.__func(args) 

class Symbol(object):
    """A symbol is simply a string that identifying itself"""

    def __init__(self, name):
        """Initialize with name"""
        self.__name = name

    def __str__(self):
        """Serialize to string"""
        return self.__name

def make_symbol(name, symbol_table={}):
    """Using default argument to initialize a global symbol table
    the symbol table is for symbol only!
    """

    if not name in symbol_table:
        symbol_table[name] = Symbol(name)
    return symbol_table[name]

def make_boolean(is_true):
    """#t for true, #f for false"""
    if is_true:
        return make_symbol('#t')
    else:
        return make_symbol('#f')

# Metacircular evaluator

def eval_primitive(exp):
    """Evaluate primitive object"""
    if is_number(exp):
        return eval(exp)
    elif is_string(exp):
        return exp.strip('"');

def eval_variable(exp, env):
    """Look up variable in environment chain"""
    if exp in env:
        return env[exp]
    elif '**parent**' in env:
        return eval_variable(exp, env['**parent**'])
    else:
        raise Exception('Undefine variable : ' + exp)

def eval_definition(exp, env):
    """Define variable in current environment
    behave like set! (not correct)
    """
    if is_variable(exp[1]):
        env[exp[1]] = evaluate(exp[2], env)
    else:
        env[exp[1][0]] = Lambda(exp[1][1:], exp[2:], env)

def eval_set(exp, env, eval_env):
    """Modify binding"""
    if exp[1] in env:
        env[exp[1]] = evaluate(exp[2], eval_env)
    else:
        eval_set(exp, env['**parent**'], eval_env)

def eval_application(exp, env):
    """Evaluate function application"""
    # Evaluate arguments
    args = [evaluate(arg, env) for arg in exp]
    # apply function (could be lambda or primitive)
    return args[0].apply(args[1:])

def eval_quote(exp):
    """Evaluate quotation
    and convert python list to nested pairs
    """
    return pylist_to_pairs(exp[1])

def eval_sequence(exp, env):
    """Evaluate sequence and return last result"""
    result = None
    for e in exp:
        result = evaluate(e, env)
    return result

# Expand derived structure

def let_to_lambda(exp):
    """Syntax transformation from let to lambda"""
    bindings = zip(*exp[1])
    paras = list(bindings[0])
    args = bindings[1]
    body = exp[2:]
    f = [['lambda', paras] + body]
    f.extend(args)
    return f

def evaluate(exp, env):
    """Evaluate parsed Scheme list in an environment"""
    # use while to prevent stack overflow
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


def make_base():
    """Make base Environment"""
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