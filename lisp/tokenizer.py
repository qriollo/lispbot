# coding:utf-8

T_EOF = -1
T_LPAREN = 1
T_RPAREN = 2
T_ID = 3
T_NUM = 4
T_QUOTE = 5
T_STRING = 6
T_DOT = 7
T_TRUE = 8
T_FALSE = 9

DIGIT = '0123456789'
LOWER = 'abcdefghijklmnopqrstuvwxyz'
UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SYMBOL = '!$%&/=?-_+*:|><'
IDENT = LOWER + UPPER + DIGIT + SYMBOL

def is_number(xs):
    if xs == '': return False
    if xs[0] == '-':
        b = xs[1:] != ''
        xs = xs[1:]
    else:
        b = True
    for x in xs:
        b = b and x in DIGIT
    return b

class Tokenizer(object):
    def __init__(self, string):
        self._s = string
        self._i = 0

    def next_token(self):
        # skip whitespace and comments
        while self._i < len(self._s) and self._s[self._i] in ' \t\r\n;':
            if self._s[self._i] == ';':
                while self._i < len(self._s) and self._s[self._i] != '\n':
                    self._i += 1
            else:
                self._i += 1
        if self._i >= len(self._s):
            return T_EOF, ''
        elif self._s[self._i] == '(':
            self._i += 1
            return T_LPAREN, '('
        elif self._s[self._i] == ')':
            self._i += 1
            return T_RPAREN, ')'
        elif self._s[self._i] == '.':
            self._i += 1
            return T_DOT, '.'
        elif self._s[self._i] == "'":
            self._i += 1
            return T_QUOTE, '\''
        elif self._s[self._i] == '#':
            self._i += 1
            if self._i < len(self._s) and self._s[self._i] == 't':
                self._i += 1
                return T_TRUE, '#t'
            elif self._i < len(self._s) and self._s[self._i] == 'f':
                self._i += 1
                return T_FALSE, '#f'
            else:
                raise Exception(u'Directiva para el reader desconocida: ' + \
                                self._s[self._i:])
        elif self._s[self._i] == '"':
            self._i += 1
            string = ''
            while self._i < len(self._s):
                if self._s[self._i] == '"':
                    self._i += 1
                    break
                if self._i == '\\' and self._i + 1 < len(self._s):
                    self._i += 1
                    if self._s[self._i] == '"':
                        string += '"'
                    elif self._s[self._i] == '\\':
                        string += '\\'
                    elif self._s[self._i] == '0':
                        string += '\0'
                    elif self._s[self._i] == 't':
                        string += '\t'
                    elif self._s[self._i] == 'r':
                        string += '\r'
                    elif self._s[self._i] == 'n':
                        string += '\n'
                    else:
                        string += self._s[self._i]
                    self._i += 1
                else:
                    string += self._s[self._i]
                    self._i += 1
            return T_STRING, string
        elif self._s[self._i] in IDENT:
            ident = ''
            while self._i < len(self._s) and self._s[self._i] in IDENT:
                ident += self._s[self._i]  
                self._i += 1
            if is_number(ident):
                return T_NUM, int(ident)
            else: 
                return T_ID, ident
        else:
            raise Exception(u'Símbolo desconocido: ' + self._s[self._i:])

