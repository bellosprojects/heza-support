NUMBER = "number"
TEXT = "text"
FUNCTION = "function"
SET = "set"
INFINITE = "infinite"
TUPLE = "tuple"
OBJECT = "object"
NULL = "null"
REFERENCE = "reference"
BOOLEAN = "boolean"
INDETERMINATE = "indeternimate"
EXPRESION = "expresion"
ERROR = "error"
UNKNOW = "any"

BINARY_OPERATIONS = [
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "pow",
    "and",
    "or",
    "then",
    "equal",
    "nEqual",
    "greater",
    "less",
    "greaterEqual",
    "lessEqual",
    "in",
    "notin",
    "del",
    "union",
    "inter",
    "symDiff",
    "cross"
]

UNARY_OPERATIONS = [
    "not",
    "pos",
    "neg",
    "fact",
    "sqrt"
]

TYPE_BINARY_MATRIX = {
    ('add', NUMBER, NUMBER): {NUMBER},
    ('sub', NUMBER, NUMBER): {NUMBER},
    ('mul', NUMBER, NUMBER): {NUMBER},
    ('div', NUMBER, NUMBER): {NUMBER},
    ('mod', NUMBER, NUMBER): {NUMBER},
    ('pow', NUMBER, NUMBER): {NUMBER},

    ('pow', NUMBER, INFINITE): {NUMBER, INDETERMINATE}
}

TYPE_UNARY_MATRIX = {
    ('not', NUMBER): {BOOLEAN},
    ('pos', NUMBER): {NUMBER},
    ('neg', NUMBER): {NUMBER},
    ('fact', NUMBER): {NUMBER},
    ('nosqrtt', NUMBER): {NUMBER},
}

from scope import Scope

def _get_single_type(node: dict) -> set[str]:

    if node['type'] == 'number':
        return {NUMBER}
    
    elif node['type'] == 'bool':
        return {BOOLEAN}
    
    elif node['type'] == 'expresion':
        return {EXPRESION}
    
    elif node['type'] == 'text':
        return {TEXT}
    
    elif node['type'] == 'null':
        return {NULL}
    
    elif node['type'] == 'indeterminate':
        return {INDETERMINATE}
    
    elif node['type'] == 'infinite':
        return {INFINITE}
    
    elif node['type'] == 'ARROBA':
        return {NUMBER}
    
    elif node['type'] == 'abs':
        return {UNKNOW}
    
    elif node['type'] == 'foreach':
        return {BOOLEAN}
    
    elif node['type'] == 'exist':
        return {BOOLEAN}
    
    elif node['type'] == 'definiteIntegral':
        return {EXPRESION}
    
    elif node['type'] == 'indefiniteIntegral':
        return {EXPRESION}
    
    elif node['type'] == 'derivative':
        return {EXPRESION}
    
    elif node['type'] == 'lim':
        return {EXPRESION}
    
    elif node['type'] == 'totalEval':
        return {EXPRESION}
    
    elif node['type'] == 'eval':
        return {EXPRESION}
    
    elif node['type'] == 'object_instantiation':
        return { node.get('object_name', 'Objecto Anonimo') }
    
    elif node['type'] == 'range':
        return { SET }
    
    elif node['type'] == 'set':
        return { SET }
    
    elif node['type'] == 'filter':
        return { SET }
    
    elif node['type'] == 'transformation':
        return { SET }
    
    elif node['type'] == 'tuple':
        return { TUPLE }
    
    return {UNKNOW}

TYPE_CACHE = {}

def inferences_type(node: dict, scope: Scope) -> set[str]:
    node_id = id(node)

    if node_id in TYPE_CACHE:
        if TYPE_CACHE[node_id] == "COMPUTING":
            return {UNKNOW}
        return TYPE_CACHE[node_id]

    result_types = set()

    if node['type'] == "binaryOperation" and node['operation'] in BINARY_OPERATIONS:

        left = inferences_type(node=node['leftValue'], scope=scope)
        right = inferences_type(node=node['rightValue'], scope=scope)

        for leftType in left:
            for rightType in right:

                if leftType == UNKNOW or right == UNKNOW:
                    result_types.add(UNKNOW)
                elif leftType == ERROR or right == ERROR:
                    result_types.add(ERROR)
                else:
                    key = (node['operation'], leftType, rightType)

                    result_types = result_types.union(TYPE_BINARY_MATRIX.get(key, {ERROR}))
    
    elif node['type'] == "unaryOperation" and node['operation'] in UNARY_OPERATIONS:

        values = inferences_type(node=node['value'], scope=scope)
        
        for value in values:

            if value == UNKNOW:
                result_types.add(UNKNOW)
            elif value == ERROR:
                result_types.add(ERROR)
            else:
                key = (node['operation'], value)
                result_types = result_types.union(TYPE_UNARY_MATRIX.get(key, {ERROR}))
    
    elif node['type'] == 'id':

        var_name = node['value']

        if var_name in scope.objetos:
            return {var_name}

        elif var_name in scope.funciones:
            return { FUNCTION }

        symbol = scope.buscar_simbolo(nombre=var_name)

        if not symbol or not symbol.get('value'):
            return {ERROR}
        
        TYPE_CACHE[node_id] = "COMPUTING"

        resolved_types = inferences_type(node=symbol['value'], scope=scope)
        
        TYPE_CACHE[node_id] = resolved_types

        return resolved_types

    else:
        
        result_types = _get_single_type(node=node)

    return result_types