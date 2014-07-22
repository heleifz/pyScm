import unittest
import pyscm

class TestParse(unittest.TestCase):

    def test_single_list(self):
        self.assertEqual(['begin', ['+', '1', '2']],
            pyscm.parse('(+ 1 2)'))
        self.assertEqual(['begin', ['number?', 'x']],
            pyscm.parse('(number? x)'))
        self.assertEqual(['begin', ['lambda', ['x'], ['+', 'x', '3']]],
            pyscm.parse('(lambda (x) (+ x 3))'))
        self.assertEqual(['begin', ['define', 'a', '5']],
            pyscm.parse('(define a 5)'))
        self.assertEqual(['begin', ['if', 'a', '#f', '1', '3']],
            pyscm.parse('(if a #f 1 3)'))

    def test_nested_list(self):
        self.assertEqual(['begin', ['+', ['*', 'a', 'b'], '4']],
            pyscm.parse('(+ (* a b) 4)'))
        self.assertEqual(['begin', ['+', ['*', 'a', ['/', '12.3', '4.3']], '4']],
            pyscm.parse('(+ (* a (/ 12.3 4.3)) 4)'))

    def test_sequence(self):
        self.assertEqual(['begin', ['+', '3', '4'], ['*', '1', '2']],
            pyscm.parse('(+ 3 4) (* 1 2)'))
        self.assertEqual(['begin', ['+', '3', '4'], ['*', '1', '2']],
            pyscm.parse('(+ 3 4) \n\n(* 1 2)'))

    def test_sequence_and_nested(self):
        self.assertEqual(['begin', ['+', ['a', '1', '2'], '4'], ['*', '1', '2']],
            pyscm.parse('(+ (a 1 2) 4) (* 1 2)'))

    def test_quote(self):
        self.assertEqual(['begin', ['quote', ['1', '2']]], pyscm.parse("'(1 2)"))
        self.assertEqual(['begin', ['quote', ['define', 'a', '1']]],
            pyscm.parse("'(define a 1)"))
        self.assertEqual(['begin', ['quote', 'a']], pyscm.parse("'a"))

    def test_data_type(self):
        self.assertEqual(['begin', ['"hello"', '"world"', '#f', '#t', '1e4']],
            pyscm.parse('("hello" "world" #f #t 1e4)'))

    def test_function(self):
        code = """
        (define (tagged-list? exp tag)
            (if (pair? exp)
                (eq? (car exp) tag)
                false))"""
        ast = ['begin', ['define', ['tagged-list?', 'exp', 'tag'],
            ['if', ['pair?', 'exp'],
            ['eq?', ['car', 'exp'], 'tag'],
            'false']]]
        self.assertEqual(ast, pyscm.parse(code))

class TestPredicators(unittest.TestCase):

    def test_is_primitive(self):
        self.assertTrue(pyscm.is_primitive('12'))
        self.assertTrue(pyscm.is_primitive('12.2'))
        self.assertTrue(pyscm.is_primitive('1.2e20'))
        self.assertTrue(pyscm.is_primitive('"hello world"'))
        self.assertFalse(pyscm.is_primitive(['define', 'a', '3']))
        self.assertFalse(pyscm.is_primitive('"illgal string'))

    def test_is_variable(self):
        self.assertTrue(pyscm.is_variable('a'))
        self.assertTrue(pyscm.is_variable('name_name'))
        self.assertFalse(pyscm.is_variable('33'))
        self.assertFalse(pyscm.is_variable('"foobar"'))
        self.assertFalse(pyscm.is_variable(['+', '1', '2']))

    def test_is_lambda(self):
        self.assertTrue(pyscm.is_lambda(['lambda',
            ['x'], ['+', '1', '2']]))
        self.assertTrue(pyscm.is_lambda(['lambda', ['x', 'y'],
            ['+', 'x', 'y']]))
        self.assertFalse(pyscm.is_lambda(['define', 'x', '1']))
        self.assertFalse(pyscm.is_lambda("var"))

    def test_is_definition(self):
        self.assertTrue(pyscm.is_definition(['define', 'x', '1']))
        self.assertTrue(pyscm.is_definition(['define', ['x','y'],
            ['+', 'x', 'y']]))

    def test_is_sequence(self):
        self.assertTrue(pyscm.is_sequence(['begin']))
        self.assertTrue(pyscm.is_sequence(['begin', [], []]))
        self.assertFalse(pyscm.is_sequence(['foo', [], []]))

