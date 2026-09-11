from typing import Dict
import traceback
from pygls.lsp.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_SIGNATURE_HELP,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticTag,
    Range,
    Position,
    ShowMessageParams,
    MessageType,
    PublishDiagnosticsParams,
    DocumentSymbolParams,
    LogMessageParams,
    CompletionParams,
    CompletionItem,
    CompletionItemLabelDetails,
    CompletionList,
    CompletionItemKind,
    CompletionOptions,
    InsertTextFormat,
    SemanticTokens,
    SemanticTokensLegend,
    SemanticTokensParams,
    SemanticTokensRegistrationOptions,
    Location,
    DefinitionParams,
    SignatureHelp,
    SignatureInformation,
    ParameterInformation,
    SignatureHelpOptions,
    SignatureHelpParams
)



server = LanguageServer("heza-server", "v0.1")

from parser import Parser, ParserError
from lexer import Lexer, LexerError, get_all_id_tokens
from symbols import get_all_symbols, get_all_symbols_from_external_module
from scope import generate_scope_from_ast
from types_inference import inferences_type, TYPE_CACHE

HEZA_GLOBAL_CACHE : Dict[str, Dict] = {}

def _get_ast(source_code: str, uri):
    tokens = Lexer(code=source_code).tokenize()
    ast, usages, mini_scopes = Parser(tokens=tokens).parse_program()

    TYPE_CACHE.clear()
    scope = generate_scope_from_ast(ast=ast['program'], mini_scopes=mini_scopes)

    HEZA_GLOBAL_CACHE[uri] = {
        "scope": scope,
        "usages": usages
    }

    return ast

