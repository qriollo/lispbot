# coding:utf-8:

from lisp.tokenizer import (
        T_EOF, T_LPAREN, T_RPAREN, T_ID, T_NUM, T_QUOTE, T_STRING, T_DOT,
        T_TRUE, T_FALSE,
        Tokenizer
     )
from lisp.sexpressions import (
        SexprNumber, SexprString, SexprCons, SexprNil, SexprTrue, SexprFalse,
        intern_symbol, build_list,
     )

class Parser(object):

    def __init__(self, string):
        self._tokenizer = Tokenizer(string)
        self._current_token = None

    def _next_token(self):
        self._current_token = self._tokenizer.next_token()

    def _peek_token(self):
        if self._current_token is None:
            self._next_token()
        return self._current_token

    def parse_expression(self):
        if self._peek_token()[0] in [T_EOF, T_RPAREN]:
            raise Exception(u'Programa inválido: fin de archivo prematuro.')
        elif self._peek_token()[0] == T_LPAREN:
            self._next_token()
            lst = self.parse_list()
            if self._peek_token()[0] != T_RPAREN:
                raise Exception(u'Programa inválido: esperaba un ).')
            self._next_token()
            return lst
        elif self._peek_token()[0] == T_QUOTE:
            nlevels = 0
            while self._peek_token()[0] == T_QUOTE:
                self._next_token()
                nlevels += 1
            expr = self.parse_expression()
            return SexprCons(intern_symbol('quote'),
                             SexprCons(expr, SexprNil()))
        elif self._peek_token()[0] == T_NUM:
            num = self._peek_token()[1]
            self._next_token()
            return SexprNumber(num)
        elif self._peek_token()[0] == T_ID:
            ident = self._peek_token()[1]
            self._next_token()
            return intern_symbol(ident)
        elif self._peek_token()[0] == T_TRUE:
            self._next_token()
            return SexprTrue()
        elif self._peek_token()[0] == T_FALSE:
            self._next_token()
            return SexprFalse()
        elif self._peek_token()[0] == T_STRING:
            string = self._peek_token()[1]
            self._next_token()
            return SexprString(string)
        else:
            raise Exception(u'Programa inválido: token inesperado' + \
                            str(self._peek_token()))

    def parse_list(self):
        lst = []
        while True:
            if self._peek_token()[0] in [T_EOF, T_RPAREN]:
                return build_list(lst, SexprNil())
            elif self._peek_token()[0] == T_DOT:
                self._next_token()
                expr = self.parse_expression()
                return build_list(lst, expr)
            else:
                lst.append(self.parse_expression())
        return lst

