FUNCIONES_NATIVAS = {
    'rand': {
        "type": "builtin_function",
        "params": ["min", "max"],
        "docstring": "Número aleatorio entre min y max (incluyendo extremos)."
    },
    'sin': {
        "type": "builtin_function",
        "params": ["x"],
        "docstring": "Calcula el seno de un ángulo x expresado en radianes."
    },
    'cos': {
        "type": "builtin_function",
        "params": ["x"],
        "docstring": "Calcula el coseno de un ángulo x expresado en radianes."
    },
    'tan': {
        "type": "builtin_function",
        "params": ["x"],
        "docstring": "Calcula la tangente de un ángulo x expresado en radianes."
    },
    'ln': {
        "type": "builtin_function",
        "params": ["x"],
        "docstring": "Calcula el logaritmo natural de un ángulo x expresado en radianes."
    },
    'exp': {
        "type": "builtin_function",
        "params": ["x"],
        "docstring": "Calcula el exponencial de un ángulo x expresado en radianes."
    },
    'pressed': {
        "type": "builtin_function",
        "params": ["key"],
        "docstring": "Detecta de la tecla key esta presionada en el instante de la llamada."
    },
    'sleep': {
        "type": "builtin_function",
        "params": ["ms"],
        "docstring": "Duerme el programa ms milisegundos. Devuelve null."
    },
    'lim': {
        "type": "builtin_function",
        "params": ["expr", "var -> value"],
        "docstring": "Evalua el limite cuando la variable var de expr tiende a value."
    },
    "d": {
        "type": "builtin_function",
        "params": ["expr"],
        "docstring": "Evalua la derivada simbolica de expr."
    },
    "eval": {
        "type": "builtin_function",
        "params": ["expr", "var = value"],
        "docstring": "Evalua expr sustituyendo var por value"
    }
}

TIPOS_NATIVOS = {
    'Text': {"type": "builtin_type", "docstring": "Cadena de caracteres nativa."},
    'Number': {"type": "builtin_type", "docstring": "Representación de valores numéricos de alta precisión."},
    'Set': {"type": "builtin_type", "docstring": "Conjunto matemático de elementos únicos."},
    'Bool': {"type": "builtin_type", "docstring": "Variable de dos estados"},
    'Inf': {"type": "builtin_type", "docstring": "Definicion de infinito"},
    'Null': {"type": "builtin_type", "docstring": "Valor nulo"},
    'Nah': {"type": "builtin_type", "docstring": "Indeterminacion (o no existe)"},
    'Expresion': {"type": "builtin_type", "docstring": "Expresion simbolica mutable"}
}

class Scope:

    def __init__(self, parent=None, start_row=0, start_col=0, end_row=0, end_col=0):
        self.parent = parent
        self.start_row = start_row
        self.start_col = start_col
        self.end_row = end_row
        self.end_col = end_col

        self.funciones = {}
        self.objetos = {}
        self.variables = {}

        self.children = []

    def contiene_posicion(self, row: int, col: int) -> bool:

        if row < self.start_row or row > self.end_row:
            return False
        
        if row == self.start_row and col < self.start_col:
            return False
        
        if row == self.end_row and col > self.end_col:
            return False
        
        return True
    
    def add_variable(self, nombre: str, variable):

        self.variables[nombre] = variable

    def add_funcion(self, nombre: str, funcion):
        
        self.funciones[nombre] = funcion

    def add_object(self, nombre: str, objeto):

        self.objetos[nombre] = objeto

    def buscar_simbolo(self, nombre: str):

        if nombre in self.variables:
            return self.variables[nombre]
        
        if nombre in self.funciones:
            return self.funciones[nombre]
        
        if nombre in self.objetos:
            return self.objetos[nombre]
        
        if self.parent:

            return self.parent.buscar_simbolo(nombre)
        
        return None
    
    def buscar_scope(self, row: int, col: int):

        for child in self.children:
            scope_encontrado = child.buscar_scope(row, col)
            if scope_encontrado:
                return scope_encontrado
            
        if self.contiene_posicion(row, col):
            return self
        
        return None
    
    def obtener_simbolos_visibles(self):
        simbolos = {
            "variables": self.variables.copy(),
            "funciones": self.funciones.copy(),
            "objetos": self.objetos.copy()
        }

        if self.parent:
            simbolos_padre = self.parent.obtener_simbolos_visibles()
            
            # Fusionamos, dándole prioridad a lo local sobre lo del padre
            for k, v in simbolos_padre["variables"].items():
                if k not in simbolos["variables"]: simbolos["variables"][k] = v
                
            for k, v in simbolos_padre["funciones"].items():
                if k not in simbolos["funciones"]: simbolos["funciones"][k] = v
                
            for k, v in simbolos_padre["objetos"].items():
                if k not in simbolos["objetos"]: simbolos["objetos"][k] = v

        return simbolos
    
    def obtener_simbolos_locales(self):
        simbolos = {
            "variables": self.variables.copy(),
            "funciones": self.funciones.copy(),
            "objetos": self.objetos.copy()
        }

        return simbolos
    
