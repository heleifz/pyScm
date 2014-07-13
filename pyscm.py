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
            # deal with quoting
            if not ast[-1] or ast[-1][-1] != "'":
                ast[-1].append(lst)
            else:
                ast[-1].pop()
                ast[-1].append(['quote', lst])
        else:
            ast[-1].append(p)
    ast = ast[0]
    return ast

# Predicators


def evaluate(lst, env):
    """Evaluate parsed Scheme list in an environment"""
    pass

