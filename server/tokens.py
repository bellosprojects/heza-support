tokens = [

    #palabras
    ('ID', r'[a-zA-Z_]\w*'),

    #Signos
    ('ADD', r'←'),
    ('THEN', r'→'),
    ('IN', r'∈'),
    ('NOTIN', r'∉'),
    ('DEL', r'\\'),
    ('AND', r'∧'),
    ('OR', r'∨'),
    ('NOT', r'¬'),
    ('SQRT', r'√'),
    ('NULL', r'∅'),
    ('FOREACH', r'∀'),
    ('EXIST', r'∃'),
    ('SUBJET', r'⊂'),
    ('DIFFERENT', r'≠'),
    ('SUMMATION', r'∑'),
    ('PRODUCTION', r'∏'),
    ('INFINITE', r'∞'),
    ('INDETERMINATE', r'∄'),
    ('PARTIAL', r'∂'),
    ('INTEGRAL', r'∫'),
    ('UNION', r'∪'),
    ('INTERSECTION', r'⋂'),
    ('SIMETRIC_DIFFERENCE', r'Δ'),
    ('NABLA', r'∇'),
    ('CROSS', r'⨉'),
    
    #Patrones
    ('NUMBER', r'\d+(\.\d+)?'),
    ('TEXT', r'"([^"]*)"'),
    ('EXPRESION', r"'([^']*)'"),

    #\t \n ESP
    ('IGNORAR', r'\s'),

    #Comentarios
    ('COMENTARIO', r'~(.*)'),

    #Operadores
    ('COMPARACION', r'=='),
    ('ASIGNACION', r'='),
    ('MAYORE',r'>='),
    ('MENORE',r'<='),
    ('PIPE', r'>>'),
    ('UNPIPE', r'<<'),
    #('Q', r'\?'),
    #('DOUBLEEXC', r'!!'),
    ('EXC', r'!'),
    ('MENOR',r'<'),
    ('MAYOR',r'>'),
    ('SUMA',r'\+'),
    ('RESTA',r'-'),
    ('MULTIPLICACION',r'\*'),
    ('DIVISION',r'/'),
    ('MOD',r'%'),
    ('POW',r'\^'),
    ('DPUNTO', r'\.\.'),
    ('PUNTO', r'\.'),
    ('COMA', r','),
    ('ARROBA', r'@'),
    ('REFERENCE', r'&'),
    ('DOUBLE', r':'),
    ('OPENP', r'\('),
    ('CLOSEP', r'\)'),
    ('OPENC', r'\['),
    ('CLOSEC', r'\]'), 
    ('OPENL', r'\{'),
    ('CLOSEL', r'\}'),
    #('DOLLAR', r'\$'),
    ('BARRA', r'\|') 
]

ExpresionValues = [
    'ID',
    'TEXT',
    'NUMBER',
    'ESP',
    'LINE',
    'TAB',
    'FALSE',
    'TRUE',
    'OPENP',
    'OPENC',
    'RESTA',
    'SUMA',
    'NOT',
    'TRACE',
    'SQRT',
    'SUMMATION',
    'NULL',
    'BARRA',
    'EXC',
    'OPENL',
    'FOREACH',
    'EXIST',
    'INFINITE',
    'PRODUCTION',
    'EXPRESION',
    'DERIVATIVE',
    'INTEGRAL',
    'REFERENCE',
    'INDETERMINATE',
    'LINE',
    'ARROBA',
    'IF'
]

#palabras clave
keyword = [
    'if',
    'else',
    'return',
    'while',
    'use',
    'copy',
    'fun',
    'do',
    'stop',
    'object'
]

#Constantes
constant = [
    'true',
    'false'
]