def validar_codigo(ls: LanguageServer, params):
    
    uri = params.text_document.uri
    text_doc = ls.workspace.get_text_document(uri)
    codigo_fuente = text_doc.source
    diagnostics = []
    
    try:
        # Intentamos parsear
        _ = _get_ast(source_code=codigo_fuente, uri=uri)
        file_info = HEZA_GLOBAL_CACHE.get(uri)

        if not file_info:
            return

        if file_info:
            scope = file_info['scope']
            usages = file_info['usages']
            declaraciones_usadas = set()

            for use in usages:

                try:

                    fila = use['fila']
                    columna = use['columna']
                    nombre = use['name']

                    actual_scope = scope.buscar_scope(row=fila, col=columna)
                    
                    existe = False
                    usado_antes_de_declarar = False

                    # Subimos por la cadena de scopes (burbujeo)
                    while actual_scope is not None:
                        simbolos = actual_scope.obtener_simbolos_locales()

                        # 1. Verificación si es una Variable
                        if nombre in simbolos['variables']:
                            existe = True
                            node_declaration = simbolos['variables'][nombre] # <-- CORREGIDO: 'variables' en plural

                            if node_declaration and "fila" in node_declaration:
                                fila_decl = node_declaration["fila"]
                                col_decl = node_declaration.get("columna", 1)

                                # COMPARACIÓN CRONOLÓGICA DE RANGOS
                                # Si la declaración ocurre en una línea posterior, o en la misma línea pero más adelante...
                                if fila_decl > fila or (fila_decl == fila and col_decl >= columna):
                                    usado_antes_de_declarar = True
                                else:
                                    # Si es una posición válida, la marcamos como usada para el linter de "no usadas"
                                    declaraciones_usadas.add((fila_decl, col_decl))
                            else:
                                # Si no tiene fila (como los parámetros de funciones), es válido en todo el scope
                                pass
                            break

                        # 2. Verificación si es una Función u Objeto
                        # Nota: Si tu lenguaje permite "Hoisting" (usar funciones antes de declararlas),
                        # las dejamos pasar directamente. Si no, aplicarías la misma lógica de arriba.
                        elif nombre in simbolos['funciones'] or nombre in simbolos['objetos']:
                            existe = True
                            break

                        actual_scope = actual_scope.parent

                    # --- GENERACIÓN DE DIAGNÓSTICOS SEGÚN EL CASO ---
                    linea_vscode = fila - 1
                    col_vscode = max(0, columna - 1)
                    rango = Range(
                        start=Position(line=linea_vscode, character=col_vscode),
                        end=Position(line=linea_vscode, character=col_vscode + len(nombre))
                    )

                    if not existe:
                        # Caso A: El identificador literalmente no existe en ningún lado
                        diagnostico = Diagnostic(
                            range=rango,
                            message=f"El identificador '{nombre}' no esta declarado en este scope.",
                            severity=DiagnosticSeverity.Warning,
                            source="Heza Analyzer"
                        )
                        diagnostics.append(diagnostico)

                    elif usado_antes_de_declarar:
                        # Caso B: Existe, pero intentaste acceder a él antes de tiempo
                        diagnostico = Diagnostic(
                            range=rango,
                            message=f"Error de tiempo de ejecucion: La variable '{nombre}' se usa antes de ser asignada.",
                            severity=DiagnosticSeverity.Error, # <-- Esto es un Error crítico, no una advertencia
                            source="Heza Analyzer"
                        )
                        diagnostics.append(diagnostico)

                except Exception as token_error:

                    ls.window_log_message(LogMessageParams(
                        type=MessageType.Log,
                        message=f"Error procesando el token '{nombre}' en linea {fila}: {str(traceback.format_exc())}"
                    ))


        # 2. Revisión de variables no usadas (Fijamos la llave a 2 elementos)
        def revisar_variables_no_usadas(scope_):
            simbolos_locales = scope_.obtener_simbolos_locales()
            for nombre_var, nodo_var in simbolos_locales['variables'].items():
                if nodo_var and "fila" in nodo_var:
                    fila_decl, col_decl = nodo_var['fila'], nodo_var.get('columna', 1)
                    # CORRECCIÓN: Ahora coincide la estructura de la tupla
                    if (fila_decl, col_decl) not in declaraciones_usadas:
                        linea_vscode, col_vscode = fila_decl - 1, max(0, col_decl - 1)
                        diagnostics.append(Diagnostic(
                            range=Range(start=Position(line=linea_vscode, character=col_vscode),
                                        end=Position(line=linea_vscode, character=col_vscode + len(nombre_var))),
                            message=f"La variable '{nombre_var}' está declarada pero nunca se lee.",
                            severity=DiagnosticSeverity.Warning,
                            tags=[DiagnosticTag.Unnecessary],
                            source="Heza Linter"
                        ))
            for hijo in scope_.children:
                revisar_variables_no_usadas(hijo)

        revisar_variables_no_usadas(scope)

    except (LexerError, ParserError) as e:
        # Manejo específico de errores de sintaxis/léxicos
        diagnostics.append(Diagnostic(
            range=Range(start=Position(line=max(0, e.fila - 1), character=max(0, e.columna - 1)),
                        end=Position(line=max(0, e.fila - 1), character=max(0, e.columna))),
            message=e.mensaje,
            source="HezaParser"
        ))
    except Exception as e:
        # Loguear el error real en la salida del servidor para saber qué está pasando
        ls.window_log_message(LogMessageParams(type=MessageType.Error, message=f"Error en validación: {traceback.format_exc()}"))

    # Siempre publicamos, aunque la lista esté vacía (esto limpia los errores anteriores)
    ls.text_document_publish_diagnostics(PublishDiagnosticsParams(uri=text_doc.uri, diagnostics=diagnostics))

