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

AVAILABLE_TYPES = [
    NUMBER,
    TEXT,
    FUNCTION,
    SET,
    INFINITE,
    TUPLE,
    NULL,
    REFERENCE,
    BOOLEAN,
    INDETERMINATE,
    EXPRESION
]

BINARY_OPERATIONS = [
    "add", "sub", "mul", "div", "mod", "pow", "and", "or", "then", 
    "equal", "nEqual", "greater", "less", "greaterEqual", "lessEqual", 
    "in", "notin", "del", "union", "inter", "symDiff", "cross"
]

UNARY_OPERATIONS = ["not", "pos", "neg", "fact", "sqrt"]

TYPE_BINARY_MATRIX = {
    ('add', NUMBER, NUMBER): {NUMBER},
    ('sub', NUMBER, NUMBER): {NUMBER},
    ('mul', NUMBER, NUMBER): {NUMBER},
    ('div', NUMBER, NUMBER): {NUMBER},
    ('mod', NUMBER, NUMBER): {NUMBER},
    ('pow', NUMBER, NUMBER): {NUMBER},
    ('and', NUMBER, NUMBER): {BOOLEAN},
    ('or', NUMBER, NUMBER): {BOOLEAN},
    ('then', NUMBER, NUMBER): {BOOLEAN},
    ('equal', NUMBER, NUMBER): {BOOLEAN},
    ('nEqual', NUMBER, NUMBER): {BOOLEAN},
    ('greater', NUMBER, NUMBER): {BOOLEAN},
    ('less', NUMBER, NUMBER): {BOOLEAN},
    ('greaterEqual', NUMBER, NUMBER): {BOOLEAN},
    ('lessEqual', NUMBER, NUMBER): {BOOLEAN},

    ('union', SET, SET): {SET},
    ('inter', SET, SET): {SET},
    ('symDiff', SET, SET): {SET},
    ('cross', SET, SET): {SET},

    ('in', SET, SET): {BOOLEAN},
    ('in', NUMBER, SET): {BOOLEAN},
    ('in', TEXT, SET): {BOOLEAN},
    ('in', REFERENCE, SET): {BOOLEAN},
    ('in', FUNCTION, SET): {BOOLEAN},
    ('in', BOOLEAN, SET): {BOOLEAN},
    ('in', TUPLE, SET): {BOOLEAN},
    ('in', INFINITE, SET): {BOOLEAN},
    ('in', INDETERMINATE, SET): {BOOLEAN},
    ('in', NULL, SET): {BOOLEAN},
    ('in', EXPRESION, SET): {BOOLEAN},
    ('in', OBJECT, SET): {BOOLEAN},
    ('in', UNKNOW, SET): {BOOLEAN},

    ('notin', SET, SET): {BOOLEAN},
    ('notin', NUMBER, SET): {BOOLEAN},
    ('notin', TEXT, SET): {BOOLEAN},
    ('notin', REFERENCE, SET): {BOOLEAN},
    ('notin', FUNCTION, SET): {BOOLEAN},
    ('notin', BOOLEAN, SET): {BOOLEAN},
    ('notin', TUPLE, SET): {BOOLEAN},
    ('notin', INFINITE, SET): {BOOLEAN},
    ('notin', INDETERMINATE, SET): {BOOLEAN},
    ('notin', NULL, SET): {BOOLEAN},
    ('notin', EXPRESION, SET): {BOOLEAN},
    ('notin', OBJECT, SET): {BOOLEAN},

    ('del', SET, SET): {BOOLEAN},
    ('del', SET, NUMBER): {BOOLEAN},
    ('del', SET, TEXT): {BOOLEAN},
    ('del', SET, REFERENCE): {BOOLEAN},
    ('del', SET, FUNCTION): {BOOLEAN},
    ('del', SET, BOOLEAN): {BOOLEAN},
    ('del', SET, TUPLE): {BOOLEAN},
    ('del', SET, INFINITE): {BOOLEAN},
    ('del', SET, INDETERMINATE): {BOOLEAN},
    ('del', SET, NULL): {BOOLEAN},
    ('del', SET, EXPRESION): {BOOLEAN},
    ('del', SET, OBJECT): {BOOLEAN},

    ('add', TEXT, TEXT): {TEXT},
    ('add', TEXT, NUMBER): {TEXT},
    ('add', NUMBER, TEXT): {TEXT},
    ('mul', TEXT, NUMBER): {TEXT},

    ('add', EXPRESION, NUMBER): {EXPRESION},
    ('add', EXPRESION, TEXT): {EXPRESION},
    ('add', EXPRESION, INFINITE): {EXPRESION},
    ('add', NUMBER, EXPRESION): {EXPRESION},
    ('add', TEXT, EXPRESION): {EXPRESION},
    ('add', INFINITE, EXPRESION): {EXPRESION},

    ('and', BOOLEAN, BOOLEAN): {BOOLEAN},
    ('or', BOOLEAN, BOOLEAN): {BOOLEAN},
    ('then', BOOLEAN, BOOLEAN): {BOOLEAN},
    ('equal', BOOLEAN, BOOLEAN): {BOOLEAN},
    ('nEqual', BOOLEAN, BOOLEAN): {BOOLEAN},

    ('pow', NUMBER, INFINITE): {NUMBER, INDETERMINATE}
}

