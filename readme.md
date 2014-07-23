# PyScm

## A Scheme Interpreter

PyScm is my toy project which implement a subset of Scheme programming language in Python. PyScm has the same structure of meta-circular interpreter in SICP.

```python
import pyscm
code = """
(define (sum lst)
    (if (eq? lst '())
        0
        (+ (car lst) (sum (cdr lst)))))
(define (map f lst)
    (if (eq? lst '())
        '()
        (cons (f (car lst)) (map f (cdr lst)))))
(sum (map car '((1 2 3) (4 5 6))))
"""
ast = pyscm.parse(code)
print pyscm.evaluate(ast, pyscm.make_base())
```

## Todo

1. Implement Scheme to C transformation