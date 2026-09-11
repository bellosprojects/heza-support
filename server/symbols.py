from lsprotocol.types import (
    DocumentSymbol,
    SymbolKind,
    Range,
    Position
)

SYMBOLS_NODES_TYPE = [
    'object_declaration',
    'fun',
    'function',
    'asignacion'
]

from parser import Parser
from lexer import Lexer
from types_inference import FUNCTION
import os

from scope import generate_scope_from_ast
from types_inference import inferences_type

def get_all_symbols_from_external_module(module_name: str) -> dict[str, set[str]]:

    """
    La ruta no debe incluie el .hz
    """

    symbols : dict[str, set[str]] = {}

    module_name = module_name + ".hz"

    if not os.path.exists(module_name):
        return symbols
    
    try:
    
        file_module = open(module_name, "r", encoding="UTF-8")

        module_source_code = file_module.read()

        module_tokens = Lexer(code=module_source_code).tokenize()

        module_ast, _, miniscopes = Parser(tokens=module_tokens).parse_program()

        module_scope = generate_scope_from_ast(ast=module_ast, mini_scopes=miniscopes)

        instrucciones = module_ast.get('program', [])

        for node in instrucciones:

            if node.get('type') in SYMBOLS_NODES_TYPE:

                if node['type'] == 'object_declaration':

                    object_name = node.get('name', 'ObjetoAnonimo')

                    symbols[object_name] = {f"object[{object_name}]"}

                elif node['type'] in ('fun', 'function'):

                    object_name = node.get('name', 'FuncionAnonima')

                    symbols[object_name] = {FUNCTION}

                elif node['type'] == 'asignacion':

                    vars_ = [lvalue for lvalue in node.get('lvalues', []) if lvalue.get("type", None) == "id"]
                    value = node.get("value", None) if len(vars_) == 1 else None
                    for var in vars_:
                        var_name = var.get("value")
                        if var_name:
                            symbols[var_name] = inferences_type(node=value, scope=module_scope)

    except Exception as e:
        return {"error": e}
        

    return symbols

def get_all_symbols(ast: any) -> list[DocumentSymbol]:

    symbols = []

    for node in ast:

        if node['type'] in SYMBOLS_NODES_TYPE:
            
            node_symbol = _get_symbol_from_node(node=node)

            if node_symbol:

                symbols.append(node_symbol)

    return symbols


def _get_symbol_from_node(node: any) -> DocumentSymbol | None:
    
    if node['type'] == 'object_declaration':
        return _get_symbol_object(node=node)
    
    elif node['type'] == 'fun':
        return _get_symbol_fun(node=node)
    
    elif node['type'] == 'function':
        return _get_symbol_math_function(node=node)
    
    return None

def _get_symbol_object(node: any) -> DocumentSymbol:

    linea = max(0, node['fila'] - 1)
    col_inicio = max(0, node['columna'] - 1)

    fila_end = max(0, node['fila_end'] - 1)
    columna_end = max(0, node['columna_end'] - 1)

    hijos_objeto = []
    for atributo in node['attributes'].keys():

        attr_fila = max(0, node['attributes'][atributo]['fila'] - 1)
        attr_col = max(0, node['attributes'][atributo]['columna'] - 1)

        hijos_objeto.append(
            DocumentSymbol(
                name=atributo,
                kind=SymbolKind.Field,
                range=Range(
                    start=Position(line=attr_fila, character=attr_col),
                    end=Position(line=attr_fila, character=attr_col + len(atributo))
                ),
                selection_range=Range(
                    start=Position(line=attr_fila, character=attr_col),
                    end=Position(line=attr_fila, character=attr_col + len(atributo))
                ),
            )
        )

    simbolo_obj = DocumentSymbol(
        name = node['name'],
        kind=SymbolKind.Object,
        children=hijos_objeto,
        range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=fila_end, character=columna_end)
        ),
        selection_range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=linea, character=col_inicio + len(node['name']))
        )
    )

    return simbolo_obj

def _get_symbol_fun(node: any) -> DocumentSymbol:

    linea = max(0, node['fila'] - 1)
    col_inicio = max(0, node['columna'] - 1)

    fila_end = max(0, node['fila_end'] - 1)
    columna_end = max(0, node['columna_end'] - 1)

    inter_symbols = get_all_symbols(ast=node['body'])

    simbolo_obj = DocumentSymbol(
        name=f"{node['name']} ({', '.join(node['params'])})",
        kind=SymbolKind.Function,
        children=inter_symbols,
        range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=fila_end, character=columna_end)
        ),
        selection_range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=linea, character=col_inicio + len(node['name']))
        )
    )

    return simbolo_obj

def _get_symbol_math_function(node: any) -> DocumentSymbol:
    
    linea = max(0, node['fila'] - 1)
    col_inicio = max(0, node['columna'] - 1)

    fila_end = max(0, node['fila_end'] - 1)
    columna_end = max(0, node['columna_end'] - 1)

    simbolo_obj = DocumentSymbol(
        name=f"{node['name']} ({', '.join(node['args'])})",
        kind=SymbolKind.Enum if node['its_parts'] else SymbolKind.Function,
        range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=fila_end, character=columna_end)
        ),
        selection_range=Range(
            start=Position(line=linea, character=col_inicio),
            end=Position(line=linea, character=col_inicio + len(node['name']))
        )
    )

    return simbolo_obj