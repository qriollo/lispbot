# coding:utf-8:

SYMBOL_TABLE = {}

def intern_symbol(symbol_name):
    if symbol_name not in SYMBOL_TABLE:
        symbol = SexprSymbol(symbol_name)
        SYMBOL_TABLE[symbol_name] = symbol
    return SYMBOL_TABLE[symbol_name]

class SexprNumber(object):

    def __init__(self, num):
        self._num = num

    def __repr__(self):
        return '%i' % (self._num,)

    def num_value(self):
        return self._num

def num_value(value):
    if isinstance(value, SexprNumber):
        return value.num_value()
    else:
        raise Exception(u'Se esperaba un número')

class SexprString(object):

    def __init__(self, string):
        self._string = string

    def __repr__(self):
        res = ''
        res += '"'
        for c in self._string:
            if c == '\0':
                res += '\\0'
            elif c == '\n':
                res += '\\n'
            elif c == '\r':
                res += '\\r'
            elif c == '\t':
                res += '\\t'
            elif c == '"':
                res += '\\"'
            elif c == '\\':
                res += '\\\\'
            else:
                res += c
        res += '"'
        return res

    def string_value(self):
        return self._string

def string_value(value):
    if isinstance(value, SexprString):
        return value.string_value()
    else:
        raise Exception(u'Se esperaba una cadena.')

class SexprSymbol(object):

    def __init__(self, symbol_name):
        self._symbol_name = symbol_name

    def __repr__(self):
        return self._symbol_name

    def name(self):
        return self._symbol_name

def symbol_name(symbol):
    return symbol.name()

class SexprCons(object):

    def __init__(self, car, cdr):
        self._car = car
        self._cdr = cdr

    def car(self):
        return self._car

    def cdr(self):
        return self._cdr

    def set_car(self, value):
        self._car = value
        return value

    def set_cdr(self, value):
        self._cdr = value
        return value

    def __repr__(self):
        if car(self) == intern_symbol('quote') and \
           consp(cdr(self)) and is_null(cdr(cdr(self))):
            return "'" + repr(car(cdr(self)))
        res = ''
        res += '('
        lst = self
        sep = ''
        while isinstance(lst, SexprCons):
            res += sep + repr(lst._car)
            lst = lst._cdr
            sep = ' '
        if lst != SexprNil():
            res += ' . ' + repr(lst)
        res += ')'
        return res

def consp(expr):
    return isinstance(expr, SexprCons)

def is_null(expr):
    return expr == SexprNil()

def is_keyword(symbol):
    name = symbol_name(symbol)
    return name == '()' or name.startswith(':') or name.startswith('#')

def symbolp(expr):
    return isinstance(expr, SexprSymbol) and not is_keyword(expr)

def car(expr):
    if isinstance(expr, SexprCons):
        return expr.car()
    else:
        raise Exception('car aplicado a algo que no es una lista.')

def cdr(expr):
    if isinstance(expr, SexprCons):
        return expr.cdr()
    else:
        raise Exception('cdr aplicado a algo que no es una lista.')

def set_car(expr, value):
    if isinstance(expr, SexprCons):
        return expr.set_car(value)
    else:
        raise Exception('set_car aplicado a algo que no es una lista.')

def set_cdr(expr, value):
    if isinstance(expr, SexprCons):
        return expr.set_cdr(value)
    else:
        raise Exception('set_cdr aplicado a algo que no es una lista.')

def SexprNil():
    return intern_symbol('()')

def build_list(elements, tail):
    res = tail
    for i in range(len(elements)):
        res = SexprCons(elements[len(elements) - 1 - i], res)
    return res

def SexprList(elements):
    return build_list(elements, SexprNil())

def SexprTrue():
    return intern_symbol('#t')

def SexprFalse():
    return intern_symbol('#f')

def SexprBool(b):
    if b:
        return SexprTrue()
    else:
        return SexprFalse()

def bool_value(value):
    if value == SexprTrue():
        return True
    elif value == SexprFalse():
        return False
    else:
        raise Exception(u'Se esperaba un booleano')

class SexprProcedure(object):

    def __init__(self, environment, parameters, body):
        self._environment = environment
        self._parameters = parameters
        self._body = body
        self._name = None

    def __repr__(self):
        if self._name is None:
            return '#<procedure %s>' % (id(self),)
        else:
            return '#<procedure %s>' % (self._name,)

    def set_name(self, name):
        if self._name is None:
            self._name = name

    def environment(self):
        return self._environment

    def parameters(self):
        return self._parameters

    def body(self):
        return self._body

class SexprBuiltin(object):

    def __init__(self, name, function):
        self._name = name
        self._function = function

    def __repr__(self):
        return '#<builtin-procedure %s>' % (self._name,)

    def call(self, environment, arguments):
        lst = []
        while consp(arguments):
            lst.append(car(arguments))
            arguments = cdr(arguments)
        return self._function(environment, *lst)

def is_callable(function):
    return isinstance(function, SexprProcedure) or \
           isinstance(function, SexprBuiltin)

def is_number(x):
    return isinstance(x, SexprNumber)