@server.feature(TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=['.', '"', '{', ',']))
def proveer_autocompletado(ls: LanguageServer, params: CompletionParams):

    row = params.position.line + 1
    col = params.position.character + 1

    uri = params.text_document.uri
    document = ls.workspace.get_text_document(uri)

    file_info = HEZA_GLOBAL_CACHE.get(uri)
    
    if file_info:
        global_scope = file_info['scope']

    if not file_info:
        return
    
    scope_actual = global_scope.buscar_scope(row=row, col=col) if global_scope else None
    simbolos = scope_actual.obtener_simbolos_visibles() if scope_actual else {'variables': {}, 'funciones': {}, 'objetos': {}}

    items = []

    linea_texto = document.lines[row - 1]
    linea_hasta_cursor_raw = linea_texto[:col - 1]
    text_hasta_cursor = linea_hasta_cursor_raw.strip()

    import re
    import os
    from urllib.parse import urlparse, unquote
    from lsprotocol.types import CompletionItemLabelDetails, TextEdit, Range, Position

    # =========================================================================
    # EXTRACTOR DE RUTAS BASE (Centralizado para evitar sugerir el propio archivo)
    # =========================================================================
    parsed_uri = urlparse(uri)
    nombre_archivo_actual = os.path.basename(unquote(parsed_uri.path))
    base_dir = os.path.dirname(unquote(parsed_uri.path))
    if base_dir.startswith('/') and os.name == 'nt':
        base_dir = base_dir[1:] # Fix para rutas en Windows

    # =========================================================================
    # CONTEXTO A: Autocompletado de Rutas de Archivos (use "..." o from "...")
    # =========================================================================
    match_path = re.search(r'(?:use|from)\s+"([^"]*)$', linea_hasta_cursor_raw)
    if match_path:
        path_typed = match_path.group(1) # Ej: "modulos/util" o ""
        
        # Separamos el directorio base del prefijo que está escribiendo el usuario
        dir_part = os.path.dirname(path_typed)
        target_dir = os.path.abspath(os.path.join(base_dir, dir_part))

        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            try:
                for entry in os.listdir(target_dir):
                    # CORRECCIÓN: Ignoramos archivos ocultos Y el propio archivo actual
                    if entry.startswith('.') or entry == nombre_archivo_actual: 
                        continue
                        
                    full_entry_path = os.path.join(target_dir, entry)
                    
                    if os.path.isdir(full_entry_path):
                        items.append(CompletionItem(
                            label=entry,
                            kind=CompletionItemKind.Folder,
                            detail="Carpeta de módulos"
                        ))
                    elif entry.endswith('.hz'):
                        items.append(CompletionItem(
                            label=entry.split('.hz')[0],
                            kind=CompletionItemKind.Module,
                            detail="Módulo Heza"
                        ))
            except Exception:
                pass
                
        return CompletionList(is_incomplete=False, items=items)

    # =========================================================================
    # CONTEXTO B: Autocompletado de Símbolos Selectivos ({ symbol1, ... })
    # =========================================================================
    match_braces = re.search(r'use\s*\{([^}]*)$', linea_hasta_cursor_raw)
    if match_braces:
        # Buscamos en toda la línea si ya existe la cláusula 'from "modulo"'
        match_from = re.search(r'from\s+"([^"]+)"', linea_texto)
        
        if match_from:
            # -----------------------------------------------------------------
            # Caso B1: El usuario ya especificó el módulo al final
            # -----------------------------------------------------------------
            modulo_relativo = match_from.group(1)
            try:
                simbolos_modulo = get_all_symbols_from_external_module(modulo_relativo) 
                for sym_name, sym_type in simbolos_modulo.items():
                    items.append(CompletionItem(
                        label=sym_name,
                        kind=CompletionItemKind.Field,
                        detail=f"Módulo: {modulo_relativo}",
                        label_details=CompletionItemLabelDetails(
                            description=" | ".join(sym_type)
                        )
                    ))
            except Exception:
                pass
        else:
            # -----------------------------------------------------------------
            # Caso B2: NO hay módulo aún -> Escaneo recursivo (Estilo TypeScript)
            # -----------------------------------------------------------------
            try:
                # Caminamos por el directorio actual y todas sus subcarpetas
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        # Solo procesamos otros archivos .hz (evitando el propio archivo)
                        if file.endswith('.hz') and file != nombre_archivo_actual:
                            full_file_path = os.path.join(root, file)
                            
                            # Calculamos la ruta relativa respecto a donde está el usuario
                            rel_path = os.path.relpath(full_file_path, base_dir)
                            # Normalizamos barras de Windows a barras de importación / y quitamos extensión
                            rel_path_clean = rel_path.replace('\\', '/').rsplit('.hz', 1)[0]
                            
                            # Construimos el prefijo relativo limpio (ej: "./math" o "./utils/format")
                            modulo_relativo = f"./{rel_path_clean}"
                            
                            # Obtenemos el diccionario { nombre: tipo } usando tu función
                            simbolos_modulo = get_all_symbols_from_external_module(modulo_relativo)
                            
                            for sym_name, sym_type in simbolos_modulo.items():
                                items.append(CompletionItem(
                                    label=sym_name,
                                    kind=CompletionItemKind.Field,
                                    detail=f"Auto-importar desde {modulo_relativo}",
                                    label_details=CompletionItemLabelDetails(
                                        description=" | ".join(sym_type)
                                    ),
                                    # EL TRUCO: Modificamos el texto desde el cursor hasta el fin de la línea actual
                                    text_edit=TextEdit(
                                        range=Range(
                                            start=Position(line=row - 1, character=col - 1),
                                            end=Position(line=row - 1, character=len(linea_texto))
                                        ),
                                        # Inserta el símbolo, cierra la llave y escribe el origen automáticamente
                                        new_text=f"{sym_name} }} from \"{modulo_relativo}\""
                                    )
                                ))
            except Exception:
                pass
                
        return CompletionList(is_incomplete=False, items=items)

    # =========================================================================
    # CONTEXTO C: Acceso a Atributos Aninados (obj.attr1.attr2)
    # =========================================================================
    if text_hasta_cursor.endswith('.') and scope_actual:
        match = re.search(r'([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\.$', text_hasta_cursor)
        if match:
            cadena_completa = match.group(1)
            partes = cadena_completa.split('.')

            base_name = partes[0]
            current_types = inferences_type({"type": "id", "value": base_name}, scope_actual)
            error_en_cadena = False

            for attr_name in partes[1:]:
                next_types = set()
                for t in current_types:
                    m = re.search(r'^object\[([a-zA-Z_]\w*)\]$', t)
                    if m:
                        class_name = m.group(1)
                        
                        # CAMBIO 1: Búsqueda profunda de la definición del objeto intermedio
                        obj_def = scope_actual.buscar_objeto_definicion(class_name)
                        if obj_def and isinstance(obj_def, dict):
                            atributos = obj_def.get('attributes', {})
                            if attr_name in atributos:
                                attr_node = atributos[attr_name].get('value') if isinstance(atributos[attr_name], dict) else atributos[attr_name]
                                tipos_atributo = inferences_type(attr_node, scope_actual)
                                next_types = next_types.union(tipos_atributo)
                if not next_types:
                    error_en_cadena = True
                    break
                current_types = next_types

            if not error_en_cadena:
                for t in current_types:
                    m = re.search(r'^object\[([a-zA-Z_]\w*)\]$', t)
                    if m:
                        class_name = m.group(1)
                        
                        # CAMBIO 2: Búsqueda profunda para obtener el objeto final y listar sus miembros
                        obj_def = scope_actual.buscar_objeto_definicion(class_name)
                        if obj_def and isinstance(obj_def, dict):
                            atributos = obj_def.get('attributes', {})

                            for final_attr_name, attr_info in atributos.items():
                                nodo_atributo = attr_info.get('value') if isinstance(attr_info, dict) else attr_info
                                tipos_inf = inferences_type(nodo_atributo, scope_actual)
                                tipo_renderizado = " | ".join(tipos_inf)

                                items.append(CompletionItem(
                                    label=final_attr_name,
                                    kind=CompletionItemKind.Property,
                                    detail=f": {tipo_renderizado}",
                                    label_details=CompletionItemLabelDetails(
                                        description=f"de {class_name}"
                                    )
                                ))
        return CompletionList(is_incomplete=False, items=items)

    # =========================================================================
    # CONTEXTO D: Ámbito General (Variables, Funciones y Objetos locales/globales)
    # =========================================================================
    elif scope_actual:
        for var_name in simbolos["variables"]:
            items.append(CompletionItem(
                label=var_name,
                kind=CompletionItemKind.Variable,
                detail=f"Variable: { ' | '.join(inferences_type(simbolos['variables'][var_name].get('value'), scope_actual)) }"
            ))
            
        for func_name, func_node in simbolos["funciones"].items():
            params = func_node.get('params', func_node.get('args', []))
            params_str = ", ".join(params)
            snippet_args = ", ".join([f"${{{i+1}:{p}}}" for i, p in enumerate(params)])
            
            items.append(CompletionItem(
                label=func_name,
                kind=CompletionItemKind.Function,
                detail=f"fun {func_name}({params_str})",
                insert_text=f"{func_name}({snippet_args})",
                insert_text_format=InsertTextFormat.Snippet
            ))
            
        for obj_name, obj_node in simbolos["objetos"].items():
            atributos = obj_node.get('attributes', {})
            attr_names = list(atributos.keys())
            attr_str = ",\n".join([f"\t{p} = ${{{i+1}:{p}}}" for i, p in enumerate(attr_names)])
            
            items.append(CompletionItem(
                label=obj_name,
                kind=CompletionItemKind.Class,
                detail=f"object: {obj_name}",
                documentation=f"Atributos:\n- " + "\n- ".join(attr_names) if attr_names else "Sin atributos",
                insert_text=obj_name + (" {\n" + attr_str + "\n}" if len(attr_names) > 0 else ""),
                insert_text_format=InsertTextFormat.Snippet
            ))

    return CompletionList(is_incomplete=False, items=items)