TYPE_UNARY_MATRIX = {
    ('not', NUMBER): {BOOLEAN},
    ('pos', NUMBER): {NUMBER},
    ('neg', NUMBER): {NUMBER},
    ('fact', NUMBER): {NUMBER},
    ('sqrt', NUMBER): {NUMBER},
}

from scope import Scope

def _get_single_type(node: dict) -> set[str]:
    if not node or 'type' not in node:
        return {UNKNOW}
    
    t = node['type']
    if t == 'number': return {NUMBER}
    elif t == 'bool': return {BOOLEAN}
    elif t == 'expresion': return {EXPRESION}
    elif t == 'text': return {TEXT}
    elif t == 'null': return {NULL}
    elif t == 'indeterminate': return {INDETERMINATE}
    elif t == 'infinite': return {INFINITE}
    elif t == 'ARROBA': return {NUMBER}
    elif t == 'abs': return {NUMBER}
    elif t == 'foreach': return {BOOLEAN}
    elif t == 'exist': return {BOOLEAN}
    elif t == 'definiteIntegral': return {EXPRESION}
    elif t == 'indefiniteIntegral': return {EXPRESION}
    elif t == 'derivative': return {EXPRESION}
    elif t == 'lim': return {EXPRESION}
    elif t == 'totalEval': return {EXPRESION}
    elif t == 'eval': return {EXPRESION}
    elif t == 'object_instantiation': return { f"object[{node.get('object_name', 'Objecto Anonimo')}]" }
    elif t in ['range', 'set', 'filter', 'transformation']: return { SET }
    elif t == 'tuple': return { TUPLE }
    
    return {UNKNOW}

def _get_access_type(node: dict, scope: Scope) -> set[str]:
    result_types = set()
    set_type = node.get('type')

    if set_type == 'id':
        simbolo = scope.buscar_simbolo(nombre=node['value'])
        if not simbolo or 'value' not in simbolo:
            return {ERROR}
        
        var_node = simbolo['value']

        if not isinstance(var_node, dict) or 'type' not in var_node:
            return {UNKNOW}
            
        var_node_type = inferences_type(node=var_node, scope=scope)

        if any([val_type not in (SET, TUPLE) for val_type in var_node_type]):
            return {ERROR}
        
        if var_node['type'] == 'set':
            values = [inferences_type(value, scope=scope) for value in var_node.get('value', [])]
            for v in values:
                result_types = result_types.union(v)
        elif var_node['type'] == 'filter':
            return _get_access_type(node=var_node.get('set', {}), scope=scope)
        elif var_node['type'] == 'transformation':
            return inferences_type(node=var_node.get('expresion', {}), scope=scope)
    else:
        result_types.add(UNKNOW)

    return result_types

def _get_math_function_returns(math_funcion: dict, scope: Scope) -> set[str]:

    if not math_funcion or not math_funcion.get('expresions'):
        return {UNKNOW}

    exprs = math_funcion.get('expresions', [])

    result_types = set()

    for expr in exprs:

        result_node = expr.get('expresion')

        result_type = inferences_type(node=result_node, scope=scope)

        result_types = result_types.union(result_type)

    return result_types

def _get_all_returns_type(body: list[dict], scope: Scope) -> set[str]:
    result_types = set()

    if body:

        for inst in body:
            if not isinstance(inst, dict):
                continue
                
            if inst.get('type') == 'return':
                values = inst.get('values', [])
                types = [inferences_type(node=value, scope=scope) for value in values]
                for t in types:
                    result_types = result_types.union(t)
            elif 'body' in inst:
                result_types = result_types.union(_get_all_returns_type(body=inst['body'], scope=scope))
            elif inst.get('type') == 'conditional':
                for branch in inst.get('branches', []): 
                    result_types = result_types.union(_get_all_returns_type(body=branch.get('body', []), scope=scope))
                if 'else_body' in inst:
                    result_types = result_types.union(_get_all_returns_type(body=inst['else_body'], scope=scope))

    return result_types

def _get_call_type(node: dict, scope: Scope) -> set[str]:
    node_type = node.get('type')

    if node_type == 'id':
        var_name = node['value']
        var_node = scope.buscar_simbolo(nombre=var_name)

        if not var_node or not var_node.get('type'):
            return {ERROR}
        
        if var_node['type'] != 'function':
            return {UNKNOW}
        
        func_node = var_node['value']

        if func_node.get('type') == 'function':
            return _get_math_function_returns(math_funcion=func_node, scope=scope)

        body = func_node.get('body', [])

        root_scope = scope.obtener_root()
        func_scope = root_scope.buscar_scope(row=func_node.get('fila', 1), col=func_node.get('columna', 1))
        
        if not func_scope:
            func_scope = scope

        return _get_all_returns_type(body=body, scope=func_scope)

    else:
        return {UNKNOW}
        
