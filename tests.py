import unittest
import pyscm

class TestParse(unittest.TestCase):

    def test_single_list(self):
        self.assertEqual([['+', '1', '2']],
            pyscm.parse('(+ 1 2)'))
        self.assertEqual([['number?', 'x']],
            pyscm.parse('(number? x)'))
        self.assertEqual([['lambda', ['x'], ['+', 'x', '3']]],
            pyscm.parse('(lambda (x) (+ x 3))'))
        self.assertEqual([['define', 'a', '5']],
            pyscm.parse('(define a 5)'))
        self.assertEqual([['if', 'a', '#f', '1', '3']],
            pyscm.parse('(if a #f 1 3)'))

    def test_nested_list(self):
        self.assertEqual([['+', ['*', 'a', 'b'], '4']],
            pyscm.parse('(+ (* a b) 4)'))
        self.assertEqual([['+', ['*', 'a', ['/', '12.3', '4.3']], '4']],
            pyscm.parse('(+ (* a (/ 12.3 4.3)) 4)'))

    def test_sequence(self):
        self.assertEqual([['+', '3', '4'], ['*', '1', '2']],
            pyscm.parse('(+ 3 4) (* 1 2)'))
        self.assertEqual([['+', '3', '4'], ['*', '1', '2']],
            pyscm.parse('(+ 3 4) \n\n(* 1 2)'))

    def test_sequence_and_nested(self):
        self.assertEqual([['+', ['a', '1', '2'], '4'], ['*', '1', '2']],
            pyscm.parse('(+ (a 1 2) 4) (* 1 2)'))

    def test_quote(self):
        self.assertEqual([['quote', ['1', '2']]], pyscm.parse("'(1 2)"))
        self.assertEqual([['quote', ['define', 'a', '1']]],
            pyscm.parse("'(define a 1)"))

    def test_data_type(self):
        self.assertEqual([['"hello"', '"world"', '#f', '#t', '1e4']],
            pyscm.parse('("hello" "world" #f #t 1e4)'))

    def test_function(self):
        code = """
        (define (tagged-list? exp tag)
            (if (pair? exp)
                (eq? (car exp) tag)
                false))"""
        ast = [['define', ['tagged-list?', 'exp', 'tag'],
            ['if', ['pair?', 'exp'],
            ['eq?', ['car', 'exp'], 'tag'],
            'false']]]
        self.assertEqual(ast, pyscm.parse(code))
        


if __name__ == '__main__':
    unittest.main()