@server.feature(TEXT_DOCUMENT_SIGNATURE_HELP, SignatureHelpOptions(trigger_characters=['(', ',']))
def proveer_ayuda_firma(ls: LanguageServer, params: SignatureHelpParams):

    uri = params.text_document.uri
    document = ls.workspace.get_text_document(uri)

    fila = params.position.line
    columna = params.position.character

    linea = document.lines[fila]

    texto_hasta_cursor = linea[:columna].strip()

    if not texto_hasta_cursor:
        return None

    import re

    match = re.search(r'([a-zA-Z_]\w*)\s*\(([^)]*)$', texto_hasta_cursor)

    if not match: return None

    nombre_funcion = match.group(1)
    argumentos_escritos = match.group(2)

    parametro_activo = argumentos_escritos.count(",")

    global_scope = HEZA_GLOBAL_CACHE.get(uri).get("scope")

    if not global_scope:
        return None
    
    scope_actual = global_scope.buscar_scope(row=fila + 1, col = columna + 1)
    simbolos = scope_actual.obtener_simbolos_visibles()

    if nombre_funcion not in simbolos['funciones']:
        return None
    
    node_func = simbolos['funciones'][nombre_funcion]
    parametros = node_func.get('params', node_func.get('args', []))

    total_params = len(parametros)
    if total_params > 0:
        parametro_activo = min(argumentos_escritos.count(","), total_params - 1)
    else:
        parametro_activo = 0

    firma_str = f"{nombre_funcion}("
    parametros_info = []

    for i, p in enumerate(parametros):
        inicio_idx = len(firma_str)
        firma_str += p
        fin_idx = len(firma_str)

        parametros_info.append(
            ParameterInformation(
                label=(inicio_idx, fin_idx)
            )
        )

        if i < total_params - 1:
            firma_str += ", "

    firma_str += ")"

    docstring_texto = ""

    if 'docstring' in node_func:
        docstring_texto = node_func['docstring']

    elif 'fila' in node_func:
        docstring_texto = extraer_docstring(document.source,  node_func['fila'])

    firma_info = SignatureInformation(
        label=firma_str,
        parameters=parametros_info,
        active_parameter=parametro_activo,
        documentation=MarkupContent(
            kind=MarkupKind.Markdown,
            value=docstring_texto if docstring_texto else f"Firma de la funcion '{nombre_funcion}'"
        )
    )

    return SignatureHelp(
        signatures=[firma_info],
        active_signature=0,
        active_parameter=parametro_activo
    )

