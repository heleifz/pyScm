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

    def test_apply(self):
        code = """
        (define accu '(1 2 3))
        (define x (cons 1 accu))
        (display (+ (car (cdr x)) 3))
        """
        ast = pyscm.parse(code)
        pyscm.evaluate(ast, pyscm.make_base())


if __name__ == '__main__':
    unittest.main()