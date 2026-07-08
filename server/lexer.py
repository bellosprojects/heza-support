from tokens import tokens, keyword, constant
import re

class LexerError(Exception):
    
    """
    Excepción personalizada para errores léxicos en Heza.

    Atributos:
        mensaje (str): Descripción del error.
        fila (int): Línea donde ocurrió el error.
        columna (int): Columna donde ocurrió el error.
    """

    def __init__(self, mensaje, fila=None, columna=None):
        self.mensaje = mensaje
        self.fila = fila
        self.columna = columna

    def __str__(self) -> str:
        if self.fila is not None and self.columna is not None:
            return f"[Error léxico]: {self.mensaje} (línea {self.fila}, columna {self.columna})"
        return f"[Error léxico]: {self.mensaje}"
    
    def __repr__(self) -> str:
        return self.__str__()

class Lexer:

    """
    Analizador léxico para el lenguaje Heza.

    Convierte el código fuente en una lista de tokens, cada uno con su tipo, valor, 
    fila y columna de aparición. Reconoce palabras clave, constantes, operadores, 
    identificadores y literales, y reporta errores léxicos con información precisa 
    de ubicación.

    Atributos:
        code (str): Código fuente a analizar.
        pos (int): Posición actual en el código.
        tokens_result (list): Lista de tokens generados.
        fila (int): Número de línea actual.
        columna (int): Número de columna actual.
    """

    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.tokens_result = []
        self.fila = 1
        self.columna = 1

    def tokenize(self) -> list:

        """
        Analiza el código fuente y genera una lista de tokens.

        Cada token es una tupla (tipo, valor, fila, columna). Si se encuentra un 
        carácter desconocido, lanza una excepción LexerError con información de 
        línea y columna.

        Returns:
            list: Lista de tokens reconocidos en el código fuente.

        Raises:
            LexerError: Si se encuentra un carácter no reconocido.
        """

        while self.pos < len(self.code):
            for token, patron in tokens:
                regex = re.compile(patron)
                match = regex.match(self.code, self.pos)
                if match:
                    valor = match.group()

                    fila = self.fila
                    columna = self.columna

                    lineas = valor.count('\n')
                    if lineas > 0:
                        self.fila += lineas
                        self.columna = len(valor.split('\n')[-1]) + 1
                    else:
                        self.columna += len(valor)

                    if token == 'NUMBER':
                        valor = int(float(valor)) if float(valor) % 1 == 0.0 else float(valor)
                    elif token == 'TEXT' or token == 'EXPRESION':
                        valor = valor[1:-1]
                    if token == 'ID':
                        if valor in keyword or valor in constant:
                            token = valor.upper()

                    if token not in ['IGNORAR', 'COMENTARIO']:
                        self.tokens_result.append((token, valor, fila, columna))
                    self.pos = match.end()
                    break
            else:
                raise LexerError(
                    f"Token desconocido '{self.code[self.pos]}'",
                    self.fila,
                    self.columna
                )
            
        return self.tokens_result
    
def get_all_id_tokens(tokens: list) -> list:

    return [token for token in tokens if token[0] == 'ID']