@server.feature(TEXT_DOCUMENT_DEFINITION)
def proveer_definicion(ls: LanguageServer, params: DefinitionParams):

    uri = params.text_document.uri
    document = ls.workspace.get_text_document(uri)
    
    # Extraemos la palabra sobre la que el usuario hizo Ctrl+Click o pulsó F12
    palabra_bajo_cursor = document.word_at_position(params.position)
    if not palabra_bajo_cursor:
        return None
    
    row = params.position.line + 1
    col = params.position.character + 1
    
    global_scope = HEZA_GLOBAL_CACHE.get(uri)['scope']
    if not global_scope: 
        return None
        
    scope_actual = global_scope.buscar_scope(row=row, col=col)
    simbolos = scope_actual.obtener_simbolos_visibles()

    nodo_destino = None

    if palabra_bajo_cursor in simbolos["funciones"]:
        nodo_destino = simbolos["funciones"][palabra_bajo_cursor]
        
    # 2. ¿Es un objeto/clase?
    elif palabra_bajo_cursor in simbolos["objetos"]:
        nodo_destino = simbolos["objetos"][palabra_bajo_cursor]
        
    # 4. ¿Es una variable local/global normal?
    elif palabra_bajo_cursor in simbolos["variables"]:
        nodo_destino = simbolos["variables"][palabra_bajo_cursor]

    # Si encontramos el nodo en nuestro mapa de símbolos, calculamos la locación
    if nodo_destino and "fila" in nodo_destino:
        # OJO: Tu AST usa base-1, pero VS Code/LSP necesita base-0 para las líneas
        linea_def = nodo_destino["fila"] - 1
        
        # Si guardas la columna úsala, si no, por ahora podemos usar 0
        col_def = nodo_destino.get("columna", 1) - 1 
        if col_def < 0: 
            col_def = 0

        # Creamos el rango donde se va a posicionar el cursor al saltar
        rango_destino = Range(
            start=Position(line=linea_def, character=col_def),
            end=Position(line=linea_def, character=col_def + len(palabra_bajo_cursor))
        )
        
        # Devolvemos la localización exacta
        return Location(uri=uri, range=rango_destino)

    return None