import re
    
def _get_attribute_access_type(node: dict, scope: Scope) -> set[str]:
    if not node or not isinstance(node, dict) or "object" not in node:
        return { UNKNOW }

    object_node = node['object']
    object_type = inferences_type(node=object_node, scope=scope)

    for t in object_type:
        match = re.search(r'^object\[([a-zA-Z_]\w*)\]$', t)
        if match:
            object_name = match.group(1)

            # Usamos el nuevo método de búsqueda profunda
            obj_decl_node = scope.buscar_objeto_definicion(object_name)

            if obj_decl_node and isinstance(obj_decl_node, dict):
                attribute_name = node.get('attribute')
                atributos = obj_decl_node.get('attributes', {})

                if attribute_name not in atributos.keys():
                    return { ERROR }

                for attr, node_attr in atributos.items():
                    if attr == attribute_name:
                        val_node = node_attr.get('value') if isinstance(node_attr, dict) and 'value' in node_attr else node_attr
                        possible_type = inferences_type(node=val_node, scope=scope)
                        possible_type.add(UNKNOW)
                        return possible_type

    return { UNKNOW }

TYPE_CACHE = {}

def inferences_type(node: dict, scope: Scope) -> set[str]:
    if not node or not isinstance(node, dict) or not node.get('type'):
        return {UNKNOW}

    node_id = id(node)

    if node_id in TYPE_CACHE:
        if TYPE_CACHE[node_id] == {"COMPUTING"}:
            return {UNKNOW}
        return TYPE_CACHE[node_id]

    result_types = set()

    if node['type'] == "binaryOperation" and node['operation'] in BINARY_OPERATIONS:
        left = inferences_type(node=node['leftValue'], scope=scope)
        right = inferences_type(node=node['rightValue'], scope=scope)

        for leftType in left:
            for rightType in right:
                # CORREGIDO: rightType en lugar del conjunto completo 'right'
                if leftType == UNKNOW or rightType == UNKNOW:
                    result_types.add(UNKNOW)
                elif leftType == ERROR or rightType == ERROR:
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
        symbol = scope.buscar_simbolo(nombre=var_name)

        if not symbol:
            return {UNKNOW}
        
        if symbol.get('type') == 'object':
            return { f"object[{var_name}]" }
        elif symbol.get('type') == 'function':
            return {FUNCTION}
        
        symbol_value_dict = symbol.get('value')
        if isinstance(symbol_value_dict, dict) and 'value' in symbol_value_dict:
            TYPE_CACHE[node_id] = {"COMPUTING"}
            resolved_types = inferences_type(node=symbol_value_dict['value'], scope=scope)
            TYPE_CACHE[node_id] = resolved_types
            return resolved_types
        else:
            return {UNKNOW}

    elif node['type'] == 'access':
        result_types = _get_access_type(node=node.get('set'), scope=scope)

    elif node['type'] == 'call':
        result_types = _get_call_type(node=node.get('callee'), scope=scope)

    elif node['type'] == 'attribute_access':
        result_types = _get_attribute_access_type(node=node, scope=scope)

    elif node['type'] in ('summation', 'production'):

        if not node.get('expresion'):
            return {ERROR}

        result_types = inferences_type(node=node['expresion'], scope=scope)

    elif node['type'] == 'ternaryOperation':

        trueValue = node.get('trueValue')
        falseValue = node.get('falseValue')

        trueValueTypes = inferences_type(node=trueValue, scope=scope)
        falseValueTypes = inferences_type(node=falseValue, scope=scope)

        result_types = trueValueTypes.union(falseValueTypes)

    elif node['type'] == 'reference':

        inter_expr = node.get('expresion')

        inter_type = inferences_type(node=inter_expr, scope=scope)

        result_types = { f"ref[{' | '.join(inter_type)}]" }

    elif node['type'] == 'convertion':

        toType = node.get('toType')

        if toType.get('type') == 'id':
            target_name = toType.get('value')

            mapping = {
                "Number": NUMBER,
                "Text": TEXT,
                "Set": SET,
                "Bool": BOOLEAN,
                "Inf": INFINITE,
                "Null": NULL,
                "Nah": INDETERMINATE,
                "Expresion": EXPRESION
            }
            
            if target_name in mapping:
                return {mapping[target_name]}

        return inferences_type(node=toType, scope=scope)
    
    elif node['type'] == 'object_declaration':
        # Al acceder a la declaración de un objeto (ej: m.Point), su tipo es la clase misma
        return { f"object[{node.get('name', 'anonimo')}]" }

    elif node['type'] in ('fun', 'function'):
        # Al acceder a una función del módulo (ej: m.calcular)
        return { FUNCTION }

    else:
        result_types = _get_single_type(node=node)

    return result_types