# Heza Language Support

**Soporte oficial para el lenguaje de programación Heza en Visual Studio Code.**

Heza es un lenguaje de programación de alto nivel que integra notación matemática nativa, diseñado para facilitar la expresión de algoritmos, modelos matemáticos y operaciones simbólicas. Esta extensión proporciona un entorno de desarrollo completo (LSP) con análisis estático, autocompletado inteligente, navegación y resaltado semántico, todo integrado en VS Code.

---

## ✨ Características

### 🔍 Análisis semántico y diagnóstico
- **Validación en tiempo real**: errores léxicos, sintácticos y de uso de variables no declaradas o no leídas.
- **Resaltado semántico** de identificadores (variables, funciones, objetos, parámetros).
- **Detección de variables no utilizadas** (advertencias) y uso antes de declaración (errores).

### 🧠 Inteligencia contextual (LSP)
- **Autocompletado** de:
  - Símbolos locales y globales (variables, funciones, objetos).
  - Atributos de objetos en cadenas anidadas (`obj.attr.subattr`).
  - Módulos y rutas de archivos en sentencias `use` y `from`.
  - Símbolos exportados de otros módulos (con importación selectiva).
- **Definición**: navegación rápida a la declaración de funciones, objetos y variables (`Ctrl+Click` / `F12`).
- **Hover**: información detallada sobre símbolos (tipo, firma, docstring extraído de comentarios).
- **Ayuda de firma**: muestra parámetros y documentación al escribir llamadas a funciones.

### 📐 Sintaxis matemática nativa
Heza permite escribir expresiones con operadores y símbolos Unicode comunes en matemáticas:

- `∑`, `∏`, `∫`, `∂`, `lim`, `∀`, `∃`, `∈`, `∉`, `∪`, `∩`, `→`, `¬`, `∧`, `∨`, etc.
- Operadores aritméticos: `+`, `-`, `*`, `/`, `%`, `^`, `√`, `!` (factorial).
- Comparadores: `==`, `≠`, `>`, `<`, `≥`, `≤`.
- Coerción de tipos: `>>`.
- Referencias perezosas: `&`.
- Expresiones simbólicas entre comillas simples: `'x^2 + 3'`.

### 🧩 Estructuras de datos y control
- **Conjuntos** `{ ... }`, **tuplas** `( ... )`, **rangos** `[from, to, step]`.
- **Transformaciones** (comprensión de conjuntos con filtros): `{ expr | var ∈ conjunto, cond }`.
- **Bucles**: `∀` (for-each), `while`.
- **Condicionales**: `if`/`else` con anidamiento.
- **Funciones** definidas por el usuario (`fun`) y **funciones a trozos**.
- **Objetos** con atributos y herencia (declaración e instanciación).
- **Módulos** mediante `use` y `from`.

### ⚙️ Integración con el ecosistema Heza
- Ejecución de scripts desde el editor (comando `Heza: Run Script`).
- Soporte para snippets con prefijos de notación matemática.

---

## 📦 Instalación

### Desde el marketplace de VS Code (próximamente)
1. Abre VS Code.
2. Ve a Extensiones (`Ctrl+Shift+X`).
3. Busca `Heza` e instala.

### Instalación manual (archivo `.vsix`)
1. Descarga el archivo `.vsix` desde la sección de releases.
2. Abre VS Code y ejecuta **Extensions: Install from VSIX...** desde la paleta de comandos.
3. Selecciona el archivo descargado.

### Requisitos previos
- **Python 3.8+** instalado en el sistema.
- El intérprete de Python debe estar accesible desde la línea de comandos o configurado en el entorno virtual `.venv` / `.env` dentro del directorio de la extensión.

---

## 🚀 Uso básico

### 1. Crear un archivo `.hz`
Crea un archivo con extensión `.hz`. La extensión detectará automáticamente el lenguaje y activará las funciones LSP.

### 2. Escribir código Heza
Ejemplo de un programa simple que usa sumatoria y salida:

```heza
fun main() {
    conjunto = {1, 2, 3, 4, 5}
    suma = ∑(i ∈ conjunto, i^2)
    Sys.out << suma   // imprime 55
}
```

### 3. Ejecutar el script
- Abre la paleta de comandos (`Ctrl+Shift+P`) y selecciona `Heza: Run Script`.
- O usa el atajo configurado (si lo has asignado).
- Se abrirá una terminal integrada mostrando la salida.

### 4. Explorar el código
- **Autocompletado**: empieza a escribir un identificador y obtén sugerencias.
- **Definición**: haz `Ctrl+Click` sobre una función o variable para saltar a su declaración.
- **Hover**: pasa el ratón sobre cualquier símbolo para ver información de tipo y documentación.

---

## 🧪 Ejemplos de sintaxis destacada

### Funciones y funciones a trozos
```heza
fun factorial(n) {
    if (n == 0) {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

// Función a trozos (definida con asignación y llaves)
f(x) = {
    x^2 if x ≥ 0,
    -x   if x < 0
}
```

### Conjuntos y transformaciones
```heza
pares = { n | n ∈ [0..10], n % 2 == 0 }
// equivalente a {0, 2, 4, 6, 8, 10}
```

### Bucles y condicionales
```heza
∀ i ∈ [1..5] do {
    if (i % 2 == 0) {
        Sys.out << i
    }
}
```

### Objetos
```heza
object Punto {
    x = 0,
    y = 0
}

p = Punto { x = 3, y = 4 }
Sys.out << p.x   // imprime 3
```

### Importación de módulos
```heza
// Importar todo el módulo con alias
use "math" as math

// Importar selectivamente
use { sin, cos, ln } from "math"
```

---

## 📋 Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `Heza: Run Script` | Ejecuta el archivo Heza activo en la terminal. |

---