def extraer_docstring(source_code: str, linea_declaracion: int, simbolo='~') -> str:
    lineas = source_code.splitlines()
    docstring = []
    
    # linea_declaracion suele venir en base-1 del AST. 
    # Para leer la línea ANTERIOR a la declaración en un array base-0:
    idx = linea_declaracion - 2 
    
    while idx >= 0:
        linea = lineas[idx].strip()
        
        # Si la línea es un comentario, la guardamos
        if linea.startswith(simbolo):
            texto_limpio = linea[len(simbolo):].strip()
            docstring.insert(0, texto_limpio) # Insertamos al principio para mantener el orden
            idx -= 1
        # Si chocamos con otra cosa (código), significa que terminó el docstring
        else:
            break
            
    return "\n".join(docstring) if docstring else ""

@server.feature(TEXT_DOCUMENT_HOVER)
def proveer_hover(ls: LanguageServer, params: HoverParams):
    uri = params.text_document.uri
    document = ls.workspace.get_text_document(uri)
    source_code = document.source

    palabra_bajo_cursor = document.word_at_position(params.position)

    if not palabra_bajo_cursor:
        return None
    
    row = params.position.line + 1
    col = params.position.character + 1
    
    file_info = HEZA_GLOBAL_CACHE.get(uri)
    
    if file_info:
        global_scope = file_info['scope']
    if not global_scope: return None

    scope_actual = global_scope.buscar_scope(row=row, col=col)
    simbolos = scope_actual.obtener_simbolos_visibles()

    markdown_result = ""

    if palabra_bajo_cursor in simbolos["funciones"]:
        nodo_func = simbolos["funciones"][palabra_bajo_cursor]
        params_str = ", ".join(nodo_func.get('params', nodo_func.get('args', [])))
        
        markdown_result = f"```heza\nfun {palabra_bajo_cursor}({params_str})\n```\n"
        
        if 'docstring' in nodo_func:
            doc = nodo_func['docstring']
            markdown_result += f"---\n{doc}"

        elif 'fila' in nodo_func: 
            doc = extraer_docstring(source_code, nodo_func['fila'])
            if doc:
                markdown_result += f"---\n{doc}"

    elif palabra_bajo_cursor in simbolos["objetos"]:
        nodo_obj = simbolos["objetos"][palabra_bajo_cursor]
        markdown_result = f"```heza\nobject {palabra_bajo_cursor}\n```\n"
        
        if 'docstring' in nodo_obj:
            doc = nodo_obj['docstring']
            markdown_result += f"---\n{doc}"
        elif 'fila' in nodo_obj:
            doc = extraer_docstring(source_code, nodo_obj['fila'])
            if doc:
                markdown_result += f"---\n{doc}"

    elif palabra_bajo_cursor in simbolos["variables"]:
        markdown_result = f"#### Variable local: `{palabra_bajo_cursor}` \n\n```heza\n{" | ".join(inferences_type(simbolos['variables'][palabra_bajo_cursor].get('value'), scope=scope_actual))}\n```\n"

    if markdown_result:
        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=markdown_result
            )
        )

