# coding:utf-8:

from lisp.sexpressions import (
        SexprNumber, SexprString, SexprCons, SexprNil, SexprSymbol,
        SexprTrue, SexprFalse, SexprProcedure, SexprBuiltin, SexprList,
        SexprBool, bool_value, num_value, string_value, is_keyword,
        intern_symbol, consp, symbolp, symbol_name, car, cdr, set_car, set_cdr,
        is_null, build_list, is_number,
     )

def generic_fold(py2lisp, lisp2py, op, z, lst):
    r = z
    for x in lst:
        r = op(r, lisp2py(x))
    return py2lisp(r)

def num_fold(op, z, lst):
    return generic_fold(SexprNumber, num_value, op, z, lst)

def bool_fold(op, z, lst):
    return generic_fold(SexprBool, bool_value, op, z, lst)

def string_fold(op, z, lst):
    return generic_fold(SexprString, string_value, op, z, lst)

def procedure_definition(environment, x):
    if isinstance(x, SexprProcedure):
        return SexprCons(intern_symbol('fun'),
                         SexprCons(x.parameters(),
                                   x.body()))
    elif isinstance(x, SexprSymbol):
        p = env_lookup(environment, x)
        if p is None or not isinstance(p, SexprProcedure):
            raise Exception(u'El símbolo no está ligado a un procedimiento.')
        return SexprCons(intern_symbol('def'),
                         SexprCons(SexprCons(x, p.parameters()),
                                   p.body()))
    else:
        raise Exception(u'Se esperaba un símbolo o booleano')

def global_environment():
    env = SexprCons({}, SexprNil())
    def db(name, function):
        env_define(env, intern_symbol(name), SexprBuiltin(name, function))
    db('+', lambda env, *args: num_fold(lambda x, y: x + y, 0, args))
    db('-', lambda env, a, b: SexprNumber(num_value(a) - num_value(b)))
    db('*', lambda env, *args: num_fold(lambda x, y: x * y, 1, args))
    db('/', lambda env, a, b: SexprNumber(num_value(a) / num_value(b)))
    db('%', lambda env, a, b: SexprNumber(num_value(a) % num_value(b)))
    db('and', lambda env, *args: bool_fold(lambda x, y: x and y, True, args))
    db('&&', lambda env, *args: bool_fold(lambda x, y: x and y, True, args))
    db('not', lambda env, x: SexprBool(not bool_value(x)))
    db('=', lambda env, x, y: SexprBool(is_number(x) and is_number(y) and num_value(x) == num_value(y)))
    db('or', lambda env, *args: bool_fold(lambda x, y: x or y, False, args))
    db('||', lambda env, *args: bool_fold(lambda x, y: x or y, False, args))
    db('>', lambda env, x, y: SexprBool(num_value(x) > num_value(y)))
    db('>=', lambda env, x, y: SexprBool(num_value(x) >= num_value(y)))
    db('<', lambda env, x, y: SexprBool(num_value(x) < num_value(y)))
    db('<=', lambda env, x, y: SexprBool(num_value(x) <= num_value(y)))
    db('str+', lambda env, *args: string_fold(lambda x, y: x + y, "", args))
    db('cons', lambda env, x, y: SexprCons(x, y))
    db('car', lambda env, x: car(x))
    db('cdr', lambda env, x: cdr(x))
    db('consp', lambda env, x: SexprBool(consp(x)))
    db('set-car', lambda env, x, y: set_car(x, y))
    db('set-cdr', lambda env, x, y: set_cdr(x, y))
    db('symbolp', lambda env, x: SexprBool(symbolp(x)))
    db('null', lambda env, x: SexprBool(is_null(x)))
    db('eq', lambda env, x, y: SexprBool(x == y))
    db('list', lambda env, *args: SexprList(args))
    db('apply', lambda env, f, *args: fun_apply(f, args, env))
    db('procedure-definition', procedure_definition)
    db('string->int', lambda env, x: SexprNumber(int(string_value(x))))
    return env

def rib_keys(rib):
    if isinstance(rib, dict):
        return rib.keys()
    else:
        d = {}
        while consp(rib):
            association = car(rib)
            d[car(association)] = 1
            rib = cdr(rib)
        return d.keys()

def rib_lookup(rib, symbol):
    if isinstance(rib, dict):
        return rib.get(symbol, None)
    else:
        while consp(rib):
            association = car(rib)
            if car(association) == symbol:
                return cdr(association)
            rib = cdr(rib)
        return None

def rib_define(rib, symbol, value):
    if isinstance(rib, dict):
        rib[symbol] = value
        return rib
    else:
        return SexprCons(SexprCons(symbol, value), rib)

def rib_set(rib, symbol, value):
    if isinstance(rib, dict):
        rib[symbol] = value
    else:
        while consp(rib):
            association = car(rib)
            if car(association) == symbol:
                set_cdr(association, value)
                break

def env_keys(environment):
    d = {}
    while consp(environment):
        rib = car(environment)
        for k in rib_keys(rib):
            d[k] = 1
        environment = cdr(environment)
    return d.keys()

def env_lookup(environment, symbol):
    if is_keyword(symbol):
        return symbol
    while consp(environment):
        rib = car(environment)
        result = rib_lookup(rib, symbol)
        if result is not None:
            return result
        environment = cdr(environment)
    raise Exception('Variable no definida: ' + symbol_name(symbol))