class TestLambda(unittest.TestCase):

    def test_getter(self):
        l = pyscm.Lambda(['a', 'b', 'c'], ['+', 'a', 'b'], {})
        self.assertEqual(['a', 'b', 'c'], l.get_paras())
        self.assertEqual(['+', 'a', 'b'], l.get_body())
        self.assertEqual({}, l.get_parent_env())

    def test_make(self):
        l = pyscm.Lambda.make(['lambda', ['a', 'b', 'c'], ['+', 'a', 'b']], {})
        self.assertEqual(['a', 'b', 'c'], l.get_paras())
        self.assertEqual([['+', 'a', 'b']], l.get_body())
        self.assertEqual({}, l.get_parent_env())

class TestSymbol(unittest.TestCase):

    def test_str(self):
        s = pyscm.Symbol('hello')
        self.assertEqual('hello', str(s))

    def test_unique(self):
        s1 = pyscm.Symbol.make('foo')
        s2 = pyscm.Symbol.make('foo')
        s3 = pyscm.Symbol.make('bar')
        self.assertTrue(s1 is s2)
        self.assertFalse(s1 is s3)
        self.assertFalse(s2 is s3)

class TestBoolean(unittest.TestCase):

    def test_str(self):
        s = pyscm.Boolean(True)
        self.assertEqual('#t', str(s))
        s = pyscm.Boolean(False)
        self.assertEqual('#f', str(s))

    def test_unique(self):
        s1 = pyscm.Boolean.make(True)
        s2 = pyscm.Boolean.make(2 > 1)
        s3 = pyscm.Boolean.make(False)
        s4 = pyscm.Boolean.make(len('hello') == 1)
        self.assertTrue(s1 is s2)
        self.assertTrue(s3 is s4)
        self.assertFalse(s1 is s3)
        self.assertFalse(s2 is s4)

class TestPrimitiveFunction(unittest.TestCase):

    def test_arithmetic(self):
        self.assertEqual(4, pyscm.add([1, 2, 1]))
        self.assertEqual(0, pyscm.add([]))
        self.assertEqual(3, pyscm.add([1, 2]))
        self.assertEqual(1, pyscm.sub([2, 1]))
        self.assertEqual(-1, pyscm.sub([2, 1, 2]))
        self.assertEqual(0, pyscm.sub([0]))
        self.assertEqual(0, pyscm.mul([0, 1]))
        self.assertEqual(27, pyscm.mul([3, 3, 3]))
        self.assertEqual(2, pyscm.div([4, 2]))
        self.assertEqual(1, pyscm.div([4, 2, 2]))

    def test_compare(self):
        t = pyscm.Boolean.make(True)
        f = pyscm.Boolean.make(False)
        self.assertTrue(t is pyscm.lt([2, 4]))
        self.assertTrue(f is pyscm.lt([4, 2]))
        self.assertTrue(t is pyscm.le([2, 4]))
        self.assertTrue(t is pyscm.le([2, 2]))
        self.assertTrue(t is pyscm.ge([2, 2]))
        self.assertTrue(t is pyscm.ge([4, 2]))
        self.assertTrue(f is pyscm.ge([2, 4]))
        self.assertTrue(t is pyscm.gt([3, 1]))

    def test_equal(self):
        t = pyscm.Boolean.make(True)
        f = pyscm.Boolean.make(False)
        self.assertTrue(t is pyscm.eq([2, 2]))
        self.assertTrue(t is pyscm.eq_question_mark([2, 2]))
        self.assertTrue(f is pyscm.eq_question_mark([2, 2.0]))
        self.assertTrue(t is pyscm.eq([2, 2.0]))
        self.assertTrue(t is pyscm.eq_question_mark([t,\
            pyscm.Boolean.make(True)]))
        self.assertTrue(t is pyscm.eq_question_mark([
                pyscm.Symbol.make('foo'),
                pyscm.Symbol.make('foo')
            ]))

        self.assertTrue(t is pyscm.eq_question_mark([
                pyscm.evaluate(['quote', []], {}),
                pyscm.evaluate(['quote', []], {})
            ]))

class TestSugar(unittest.TestCase):

    def test_let_to_lambda(self):
        ast = pyscm.parse('(let ((x 3) (y 4)) (+ x y))')[1]
        self.assertEqual(
            [['lambda', ['x', 'y'], ['+', 'x', 'y']], '3', '4'],
            pyscm.let_to_lambda(ast)
        )

