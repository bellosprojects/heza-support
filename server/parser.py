from tokens import ExpresionValues
import sys

class ParserError(Exception):
    def __init__(self, mensaje, fila = None, columna = None):
        self.mensaje = mensaje
        self.fila = fila
        self.columna = columna

    def __str__(self):
        if self.fila is not None and self.columna is not None:
            return f"[Error de sintaxis]: {self.mensaje} (línea {self.fila}, columna {self.columna})"
        return f"[Error de sintaxis]: {self.mensaje}"
    
    def __repr__(self):
        return self.__str__()
    
class Parser:

    """
    Parser para el lenguaje Heza.

    Convierte una lista de tokens en un árbol de sintaxis abstracta (AST).

    Args:
        tokens (list): Lista de tokens generados por el lexer, cada uno con tipo, valor, fila y columna.
    
    Attributes
    =======
        tokens (list): Lista de tokens a procesar.
        pos (int): Posición actual en la lista de tokens.
        current_token (tuple): Token actual que se está procesando.
        inFuction (bool): Indica si se esta procesando el cuerpo de una funcion.
        inBucle (bool): Indica si se esta procesando el cuerpo de un bucle.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
        self.inFunction = False
        self.inBucle = 0
        self.usages = []
        self.mini_scopes = []
        sys.set_int_max_str_digits(43000)

    def advance(self):

        """
        Aumenta el atributo `pos` una unidad y asigna a `current_token` el siguiente token si no se excede el tamaño (`None`) en otro caso.
        """

        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def error(self, msg):

        """
        Metodo que maneja los errores de tokens inesperados.

        Parameters
        ==========

        msg (str) : Mensaje de error.

        Raises
        =======

        ParserError (Exception) : Error durante el analisis sintactico.
        """

        if not self.current_token and self.pos > 0:
            self.current_token = self.tokens[self.pos - 1]
        fila = self.current_token[2] if self.current_token and len(self.current_token) > 2 else None
        columna = self.current_token[3] if self.current_token and len(self.current_token) > 3 else None
        raise ParserError(msg, fila, columna)
    
    def parse_arguments(self):
        """
        Parsea una lista de argumentos separados por comas hasta encontrar ')'.
        Devuelve una lista de nodos AST.
        """
        args = []
        if self.current_token and self.current_token[0] == 'CLOSEP':
            return args
        while self.current_token and self.current_token[0] in ExpresionValues:
            arg = self.parse_expresion()
            args.append(arg)
            if self.current_token and self.current_token[0] == 'COMA':
                self.advance()
            else:
                break
        return args
    
    def parse_postfix(self, left):
        """
        Aplica todos los postfijos (acceso a índice, llamada, acceso a atributo)
        de forma iterativa sobre un nodo primario.
        """
        while True:
            if self.current_token and self.current_token[0] == 'OPENC':  # [
                self.advance()
                index = self.parse_expresion()
                if not self.current_token or self.current_token[0] != 'CLOSEC':
                    self.error("Se esperaba ]")
                self.advance()
                left = {
                    'type': 'access',
                    'set': left,
                    'index': index
                }
                continue

            elif self.current_token and self.current_token[0] == 'PUNTO':  # .
                self.advance()
                if not self.current_token or self.current_token[0] != 'ID':
                    self.error("Se esperaba un identificador después de .")
                attr_name = self.current_token[1]
                self.advance()
                left = {
                    'type': 'attribute_access',
                    'object': left,
                    'attribute': attr_name
                }
                continue

            elif self.current_token and self.current_token[0] == 'OPENP':  # (
                # Verificar si es una función especial
                if left.get('type') == 'id' and left['value'] in ('lim', 'eval', 'd'):
                    self.advance()  # consumir (
                    if left['value'] == 'lim':
                        return self.parse_lim()
                    elif left['value'] == 'eval':
                        return self.parse_eval()
                    elif left['value'] == 'd':
                        return self.parse_derivative()
                # Llamada normal a función/método
                self.advance()
                args = self.parse_arguments()
                if not self.current_token or self.current_token[0] != 'CLOSEP':
                    self.error("Se esperaba )")
                self.advance()
                left = {
                    'type': 'call',
                    'callee': left,
                    'args': args
                }
                continue

            else:
                break

        return left
    
    def parse_expresion(self):

        """
        Metodo principal que se encarga de inciar la busqueda de una expresion aritmetica|logica

        Returns
        ========
            Node (dict) : AST de la expresion
        """

        return self.parse_binary_operation_logic()
    
    def parse_binary_operation_logic(self):

        """
        Metodo que busca una operacion binaria logica (AND|OR)

        Retorna el nodo del siguiente nivel si no hay operaciones logicas binarias

        Returns
        ========
            Node (dict) : AST de la expresion
        """

        left = self.parse_unary_operation_logic()
        while self.current_token is not None and self.current_token[0] in ['AND','OR','THEN']:
            op = str(self.current_token[0]).lower()
            self.advance()
            right = self.parse_unary_operation_logic()
            left = {
                'type': 'binaryOperation',
                'operation': op,
                'leftValue': left,
                'rightValue': right
            }
        return left
    
    def parse_unary_operation_logic(self):

        """
        Metodo que busca la operacion logica unaria (NOT)

        Retorna el nodo del siguiente nivel si no se encuentra el token NOT

        Returns
        ========
            Node (dict) : AST de la expresion
        """

        if self.current_token and self.current_token[0] == 'NOT':
            self.advance()
            value = self.parse_binary_operation_relational()
            return {
                'type': "unaryOperation",
                'operation': 'not',
                'value': value
            }
        return self.parse_binary_operation_relational()
    
    def parse_binary_operation_relational(self):

        """
        Metodo que busca una operacion binaria de comparacion
        
        (COMPARACION|DIFFERENT|MAYOR|MAYORE|MENOR|MENORE|IN)

        Retorna el nodo del siguiente nivel si no hay comparaciones binarias

        Returns
        ========
            Node (dict) : AST de la expresion
        """

        left = self.parse_binary_operation_add_sub()
        while self.current_token is not None and self.current_token[0] in ['COMPARACION','DIFFERENT','MAYORE','MENORE','MAYOR','MENOR','IN', 'NOTIN', 'DEL']:
            convertion_table = {
                'COMPARACION': 'equal',
                'DIFFERENT': 'nEqual',
                'MAYOR': 'greater',
                'MENOR': 'less',
                'MAYORE': 'greaterEqual',
                'MENORE': 'lessEqual',
                'IN': 'in',
                'NOTIN': 'notin',
                'DEL': 'del'
            }
            op = convertion_table[self.current_token[0]]
            self.advance()
            right = self.parse_binary_operation_add_sub()
            left = {
                    'type':'binaryOperation',
                    'operation':op,
                    'leftValue':left,
                    'rightValue':right
                    }
        return left
    
    def parse_binary_operation_add_sub(self):
        left = self.parse_binary_operation_mul_div_mod()
        while self.current_token and self.current_token[0] in ['SUMA','RESTA']:
            op =  'add' if self.current_token[0] == 'SUMA' else 'sub'
            self.advance()
            right = self.parse_binary_operation_mul_div_mod()
            left = {
                    'type':'binaryOperation',
                    'operation':op,
                    'leftValue':left,
                    'rightValue':right
                    }
        return left
    
    def parse_binary_operation_mul_div_mod(self):
        left = self.parse_unary_operation_aritmetic()
        while self.current_token is not None and self.current_token[0] in ['MULTIPLICACION','DIVISION','MOD']:
            convertion_table = {
                'MULTIPLICACION': 'mul',
                'DIVISION': 'div',
                'MOD': 'mod'
            }
            op = convertion_table[self.current_token[0]]
            self.advance()
            right = self.parse_unary_operation_aritmetic()
            left = {
                    'type':'binaryOperation',
                    'operation':op,
                    'leftValue':left,
                    'rightValue':right
                    }
        return left
    
    def parse_unary_operation_aritmetic(self):
        if self.current_token is not None and self.current_token[0] in ['RESTA','SUMA','EXC','SQRT']:
            convertion_table = {
                'SUMA': 'pos',
                'RESTA': 'neg',
                'EXC': 'fact',
                'SQRT': 'sqrt'
            }
            op = convertion_table[self.current_token[0]]
            self.advance()
            expr = self.parse_binary_operation_pow()
            return {
                    'type':'unaryOperation',
                    'operation':op,
                    'value':expr
                    }
        else:
            return self.parse_binary_operation_pow()
        
    def parse_binary_operation_pow(self):
        left = self.parse_binary_operation_sets()
        while self.current_token is not None and self.current_token[0] == 'POW':
            self.advance()
            right = self.parse_binary_operation_sets()
            left = {
                    'type':'binaryOperation',
                    'operation':'pow',
                    'leftValue':left,
                    'rightValue':right
                    }
        return left

    def parse_binary_operation_sets(self):
        left = self.parse_convertions()
        while self.current_token is not None and self.current_token[0] in ['UNION','INTERSECTION','SIMETRIC_DIFFERENCE', 'CROSS']:
            convertion_table = {
                'UNION': 'union',
                'INTERSECTION': 'inter',
                'SIMETRIC_DIFFERENCE': 'symDiff',
                'CROSS': 'cross'
            }
            
            op = convertion_table[self.current_token[0]]
            self.advance()
            right = self.parse_convertions()
            left = {
                    'type':'binaryOperation',
                    'operation':op,
                    'leftValue':left,
                    'rightValue':right
                    }
        return left
    
    def parse_convertions(self):
        left = self.parse_parentesis()
        while self.current_token is not None and self.current_token[0] == 'PIPE':
            self.advance()
            right = self.parse_parentesis()
            left = {
                    'type':'convertion',
                    'value':left,
                    'toType':right
                    }
        return left

    def parse_parentesis(self):
        if self.current_token and self.current_token[0] == 'OPENP':
            self.advance()
            first = self.parse_expresion()
            if self.current_token and self.current_token[0] == 'COMA':
                values = [first]
                while self.current_token and self.current_token[0] == 'COMA':
                    self.advance()
                    values.append(self.parse_expresion())
                if not self.current_token or self.current_token[0] != 'CLOSEP':
                    self.error("Se esperaba ) para cerrar la tupla")
                self.advance()
                return {"type": "tuple", "values": values}
            else:
                if not self.current_token or self.current_token[0] != 'CLOSEP':
                    self.error("Se esperaba )")
                self.advance()
                return first  # ya tiene postfix aplicado
        else:
            return self.parse_value()
        
    def parse_index_access(self, left):
        """Parsea accesos por índice encadenados: expr[0][1]..."""
        while self.current_token and self.current_token[0] == 'OPENC':
            self.advance()  # consumir [
            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un índice después de [")
            index = self.parse_expresion()
            if not self.current_token or self.current_token[0] != 'CLOSEC':
                self.error("Se esperaba ] para cerrar el acceso por índice")
            self.advance()  # consumir ]
            left = {
                'type': 'access',
                'set': left,
                'index': index
            }
        return left
        
    def parse_value(self):
        if not self.current_token:
            self.error("Se esperaba un valor")

        if self.current_token[0] == 'NUMBER':
            value = self.current_token[1]
            self.advance()
            node = {"type": "number", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'ID':
            value = self.current_token[1]
            fila = self.current_token[2]
            columna = self.current_token[3]
            self.usages.append({
                "name": value,
                "fila": fila,
                "columna": columna
            })
            self.advance()
            # Instanciación rápida de objeto
            if self.current_token and self.current_token[0] == 'OPENL':
                self.advance()
                return self.parse_object_instantiation(value)
            node = {"type": "id", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'FALSE':
            self.advance()
            node = {"type": "bool", "value": False}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'TRUE':
            self.advance()
            node = {"type": "bool", "value": True}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'EXPRESION':
            value = self.current_token[1]
            self.advance()
            node = {"type": "expresion", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'TEXT':
            value = self.current_token[1]
            self.advance()
            node = {"type": "text", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'NULL':
            self.advance()
            node = {"type": "null"}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'INFINITE':
            self.advance()
            node = {"type": "infinite"}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'INDETERMINATE':
            self.advance()
            node = {"type": "indeterminate"}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'TRACE':
            self.advance()
            return self.parse_trace()  # trace ya es un valor completo

        elif self.current_token[0] == 'ARROBA':
            self.advance()
            expr = self.parse_expresion()
            node = {"type": "arroba", "value": expr}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'OPENC':
            self.advance()
            return self.parse_range()  # range ya es un valor completo

        elif self.current_token[0] == 'SUMMATION':
            self.advance()
            return self.parse_summation()

        elif self.current_token[0] == 'PRODUCTION':
            self.advance()
            return self.parse_production()

        elif self.current_token[0] == 'OPENL':
            self.advance()
            return self.parse_set()  # set ya es valor completo

        elif self.current_token[0] == 'PARTIAL':
            self.advance()
            return self.parse_derivative(its_partial=True)

        elif self.current_token[0] == 'INTEGRAL':
            self.advance()
            return self.parse_integral()

        elif self.current_token[0] == 'REFERENCE':
            self.advance()
            node = {"type": "reference", "expresion": self.parse_expresion()}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'BARRA':
            self.advance()
            value = self.parse_expresion()
            if not self.current_token or self.current_token[0] != 'BARRA':
                self.error("Se esperaba | para cerrar abs")
            self.advance()
            node = {"type": "abs", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'FOREACH':
            self.advance()
            return self.parse_foreach()

        elif self.current_token[0] == 'EXIST':
            self.advance()
            return self.parse_exist()

        elif self.current_token[0] in ('ESP', 'TAB', 'LINE'):
            value = self.current_token[1]
            self.advance()
            node = {"type": "constantText", "value": value}
            return self.parse_postfix(node)

        elif self.current_token[0] == 'OPENP':
            # Este caso ya no debería ocurrir porque parse_parentesis lo captura,
            # pero lo dejamos por si acaso.
            self.advance()
            expr = self.parse_expresion()
            if not self.current_token or self.current_token[0] != 'CLOSEP':
                self.error("Se esperaba )")
            self.advance()
            return self.parse_postfix(expr)
        
        elif self.current_token[0] == 'IF':
            self.advance()

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba una condicion despues de if")

            condition = self.parse_expresion()

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un valor despues de la condicion en if")

            trueValue = self.parse_expresion()

            if not self.current_token or self.current_token[0] != 'ELSE':
                self.error("Se esperaba else despues del primer valor en if")
            self.advance()

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un valor despues de else en if")

            falseValue = self.parse_expresion()

            return {
                "type": "ternaryOperation",
                "condition": condition,
                "trueValue": trueValue,
                "falseValue": falseValue
            }

        else:
            self.error(f"Se esperaba un valor y se recibió: {self.current_token[1]}")

    def parse_trace(self):
        if not self.current_token or self.current_token[0] != "DOUBLE":
            self.error("Se esperaba el operador de referencia despues de trace")
        self.advance()
        if not self.current_token or self.current_token[0] != "ID":
            self.error("Se esperaba un identificador despues de trace:")
        var_name = self.current_token[1]
        self.advance()
        return {
            "type": "trace",
            "value": var_name
        }
    
    def parse_range(self):
        if not self.current_token:
            self.error("Se esperaba un valor para fromValue en Rango")
        fromValue = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'COMA':
            self.error("Se esperaba , despues de fromValue en Rango")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba un valor para toValue en Rango")
        toValue = self.parse_expresion()

        if not self.current_token:
            self.error("Se esperaba ] para cerrar el Rango")

        if self.current_token[0] == "CLOSEC":
            self.advance()
            return {
                "type": "range",
                "fromValue": fromValue,
                "toValue": toValue
            }
        if self.current_token[0] != "DOUBLE":
            self.error("Se esperaba : para indicar el step en Rango o ] para cerrar")
        self.advance() 

        if not self.current_token:
            self.error("Se esperaba un valor para step en Rango")
        step = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'CLOSEC':
            self.error("Se esperaba ] para cerrar el rango")
        self.advance()

        return {
            "type": "range",
            "fromValue": fromValue,
            "toValue": toValue,
            "step": step
        }
    
    def parse_summation(self):
        
        if not self.current_token or self.current_token[0] != 'OPENP':
            self.error("Se esperaba ( despues de ∑")

        fila = self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador despues de ∑(")
        varName = self.current_token[1]
        self.advance()

        if not self.current_token or self.current_token[0] != "IN":
            self.error(f"Se esperaba ∈ despues de ∑({varName}")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba un conjunto despues de ∈ en summation")
        set = self.parse_expresion()
        
        if not self.current_token or self.current_token[0] != "COMA":
            self.error("Se esperaba una coma despues del conjunto en summation")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba una expresion para summation despues de la coma")
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != "CLOSEP":
            self.error("Se esperaba ) despues de la expresion en summation")

        fila_end = self.current_token[2]
        columna_end = self.current_token[3]
        self.advance()

        self.mini_scopes.append({
            "vars": [varName],
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "summation",
            "set": set,
            "var": varName,
            "expresion": expresion
        }
    
    def parse_production(self):
        if not self.current_token or self.current_token[0] != 'OPENP':
            self.error("Se esperaba ( despues de ∏")

        fila = self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador despues de ∏(")
        varName = self.current_token[1]
        self.advance()

        if not self.current_token or self.current_token[0] != "IN":
            self.error(f"Se esperaba ∈ despues de ∏({varName}")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba un conjunto despues de ∈ en production")
        set = self.parse_expresion()
        
        if not self.current_token or self.current_token[0] != "COMA":
            self.error("Se esperaba una coma despues del conjunto en production")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba una expresion para production despues de la coma")
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != "CLOSEP":
            self.error("Se esperaba ) despues de la expresion en production")

        fila_end = self.current_token[2]
        columna_end = self.current_token[3]
        self.advance()

        self.mini_scopes.append({
            "vars": [varName],
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "production",
            "set": set,
            "var": varName,
            "expresion": expresion
        }
    
    def parse_set(self):
        if not self.current_token:
            self.error("Se esperaba un valor despues de {")

        if self.current_token[0] == 'CLOSEL':
            self.advance()
            return {
                "type": "set",
                "value": []
            }

        pos_aux = self.pos
        token_aux = self.current_token
        _ = self.parse_expresion()

        if not self.current_token:
            self.error("Se esperaba } para cerrar el conjunto")

        if self.current_token[0] == 'BARRA':
            self.current_token = token_aux
            self.pos = pos_aux
            return self.parse_transformation()
        
        self.current_token = token_aux
        self.pos = pos_aux

        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'ID':
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos+1][0] == 'IN':
                is_sub = False
                num = self.pos+2
                llaves = 0
                while num < len(self.tokens):
                    if self.tokens[num][0] == 'OPENL':
                        llaves += 1
                    if self.tokens[num][0] == 'CLOSEL':
                        llaves -= 1
                    if self.tokens[num][0] == 'COMA' and llaves == 0:
                        break
                    if self.tokens[num][0] == 'DOUBLE':
                        is_sub = True
                        break
                    num += 1

                if is_sub:
                    return self.parse_filter()
                
        values = []

        while self.current_token and self.current_token[0] in ExpresionValues:
            value = self.parse_expresion()
            values.append(value)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba } para cerrar el conjunto 2")
        self.advance()

        return {
            "type": "set",
            "value": values
        }


    def parse_transformation(self):
        
        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion despues de { en transformation")

        fila = self.current_token[2]
        columna = self.current_token[3]
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'BARRA':
            self.error("Se esperaba | despues de la expresion en transformation")
        self.advance()

        t_vars = []
        sets = []
        condition = {
            "type": "bool",
            "value": True
        }

        while self.current_token and self.current_token[0] == 'ID':
            var = self.current_token[1]
            t_vars.append(var)
            self.advance()

            if not self.current_token or self.current_token[0] != 'IN':
                self.error("Se esperaba ∈ espues de la variable en transformation")
            self.advance()

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error(f"Se esperaba un valor como el conjunto de la variable {var}")
            set = self.parse_expresion()
            sets.append(set)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        if self.current_token and self.current_token[0] == 'DOUBLE':
            self.advance()

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba una condicion despues de : en transformation")
            condition = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba { para cerrar la transformacion")

        fila_end = self.current_token[2]
        columna_end = self.current_token[3]
        self.advance()

        if len(t_vars) != len(sets):
            self.error("La cantidad de conjuntos es distinta a la cantidad de variables en transformation")

        self.mini_scopes.append({
            "vars": t_vars,
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "transformation",
            "sets": sets,
            "vars": t_vars,
            "expresion": expresion,
            "condition": condition
        }

    def parse_filter(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador en filter")
        var = self.current_token[1]
        fila = self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'IN':
            self.error("Se esperaba ∈ despues de {"+var)
        self.advance()

        if not self.current_token:
            self.error("Se esperaba un conjunto para filter despues de ∈")
        set = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'DOUBLE':
            self.error("Se esperaba el operador de referencia")
        self.advance()

        if not self.current_token:
            self.error("Se esperaba una condicion despues de : en filter")

        condition = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba } para cerrar el filtro")

        fila_end = self.current_token[2]
        columna_end = self.current_token[3]
        self.advance()

        self.mini_scopes.append({
            "vars": [var],
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "filter",
            "set": set,
            "var": var,
            "condition": condition
        }
    
    def parse_derivative(self, its_partial = False):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion como funcion despues d(")
        
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'CLOSEP':
            self.error("Se esperaba ) para cerrar derivative")
        self.advance()

        if not self.current_token or self.current_token[0] != 'DIVISION':
            self.error("Se esperaba una / despues de la expresion en derivative")
        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador como variable en derivative")

        var = self.current_token[1]
        self.advance()

        if len(var) != 2 or var[0] != 'd' or not str(var[1]).isalpha():
            self.error(f"La expresion {var} no es valida como diferencial")

        return {
            "type": "derivative",
            "expresion": expresion,
            "var": var[1],
            "its_partial": its_partial
        }
    
    def parse_integral(self):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion como limite inferior despues de ∫")

        limI = self.parse_expresion()

        if not self.current_token or self.current_token[0] not in ['DPUNTO', 'ID'] :
            self.error("Se esperaba .. o d() despues del primer termino de la integral")

        if self.current_token[0] == 'ID':
            diferencial = self.current_token[1]

            if len(diferencial) != 2 or diferencial[0] != 'd' or not str(diferencial[1]).isalpha():
                self.error(f"{diferencial} no es un diferencial valido")

            self.advance()

            return {
                "type": "indefiniteIntegral",
                "expresion": limI,
                "var": diferencial[1]
            }

        if not self.current_token or self.current_token[0] != 'DPUNTO':
            self.error("Se esperaba .. despues del limite inferior en integral")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba un limite superior en integral definida")

        limS = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'DOUBLE':
            self.error("Se esperaba : despues de los limites para integral definida")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion para integrar en integral definida")
        
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un diferencial en integral definida")

        diferencial = self.current_token[1]

        if len(diferencial) != 2 or diferencial[0] != 'd' or not str(diferencial[1]).isalpha():
            self.error(f"{diferencial} no es un diferencial valido")

        self.advance()

        return {
            "type": "definiteIntegral",
            "expresion": expresion,
            "var": diferencial[1],
            "limI": limI,
            "limS": limS
        }

    def parse_parts(self, name, args, initial_position):

        expresions = []
        hav_else = 0
        while self.current_token:
            if self.current_token[0] == 'CLOSEL':
                break

            expresion = self.parse_expresion()
            condition = {
                'type': 'bool',
                'value': True
            }
            if self.current_token and self.current_token[0] == 'IF':
                self.advance()
                if not self.current_token or self.current_token[0] not in ExpresionValues:
                    self.error("Se esperaba una condicion")
                condition = self.parse_expresion()
            else:
                hav_else += 1

            expresions.append({
                'condition': condition,
                'expresion': expresion
            })

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        if hav_else == 0:
            self.error(f"la funcion a trozos {name} debe tener un valor de retorno por defecto")
        elif hav_else > 1:
            self.error(f"la funcion a trozos {name} solo puede tener un valor de retorno por defecto")
        
        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba } para cerrar la funcion a trozos")
        fila_end = self.current_token[2]
        columna_end = self.current_token[3]
        self.advance()

        return {
            'type': 'function',
            'name': name,
            'args': args,
            'expresions': expresions,
            'fila': initial_position[0],
            'columna': initial_position[1],
            'fila_end': fila_end,
            'columna_end': columna_end,
            'its_parts': True
        }

    def parse_lim(self):
        
        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion como funcion en despues de lim(")
        expresion = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'COMA':
            self.error("Se esperaba una coma despues de la expresion en lim")
        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba una variable despues de la coma para lim")
        var = self.current_token[1]
        self.advance()

        if not self.current_token or self.current_token[0] != 'THEN':
            self.error(f"Se esperaba → despues de {var} en lim")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error(f"Se esperaba un valor para despues de {var} → en lim")
        value = self.parse_expresion()

        value_dir = None
        if self.current_token and self.current_token[0] in ['SUMA','RESTA']:
            value_dir = self.current_token[1]
            self.advance()

        if not self.current_token or self.current_token[0] != 'CLOSEP':
            self.error("Se esperaba ) para cerrar lim")
        self.advance()

        return {
            "type": "lim",
            "expresion": expresion,
            "var": var,
            "value": value,
            'dir': value_dir
        }

    def parse_eval(self):
        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion como funcion en despues de eval(")
        expresion = self.parse_expresion()

        if not self.current_token:
            self.error("Se esperaba ) para cerrar eval")
        
        if self.current_token[0] == 'CLOSEP':
            self.advance()

            return {
                "type": "totalEval",
                "expresion": expresion
            }
        
        if self.current_token[0] != 'COMA':
            self.error("Se esperaba ) para cerrar eval")
        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador como variable en eval")
        var = self.current_token[1]
        self.advance()

        if not self.current_token or self.current_token[0] != 'ASIGNACION':
            self.error(f"Se esperaba = despues {var} en eval")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error(f"Se esperaba un valor despues despues de {var} = en eval")
        value = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'CLOSEP':
            self.error("Se esperaba ) para cerrar eval")
        self.advance()

        return {
            "type": "eval",
            "expresion": expresion,
            "var": var,
            "value": value
        } 
    
    def parse_reference(self):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion para referenciar despues de &")

        expresion = self.parse_expresion()

        return {
            "type": "reference",
            "expresion": expresion
        }

    def parse_abs(self):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba un valor despues de | (abs)")
        value = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'BARRA':
            self.error("Se esperaba | despues de la expresion para cerra abs")
        self.advance()

        return {
            "type": "abs",
            "value": value
        }
    
    def parse_foreach(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba una variable iteradora despues de ∀")
        var = self.current_token[1]
        fila =self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'IN':
            self.current_token(f"Se esperaba ∈ depues de ∀ {var}")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error(f"Se esperaba un conjunto para recorres despues de ∀ {var} ∈")
        set = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'DOUBLE':
            self.error("Se esperaba : despues del conjunto en ∀")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion booleana despues de : en ∀")
        condition = self.parse_expresion()

        import math

        fila_end = math.inf
        columna_end = math.inf

        if self.current_token:
            fila_end = self.current_token[2]
            columna_end = self.current_token[3]

        self.mini_scopes.append({
            "vars": [var],
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "foreach",
            "set": set,
            "var": var,
            "condition": condition
        }

    def parse_exist(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba una variable iteradora despues de ∃")
        var = self.current_token[1]
        fila =self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'IN':
            self.current_token(f"Se esperaba ∈ depues de ∃ {var}")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error(f"Se esperaba un conjunto para recorres despues de ∃ {var} ∈")
        set = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'DOUBLE':
            self.error("Se esperaba : despues del conjunto en ∃")
        self.advance()

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una expresion booleana despues de : en ∃")
        condition = self.parse_expresion()

        import math

        fila_end = math.inf
        columna_end = math.inf

        if self.current_token:
            fila_end = self.current_token[2]
            columna_end = self.current_token[3]

        self.mini_scopes.append({
            "vars": [var],
            "fila": fila,
            "columna": columna,
            "fila_end": fila_end,
            "columna_end": columna_end
        })

        return {
            "type": "exist",
            "set": set,
            "var": var,
            "condition": condition
        }
    
    def parse_fun(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador de funcion despues de fun")

        fun_name = self.current_token[1]
        fila = self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        if not self.current_token or self.current_token[0] != 'OPENP':
            self.error(f"Se esperaba ( despues de fun {fun_name}")
        self.advance()

        params = []

        while self.current_token and self.current_token[0] == 'ID':

            param = self.current_token[1]
            params.append(param)
            self.advance()

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        if not self.current_token or self.current_token[0] != 'CLOSEP':
            self.error(f"Se esperaba ) despues de los parametros en fun {fun_name}")
        self.advance()

        if not self.current_token or self.current_token[0] != 'OPENL':
            self.error("Se espraba { para iniciar el cuerpo de la funcion " + fun_name)
        self.advance()

        body = []

        self.inFunction = True

        while self.current_token:

            if self.current_token[0] == 'CLOSEL':
                break

            inst = self.parse_instruccion()
            body.append(inst)

        self.inFunction = False

        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esparaba } para cerrar el cuerpo de la funcion " + fun_name)

        fila_end = self.current_token[2]
        columna_end = self.current_token[3]

        self.advance()

        return {
            'type': 'fun',
            'name': fun_name,
            'params': params,
            'body': body,
            'fila': fila,
            'columna': columna,
            'fila_end': fila_end,
            'columna_end': columna_end
        }
    
    def parse_return(self):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esparaban uno o mas valores despues de return")

        values = []

        while self.current_token and self.current_token[0] in ExpresionValues:
            val = self.parse_expresion()
            values.append(val)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        return {
            'type': 'return',
            'values': values
        }
    
    def parse_body(self):

        if not self.current_token:
            self.error("Se esperaba una instruccion")

        fila = self.current_token[2]
        columna = self.current_token[3]

        """Parsea un bloque de instrucciones o una instrucción única."""
        if self.current_token and self.current_token[0] == 'OPENL':
            self.advance()  # consumir {
            body = []
            while self.current_token and self.current_token[0] != 'CLOSEL':
                inst = self.parse_instruccion()
                if inst is not None:
                    body.append(inst)
            if not self.current_token or self.current_token[0] != 'CLOSEL':
                self.error("Se esperaba } para cerrar el bloque")
            fila_end = self.current_token[2]
            columna_end = self.current_token[3]
            self.advance()  # consumir }
            return body, (fila, columna, fila_end, columna_end)
        else:
            # Instrucción única (sin llaves)
            inst = self.parse_instruccion()
            if inst is None:
                self.error("Se esperaba una instrucción")
            import math
            fila_end = self.current_token[2] if self.current_token else math.inf
            columna_end = self.current_token[3] if self.current_token else math.inf

            return [inst], (fila, columna, fila_end, columna_end)

    def parse_conditional(self):
        
        # Se espera que el token actual sea IF (ya fue consumido en parse_instruccion)
        condition = self.parse_expresion()
        body, positions = self.parse_body()

        branches = [{'condition': condition, 'body': body, 'positions': positions}]
        else_body = None
        pos = (1,1,1,1)

        # Verificar si hay else o else if
        while self.current_token and self.current_token[0] == 'ELSE':
            self.advance()  # consumir ELSE
            if self.current_token and self.current_token[0] == 'IF':
                # else if
                self.advance()  # consumir IF
                cond = self.parse_expresion()
                b, p = self.parse_body()
                branches.append({'condition': cond, 'body': b, 'positions': p})
            else:
                # else simple
                else_body, pos = self.parse_body()
                break

        return {
            'type': 'conditional',
            'branches': branches,
            'else_body': else_body,
            'else_positions': pos
        }
            
    def parse_input(self):
        
        if not self.current_token or self.current_token[0] != 'PIPE':
            self.error("Se esperaba << despues de Sys.in")
        self.advance()

        vars = []

        while self.current_token:

            if not self.current_token or self.current_token[0] != 'ID':
                self.error("Se esperaba un identificador en Sys.in")

            value = self.current_token[1]
            self.advance()
            vars.append(value)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            
            self.advance()

        return {
            "type": "sys.in",
            "vars": vars
        }
        
    def parse_for(self):

        pattern_type = 'simple'   # 'simple' o 'tuple'
        vars_for = []
        sets = []

        # --- Detectar si el primer token es '(' (patrón de tupla) ---
        if self.current_token and self.current_token[0] == 'OPENP':
            self.advance()  # consumir '('
            # Leer identificadores dentro del paréntesis
            while self.current_token and self.current_token[0] == 'ID':
                vars_for.append(self.current_token[1])
                self.advance()
                if not self.current_token or self.current_token[0] != 'COMA':
                    break
                self.advance()
            if not self.current_token or self.current_token[0] != 'CLOSEP':
                self.error("Se esperaba ) para cerrar el patrón de tupla")
            self.advance()
            if not self.current_token or self.current_token[0] != 'IN':
                self.error("Se esperaba ∈ después del patrón de tupla")
            self.advance()
            # Parsear el conjunto
            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un conjunto después de ∈")
            set_node = self.parse_expresion()
            sets.append(set_node)
            pattern_type = 'tuple'
            # No se permiten más patrones después de una tupla
        else:
            # --- Comportamiento original: lista de variables y conjuntos (por índices) ---
            while self.current_token and self.current_token[0] == 'ID':
                var = self.current_token[1]
                vars_for.append(var)
                self.advance()
                if not self.current_token or self.current_token[0] != 'IN':
                    self.error(f"Se esperaba ∈ después de {var}")
                self.advance()
                if not self.current_token or self.current_token[0] not in ExpresionValues:
                    self.error(f"Se esperaba un conjunto para la variable {var}")
                set_node = self.parse_expresion()
                sets.append(set_node)
                if not self.current_token or self.current_token[0] != 'COMA':
                    break
                self.advance()

        # --- El resto (DO y cuerpo) es igual ---
        if not self.current_token or self.current_token[0] != 'DO':
            self.error("Se esperaba do después de los conjuntos en ∀")

        fila = self.current_token[2]
        columna = self.current_token[3]
        self.advance()

        body = []
        if self.current_token[0] == 'OPENL':
            self.advance()
            self.inBucle += 1
            while self.current_token and self.current_token[0] != 'CLOSEL':
                inst = self.parse_instruccion()
                body.append(inst)
            self.inBucle -= 1
            if not self.current_token or self.current_token[0] != 'CLOSEL':
                self.error("Se esperaba } para cerrar el bucle for")
            fila_end = self.current_token[2]
            columna_end = self.current_token[3]
            self.advance()
        else:
            inst = self.parse_instruccion()
            body.append(inst)
            fila_end = fila
            columna_end = columna

        return {
            'type': 'for',
            'pattern_type': pattern_type,   # 'simple' o 'tuple'
            'vars': vars_for,
            'sets': sets,
            'body': body,
            'fila': fila,
            'columna': columna,
            'fila_end': fila_end,
            'columna_end': columna_end
        }

    def parse_while(self):

        if not self.current_token or self.current_token[0] not in ExpresionValues:
            self.error("Se esperaba una condicion despues de while ")

        condition = self.parse_expresion()

        if not self.current_token or self.current_token[0] != 'DO':
            self.error("Se esperaban do despues de la condicion en while")

        self.advance()

        if not self.current_token:
            self.error("Se esperaba una instruccion despues de do en while")

        fila = self.current_token[2]
        columna = self.current_token[3]

        body = []

        if self.current_token[0] != 'OPENL':
            unique_instruction = self.parse_instruccion()
            body.append(unique_instruction)
            fila_end = fila
            columna_end = columna

        else:
            
            self.advance()

            self.inBucle += 1

            while self.current_token:

                if self.current_token[0] == 'CLOSEL':
                    break

                instruccion = self.parse_instruccion()
                body.append(instruccion)

            self.inBucle -= 1

            if not self.current_token or self.current_token[0] != 'CLOSEL':
                self.error("Se esperaba } para cerrar el while")
            fila_end = self.current_token[2]
            columna_end = self.current_token[3]
            self.advance()

        return {
            "type": "while",
            "condition": condition,
            'body': body,
            'fila': fila,
            'columna': columna,
            'fila_end': fila_end,
            'columna_end': columna_end
        }


    def parse_copy(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba uno o mas identificadores despues de copy")

        vars = []

        while self.current_token and self.current_token[0] == 'ID':

            var_name = self.current_token[1]
            vars.append(var_name)
            self.advance()

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        return {
            'type': 'copy',
            'vars': vars
        }

    def parse_add(self, set_name):

        values = []

        while self.current_token:

            if self.current_token[0] not in ExpresionValues:
                self.error(f"Se esperaba un valor para agregar al conjunto {set_name}")

            valor = self.parse_expresion()
            values.append(valor)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        return {
            'type': 'add',
            'set': set_name,
            'values': values
        }

    def parse_print(self):

        if not self.current_token or self.current_token[0] != 'UNPIPE':
            self.error("Se esperaba << despues de Sys.out")
        self.advance()

        values = []

        while self.current_token:

            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un valor para imprimir")

            value = self.parse_expresion()
            values.append(value)

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            
            self.advance()

        return {
            "type": "sys.out",
            "values": values
        }
    
    def parse_sys(self):
        if not self.current_token or self.current_token[0] != 'PUNTO':
            self.error("Se esperaba . después de Sys")
        self.advance()

        if not self.current_token or self.current_token[0] != "ID":
            self.error("Se esperaba un identificador después de Sys.")
        command = self.current_token[1]
        self.advance()

        if command == 'out':
            return self.parse_print()
        elif command == 'in':
            return self.parse_input()
        elif command == 'clear':
            return {"type": "sys.clear"}
        elif command == 'set':
            if not self.current_token or self.current_token[0] != 'OPENP':
                self.error("Se esperaba ( después de Sys.set")
            self.advance()
            prop = self.parse_expresion()
            if not self.current_token or self.current_token[0] != 'COMA':
                self.error("Se esperaba , después de la propiedad")
            self.advance()
            value = self.parse_expresion()
            if not self.current_token or self.current_token[0] != 'CLOSEP':
                self.error("Se esperaba ) para cerrar Sys.set")
            self.advance()
            return {
                'type': 'sys.set',
                'property': prop,
                'value': value
            }
        else:
            self.error(f"Comando Sys.{command} no reconocido")
        
    def parse_asignacion(self, var_name):

        if not self.current_token or self.current_token[0] != 'ASIGNACION':
            self.error("Se esperaba =")
            self.advance()
            value = self.parse_expresion()
            return {
                'type': 'asignacion',
                'vars': [var_name],
                'value': value
            }

    def parse_use(self):

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaban uno o mas nombres de modulos a importar despues de use")

        modulos = []

        while self.current_token and self.current_token[0] == 'ID':
            modulo = self.current_token[1]
            modulos.append(modulo)
            self.advance()

            if not self.current_token or self.current_token[0] != 'COMA':
                break
            self.advance()

        return {
            'type': 'use',
            'modules': modulos
        }
    
    def parse_object_declaration(self):

        self.advance()

        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un nombre para el objeto")
        obj_name = self.current_token[1]

        initial_line = self.current_token[2]
        initial_col =self.current_token[3]

        self.advance()

        if not self.current_token or self.current_token[0] != 'OPENL':
            self.error(f"Se esperaba {{ después de 'object {obj_name}'")
        self.advance()

        attributes = {}
        while self.current_token and self.current_token[0] != 'CLOSEL':
            if not self.current_token or self.current_token[0] != 'ID':
                self.error("Se esperaba un nombre de atributo")
            attr_name = self.current_token[1]
            attr_fila = self.current_token[2]
            attr_col = self.current_token[3]
            self.advance()

            default_value = {"type": "null"}  # por defecto
            if self.current_token and self.current_token[0] == 'ASIGNACION':
                self.advance()
                if not self.current_token or self.current_token[0] not in ExpresionValues:
                    self.error(f"Se esperaba un valor para el atributo '{attr_name}'")
                default_value = self.parse_expresion()   # ← guardar AST, NO evaluar

            attributes[attr_name] = {
                'value': default_value,
                'fila': attr_fila,
                'columna': attr_col 
            }

            if self.current_token and self.current_token[0] == 'COMA':
                self.advance()
            else:
                break

        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba } para cerrar la definición del objeto")
        end_fila = self.current_token[2]
        end_col = self.current_token[3]
        self.advance()

        return {
            'type': 'object_declaration',
            'name': obj_name,
            'attributes': attributes,
            'fila': initial_line,
            'columna': initial_col,
            'fila_end': end_fila,
            'columna_end': end_col
        }
    
    def parse_object_instantiation(self, name):
        attr_values = {}
        while self.current_token and self.current_token[0] != 'CLOSEL':
            if not self.current_token or self.current_token[0] != 'ID':
                self.error("Se esperaba un nombre de atributo en la inicialización")
            attr_name = self.current_token[1]
            self.advance()
            if not self.current_token or self.current_token[0] != 'ASIGNACION':
                self.error("Se esperaba = después del nombre del atributo")
            self.advance()
            if not self.current_token or self.current_token[0] not in ExpresionValues:
                self.error("Se esperaba un valor para el atributo")
            value = self.parse_expresion()
            attr_values[attr_name] = value
            if self.current_token and self.current_token[0] == 'COMA':
                self.advance()
            else:
                break
        if not self.current_token or self.current_token[0] != 'CLOSEL':
            self.error("Se esperaba } para cerrar la inicialización")
        self.advance()
        return {
            'type': 'object_instantiation',
            'object_name': name,
            'attr_values': attr_values
        }
    
    @DeprecationWarning
    def parse_lvalue(self):
        """Parsea un lvalue: identificador, posiblemente seguido de .atributo o [indice]"""
        if not self.current_token or self.current_token[0] != 'ID':
            self.error("Se esperaba un identificador para el lado izquierdo")
        node = {'type': 'id', 'value': self.current_token[1]}
        self.advance()
        while True:
            if self.current_token and self.current_token[0] == 'PUNTO':
                self.advance()
                if not self.current_token or self.current_token[0] != 'ID':
                    self.error("Se esperaba un identificador después de .")
                attr = self.current_token[1]
                self.advance()
                node = {'type': 'attribute_access', 'object': node, 'attribute': attr}
            elif self.current_token and self.current_token[0] == 'OPENC':
                self.advance()
                index = self.parse_expresion()
                if not self.current_token or self.current_token[0] != 'CLOSEC':
                    self.error("Se esperaba ]")
                self.advance()
                node = {'type': 'access', 'set': node, 'index': index}
            else:
                break
        return node

    def parse_instruccion(self):
        
        if not self.current_token:
            return
        
        elif self.current_token[0] == "IF":
            self.advance()
            return self.parse_conditional()
        
        elif self.current_token[0] == 'WHILE':
            self.advance()
            return self.parse_while()
        
        elif self.current_token[0] == 'USE':
            self.advance()
            return self.parse_use()

        elif self.current_token[0] == 'RETURN' and self.inFunction:
            self.advance()
            return self.parse_return()
        
        elif self.current_token[0] == 'STOP' and self.inBucle > 0:
            self.advance()
            return { "type": "stop" }

        elif self.current_token[0] == 'FUN':
            self.advance()
            return self.parse_fun()
        
        elif self.current_token[0] == 'ID':
            first_id = self.current_token[1]
            fila = self.current_token[2]
            columna = self.current_token[3]
            self.advance()

            # Caso especial: Sys
            if first_id == "Sys":
                return self.parse_sys()

            # Verificar si es llamada a función o declaración: ID ( ... )
            if self.current_token and self.current_token[0] == 'OPENP':
                self.advance()
                args = self.parse_arguments()
                if not self.current_token or self.current_token[0] != 'CLOSEP':
                    self.error("Se esperaba )")
                self.advance()

                # Verificar si es declaración de función (sigue = o def)
                if self.current_token and self.current_token[0] in ('ASIGNACION', 'DEF'):
                    if self.current_token[0] == 'ASIGNACION':
                        self.advance()
                        if self.current_token and self.current_token[0] == 'OPENL':
                            self.advance()
                            return self.parse_parts(first_id, [arg['value'] for arg in args if arg['type'] == 'id'], (fila, columna))
                        else:
                            expr = self.parse_expresion()
                            last_expre_pos = self.pos - 1
                            last_expr_token = self.tokens[last_expre_pos]
                            fila_end = last_expr_token[2]
                            columna_end = last_expr_token[3]
                            return {
                                'type': 'function',
                                'name': first_id,
                                'args': [arg['value'] for arg in args if arg['type'] == 'id'],
                                'expresions': [{
                                    'condition': {'type': 'bool', 'value': True},
                                    'expresion': expr
                                }],
                                'fila': fila,
                                'columna': columna,
                                'fila_end': fila_end,
                                'columna_end': columna_end,
                                'its_parts': False
                            }
                    else:
                        self.error("Sintaxis 'def' aún no implementada")
                else:
                    # Es una llamada normal
                    call_node = {
                        'type': 'call',
                        'callee': {'type': 'id', 'value': first_id},
                        'args': args
                    }
                    # Aplicar postfijos adicionales (posibles [0] o . después de la llamada)
                    final_node = self.parse_postfix(call_node)
                    return {'type': 'expression_statement', 'expression': final_node}

            # Si no es llamada, entonces es una expresión que puede ser lvalue o lista de lvalues
            # Construir el primer lvalue
            base_node = {'type': 'id', 'value': first_id, "fila": fila, "columna": columna}
            node = self.parse_postfix(base_node)  # aplica [ ] y . si los hay
            lvalues = [node]

            # Leer más lvalues si hay coma
            while self.current_token and self.current_token[0] == 'COMA':
                self.advance()
                if not self.current_token or self.current_token[0] != 'ID':
                    self.error("Se esperaba un identificador después de ,")
                next_id = self.current_token[1]
                fila_id = self.current_token[2]
                columna_id = self.current_token[3]
                self.advance()
                next_base = {'type': 'id', 'value': next_id, 'fila': fila_id, 'columna': columna_id}
                next_node = self.parse_postfix(next_base)
                lvalues.append(next_node)

            # Verificar ADD (añadir a conjunto)
            if self.current_token and self.current_token[0] == 'ADD':
                self.advance()
                if len(lvalues) > 1:
                    self.error("Solo se puede añadir a un conjunto a la vez")
                return self.parse_add(lvalues[0])

            # Verificar ASIGNACION
            if self.current_token and self.current_token[0] == 'ASIGNACION':
                self.advance()
                if not self.current_token or self.current_token[0] not in ExpresionValues:
                    self.error("Se esperaba un valor para la asignación")
                value = self.parse_expresion()
                result = {
                    "type": "asignacion",
                    "lvalues": lvalues,
                    "value": value
                }
                return result

            # Si no hay asignación ni ADD, es una expresión suelta
            if len(lvalues) > 1:
                self.error("Expresiones múltiples sin asignación no son válidas")
            return {'type': 'expression_statement', 'expression': lvalues[0]}
            
        elif self.current_token[0] == 'FOREACH':
            self.advance()
            return self.parse_for()
        
        elif self.current_token[0] == 'COPY' and (self.inBucle > 0 or self.inFunction):
            self.advance()
            return self.parse_copy()
        
        elif self.current_token[0] == 'OBJECT':
            return self.parse_object_declaration()

        else:
            self.error(f"{self.current_token[1]} inesperado")

    def parse_program(self):
        
        program = []

        while self.current_token:
            instruccion = self.parse_instruccion()
            program.append(instruccion)

        return {
            "program": program
        }, self.usages, self.mini_scopes