def env_define(environment, symbol, value):
    if is_keyword(symbol):
        raise Exception('No se puede definir una keyword.')

    if isinstance(value, SexprProcedure):
        value.set_name(symbol_name(symbol))

    rib = car(environment)
    result = rib_lookup(rib, symbol)
    if result is not None:
        #raise Exception('Variable ya definida: ' + symbol_name(symbol))
        rib_set(rib, symbol, value)
    else:
        set_car(environment, rib_define(car(environment), symbol, value))

def env_set(environment, symbol, value):
    if is_keyword(symbol):
        raise Exception('No se puede definir una keyword.')
    while consp(environment):
        rib = car(environment)
        if rib_lookup(rib, symbol) is not None:
            rib_set(rib, symbol, value)
            return
        environment = cdr(environment)
    raise Exception('Variable no definida: ' + symbol_name(symbol))

def env_bind(environment, parameters, arguments):
    environment = SexprCons(SexprNil(), environment)
    while consp(parameters):
        if not consp(arguments):
            raise Exception(u'Faltan parámetros')
        env_define(environment, car(parameters), car(arguments))
        parameters = cdr(parameters)
        arguments = cdr(arguments)
    if parameters == SexprNil():
        if arguments != SexprNil():
            raise Exception(u'Sobran parámetros')
    elif isinstance(parameters, SexprSymbol):
        env_define(environment, parameters, arguments)
    else:
        raise Exception(u'Lista de parámetros deforme')
    return environment

def first(expr):
    return car(expr)

def second(expr):
    return car(cdr(expr))

def third(expr):
    return car(cdr(cdr(expr)))

def fourth(expr):
    return car(cdr(cdr(cdr(expr))))

def eval_expression(expr, environment):
    if isinstance(expr, SexprNumber):
        return expr
    elif isinstance(expr, SexprString):
        return expr
    elif isinstance(expr, SexprSymbol):
        return env_lookup(environment, expr)
    elif isinstance(expr, SexprCons):
        head = first(expr)
        if head == intern_symbol('quote'):
            return second(expr)
        elif head == intern_symbol('do'):
            return eval_block(cdr(expr), environment)
        elif head == intern_symbol('def'):
            if consp(second(expr)):
                expr2 = SexprList([
                            intern_symbol('def'),
                            car(second(expr)),
                            SexprCons(
                                intern_symbol('fun'),
                                SexprCons(
                                    cdr(second(expr)),
                                    cdr(cdr(expr))
                                )
                            )
                        ])
                return eval_expression(expr2, environment)
            else:
                value = eval_expression(third(expr), environment)
                env_define(environment, second(expr), value)
                return value
        elif head == intern_symbol('let'):
            local_environment = SexprCons(SexprNil(), environment)
            decls = second(expr)
            body = cdr(cdr(expr))
            while consp(decls):
                variable = first(decls)
                value = eval_expression(second(decls), environment)
                env_define(local_environment, variable, value)
                decls = cdr(cdr(decls))
            return eval_block(cdr(cdr(expr)), local_environment)
        elif head == intern_symbol('let*'):
            local_environment = SexprCons(SexprNil(), environment)
            decls = second(expr)
            body = cdr(cdr(expr))
            while consp(decls):
                variable = first(decls)
                value = eval_expression(second(decls), local_environment)
                env_define(local_environment, variable, value)
                decls = cdr(cdr(decls))
            return eval_block(cdr(cdr(expr)), local_environment)
        elif head == intern_symbol('set'):
            value = eval_expression(third(expr), environment)
            env_set(environment, second(expr), value)
            return value
        elif head == intern_symbol('if'):
            rest = cdr(expr)
            while consp(rest):
                if consp(cdr(rest)):
                    cond = eval_expression(first(rest), environment)
                    if cond != SexprFalse():
                        return eval_expression(second(rest), environment)
                    rest = cdr(cdr(rest))
                else:
                    return eval_expression(car(rest), environment)
            return SexprNil()
        elif head == intern_symbol('fun'):
            return SexprProcedure(environment, second(expr), cdr(cdr(expr)))
        else:
            function = eval_expression(head, environment)
            arguments = eval_list(cdr(expr), environment)
            return eval_application(function, arguments, environment)
    else:
        raise Exception(u'Expresión no reconocida: ' + repr(expr))

def eval_block(block, environment):
    res = SexprNil()
    while consp(block):
        res = eval_expression(car(block), environment)
        block = cdr(block)
    return res

def eval_list(expr, environment):
    res = []
    while consp(expr):
        res.append(eval_expression(car(expr), environment))
        expr = cdr(expr)
    return SexprList(res)

def eval_application(function, arguments, environment):
    if isinstance(function, SexprProcedure):
        closure_environment = function.environment()
        local_environment = env_bind(closure_environment,
                                     function.parameters(),
                                     arguments)
        return eval_block(function.body(), local_environment)
    elif isinstance(function, SexprBuiltin):
        return function.call(environment, arguments)
    else:
        raise Exception(u'El valor no es aplicable.')

def fun_apply(function, arguments, environment):
    if len(arguments) == 0:
        return eval_application(function, SexprNil(), environment)
    xs = []
    for x in arguments[:-1]:
        xs.append(x)
    rest = arguments[-1]
    return eval_application(function, build_list(xs, rest), environment)