class TestEvaludator(unittest.TestCase):

    def test_primitive(self):
        self.assertEqual(3, pyscm.eval_primitive('3'))
        self.assertEqual(12.3, pyscm.eval_primitive('1.23e1'))
        self.assertEqual("hello", pyscm.eval_primitive('"hello"'))

    def test_variable(self):
        self.assertEqual(3, pyscm.eval_variable('a', {'a':3}))
        self.assertEqual(3, pyscm.eval_variable('a', {'**parent**':{'a':3}}))
        self.assertRaises(Exception, pyscm.eval_variable, 'a', {})

    def test_lambda(self):
        l = pyscm.evaluate(['lambda', ['a', 'b', 'c'], ['+', 'a', 'b']], {})
        self.assertTrue(isinstance(l, pyscm.Lambda))
        self.assertEqual(['a', 'b', 'c'], l.get_paras())
        self.assertEqual([['+', 'a', 'b']], l.get_body())
        self.assertEqual({}, l.get_parent_env())

    def test_definition(self):
        env = {}
        pyscm.evaluate(['define', 'a', '3'], env)
        pyscm.evaluate(['define', 'foo', '"bar"'], env)
        pyscm.evaluate(['define', ['func', 'p1', 'p2'],
           ['+', 'p1', 'p2']], env)
        self.assertEqual(3, env['a'])
        self.assertEqual("bar", env['foo'])
        l = env['func']
        self.assertTrue(isinstance(l, pyscm.Lambda))
        self.assertEqual(['p1', 'p2'], l.get_paras())
        self.assertEqual([['+', 'p1', 'p2']], l.get_body())
        self.assertEqual(env, l.get_parent_env())

    def test_set(self):
        env = {}
        pyscm.evaluate(['define', 'a', '3'], env)
        self.assertEqual(3, env['a'])
        pyscm.evaluate(['set!', 'a', '4'], env)
        self.assertEqual(4, env['a'])
        env = {}
        pyscm.evaluate(['define', 'a', '3'], env)
        pyscm.evaluate(['define', ['f', 'x'], ['set!', 'a', 'x']], env)
        pyscm.evaluate(['f', '9'], env)
        self.assertEqual(9, env['a'])

    def test_sequence(self):
        env = {}
        pyscm.evaluate(['begin', ['define', 'a', '3'],
                                 ['define', 'foo', '"bar"'],
                                 ['define', ['func', 'p1', 'p2'],
                                    ['+', 'p1', 'p2']]], env)
        self.assertEqual(3, env['a'])
        self.assertEqual("bar", env['foo'])
        l = env['func']
        self.assertTrue(isinstance(l, pyscm.Lambda))
        self.assertEqual(['p1', 'p2'], l.get_paras())
        self.assertEqual([['+', 'p1', 'p2']], l.get_body())
        self.assertEqual(env, l.get_parent_env())

    def test_if(self):
        t = pyscm.Boolean.make(True) 
        f = pyscm.Boolean.make(False) 
        ast = pyscm.parse('(if (> 2 1) 9 10)')[1]
        self.assertEqual(9, pyscm.evaluate(ast, pyscm.make_base()))
        ast = pyscm.parse('(if (> 1 2) 9 10)')[1]
        self.assertEqual(10, pyscm.evaluate(ast, pyscm.make_base()))
        ast = pyscm.parse('(if (> 2 3) 10)')[1]
        self.assertEqual(None, pyscm.evaluate(ast, pyscm.make_base()))
        ast = pyscm.parse('(if (< 2 3) 10)')[1]
        self.assertEqual(10, pyscm.evaluate(ast, pyscm.make_base()))

    def test_cond(self):
        t = pyscm.Boolean.make(True) 
        f = pyscm.Boolean.make(False) 
        code = """
        (define (f x)
            (cond
                ((< x 3) 1)
                ((< x 5) 44)
                (else 99)
                )) 
        (define a (f 2))
        (define b (f 4))
        (define c (f 33))
        """
        ast = pyscm.parse(code)
        base = pyscm.make_base()
        pyscm.evaluate(ast, base)
        self.assertEqual(1, base['a'])
        self.assertEqual(44, base['b'])
        self.assertEqual(99, base['c'])

    def test_apply(self):
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
        self.assertEqual(5, pyscm.evaluate(ast, pyscm.make_base()))
        code = """
        ((lambda (x y) (+ x y)) 1 9)
        """
        ast = pyscm.parse(code)
        self.assertEqual(10, pyscm.evaluate(ast, pyscm.make_base()))
        code = """
        (define (func x y)
            (let ((z 3) (w 7))
                (+ x w y z)))
        (func 9 9)
        """
        ast = pyscm.parse(code)
        self.assertEqual(28, pyscm.evaluate(ast, pyscm.make_base()))


if __name__ == '__main__':
    unittest.main()