TOKENS_TYPES = ['variable', 'function', 'class', 'property', 'parameter']
TOKENS_MODIFIERS = ['declaration', 'definition']

leyenda_semantica = SemanticTokensLegend(
    token_types=TOKENS_TYPES,
    token_modifiers=TOKENS_MODIFIERS
)

@server.feature(TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, SemanticTokensRegistrationOptions(legend=leyenda_semantica, full=True))
def proveer_resaltado_semantico(ls: LanguageServer, params: SemanticTokensParams):

    uri = params.text_document.uri
    source_code = ls.workspace.get_text_document(uri).source

    tokens = []

    try:

        tokens = Lexer(code=source_code).tokenize()

    except Exception as _:
        pass

    identificadores = get_all_id_tokens(tokens=tokens)

    data = []
    linea_anterior = 0
    col_anterior = 0

    file_info = HEZA_GLOBAL_CACHE.get(uri)

    if file_info:
        
        global_scope = file_info['scope']


        for _, nombre, fila, col in identificadores:

            linea_actual = fila - 1
            col_actual = col - 1
            longitud = len(nombre)

            scope_actual = global_scope.buscar_scope(row=linea_actual + 1, col=col_actual + 1)
            if not scope_actual:
                scope_actual = global_scope

            simbolos = scope_actual.obtener_simbolos_visibles()
            tipo_token = -1

            if nombre in simbolos["funciones"]:
                tipo_token = TOKENS_TYPES.index('function')
            elif nombre in simbolos["objetos"]:
                tipo_token = TOKENS_TYPES.index('class')
            elif nombre in simbolos["variables"]:
                tipo_token = TOKENS_TYPES.index('variable')

            if tipo_token != -1:
                delta_linea = linea_actual - linea_anterior

                if delta_linea > 0:
                    delta_col = col_actual
                else:
                    delta_col = col_actual - col_anterior

                data.extend([delta_linea, delta_col, longitud, tipo_token, 0])

                linea_anterior = linea_actual
                col_anterior = col_actual

    return SemanticTokens(data=data)

@server.feature(TEXT_DOCUMENT_DID_OPEN)
def al_abrir(ls, params):
    validar_codigo(ls, params)

@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def al_escribir(ls, params):
    validar_codigo(ls, params)

@server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def al_pedir_simbolos(ls: LanguageServer, params: DocumentSymbolParams):
    symbols = []

    try:
        uri = params.text_document.uri
        text_doc = ls.workspace.get_text_document(uri)
        codigo_fuente = text_doc.source

        ast = _get_ast(source_code=codigo_fuente, uri=uri)['program']

        symbols = get_all_symbols(ast=ast)

        return symbols
    
    except (ParserError, LexerError) as _:
        pass

    except Exception as e:
        import traceback

        ls.window_log_message(
            LogMessageParams(
                type=MessageType.Log,
                message=f"Error en Outline: {str(e)}\n{traceback.format_exc()}"
            )
        )

        return []

if __name__ == '__main__':
    server.start_io()