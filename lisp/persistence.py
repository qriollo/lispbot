
from lisp.parser import Parser
from lisp.sexpressions import (
            SexprNumber, SexprString, SexprSymbol,
            SexprProcedure, SexprBuiltin, consp, car, cdr,
            intern_symbol, symbol_name
       )

def read(string):
    return Parser(string).parse_expression()

def env_dump(environment):
    while consp(environment):
        last_rib = car(environment)
        environment = cdr(environment)
    assert isinstance(last_rib, dict)

    elements = []
    for key, value in last_rib.items():
        if isinstance(value, SexprProcedure):
            elements.append((symbol_name(key), 'p', (repr(value.parameters()), repr(value.body()))))
        elif isinstance(value, SexprBuiltin):
            pass
        else:
            elements.append((symbol_name(key), 'f', repr(value)))
    return elements

def env_load(environment, elements):
    while consp(environment):
        last_env = environment
        last_rib = car(environment)
        environment = cdr(environment)
    assert isinstance(last_rib, dict)

    for element in elements:
        if len(element) != 3:
            print('No se pudo cargar registro.')
            continue
        key, typ, value = element
        if typ == 'p':
            parameters = read(value[0])
            body = read(value[1])
            procedure = SexprProcedure(last_env, parameters, body)
            procedure.set_name(key)
            last_rib[intern_symbol(key)] = procedure
        elif typ == 'f':
            last_rib[intern_symbol(key)] = read(value)
        else:
            print('No se pudo cargar registro.')