import math

def generate_scope_from_ast(ast: list, mini_scopes: list = None) -> Scope:

    global_scope = Scope(None, 1, 1, math.inf, math.inf)

    for func_name, func in FUNCIONES_NATIVAS.items():
        global_scope.funciones[func_name] = func

    for tipo_name, tipo in TIPOS_NATIVOS.items():
        global_scope.objetos[tipo_name] = tipo

    def _procesar_nodo(node: dict, scope_actual: Scope):
        if not isinstance(node, dict) or 'type' not in node:
            return
        
        tipo = node['type']

        if tipo in ['fun', 'function']:

            scope_actual.add_funcion(node.get('name', 'anonima'), node)

            nuevo_scope = Scope(
                parent=scope_actual,
                start_row=node.get('fila', 1),
                start_col=node.get('columna', 1),
                end_row=node.get('fila_end', 1),
                end_col=node.get('columna_end', 1)
            )

            parametros = node.get('params', node.get('args', []))

            for param in parametros:

                nuevo_scope.add_variable(param, {
                    'type': 'param',
                    'name': param
                })

            for hijo in node.get('body', []):
                _procesar_nodo(hijo, nuevo_scope)

            scope_actual.children.append(nuevo_scope)

        elif tipo == 'object_declaration':
            scope_actual.add_object(node.get('name', 'anonimo'), node)
            
            nuevo_scope = Scope(
                parent=scope_actual,
                start_row=node.get('fila', 1),
                start_col=node.get('columna', 1),
                end_row=node.get('fila_end', 1),
                end_col=node.get('columna_end', 1)
            )
                
            scope_actual.children.append(nuevo_scope)

        elif tipo == 'asignacion':

            vars_ = [lvalue for lvalue in node.get('lvalues', []) if lvalue.get("type", None) == "id"]

            value = None

            if len(vars_) == 1:
                value = node.get("value", None)

            for var in vars_:
                if var and "value" in var:
                    scope_actual.add_variable(var.get("value", None), {
                        "fila": var.get("fila", None),
                        "columna": var.get("columna", None),
                        "value": value
                    })

        elif tipo == 'for':

            nuevo_scope = Scope(
                parent=scope_actual,
                start_row=node.get('fila', 1),
                start_col=node.get('columna', 1),
                end_row=node.get('fila_end', 1),
                end_col=node.get('columna_end', 1)
            )

            vars_names = node.get('vars', [])

            for var in vars_names:
                nuevo_scope.add_variable(var, None)

            for hijo in node.get('body', []):
                _procesar_nodo(hijo, nuevo_scope)

            scope_actual.children.append(nuevo_scope)

        elif tipo == 'while':

            nuevo_scope = Scope(
                parent=scope_actual,
                start_row=node.get('fila', 1),
                start_col=node.get('columna', 1),
                end_row=node.get('fila_end', 1),
                end_col=node.get('columna_end', 1)
            )

            for hijo in node.get('body', []):
                _procesar_nodo(hijo, nuevo_scope)

            scope_actual.children.append(nuevo_scope)

        elif tipo == 'conditional':

            for branch in node.get('branches', []): 

                fila, columna, fila_end, columna_end = branch.get('positions', (1,1,1,1))

                nuevo_scope = Scope(
                    parent=scope_actual,
                    start_row=fila,
                    start_col=columna,
                    end_row=fila_end,
                    end_col=columna_end
                )

                for hijo in branch.get('body', []):
                    _procesar_nodo(hijo, nuevo_scope)

                scope_actual.children.append(nuevo_scope)

            if node.get('else_body', None):

                fila, columna, fila_end, columna_end = node.get('else_positions', (1,1,1,1))

                nuevo_scope = Scope(
                    parent=scope_actual,
                    start_row=fila,
                    start_col=columna,
                    end_row=fila_end,
                    end_col=columna_end
                )

                for hijo in node.get('else_body', []):
                    _procesar_nodo(hijo, nuevo_scope)

                scope_actual.children.append(nuevo_scope)


    for node in ast:
        _procesar_nodo(node=node, scope_actual=global_scope)

    if mini_scopes:

        mini_scopes_ordenados = sorted(
            mini_scopes,
            key=lambda x: (x['fila_end'] - x['fila'], x['columna_end'] - x['columna']),
            reverse=True
        )

        for ms in mini_scopes_ordenados:

            parent_scope = global_scope.buscar_scope(row=ms['fila'], col=ms['columna'])

            nuevo_mini_scope = Scope(
                parent=parent_scope,
                start_row=ms['fila'],
                start_col=ms['columna'],
                end_row=ms['fila_end'],
                end_col=ms['columna_end']
            )

            iterator_vars = ms.get('vars', [])

            for var in iterator_vars:
                nuevo_mini_scope.add_variable(
                    nombre=var,
                    variable=None
                )

            parent_scope.children.append(nuevo_mini_scope)

    return global_scope