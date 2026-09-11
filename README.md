# Heza Support para Visual Studio Code

Soporte de lenguaje para [Heza](https://github.com/bellosprojects/Heza-Lang), un lenguaje de programación orientado a algoritmos, matemáticas y expresiones simbólicas.

[![Repositorio](https://img.shields.io/badge/GitHub-heza--support-181717?logo=github)](https://github.com/bellosprojects/heza-support)
[![Lenguaje](https://img.shields.io/badge/language-Heza-5b8def)](https://github.com/bellosprojects/Heza-Lang)
[![VS Code](https://img.shields.io/badge/VS%20Code-1.110%2B-007acc?logo=visualstudiocode)](https://code.visualstudio.com/)

> Proyecto en desarrollo. La extensión puede instalarse desde un archivo `.vsix` mientras se prepara su publicación en el Marketplace.

## Qué aporta

Heza Support convierte VS Code en un entorno de trabajo para archivos `.hz`: combina resaltado de sintaxis, un servidor de lenguaje Python y herramientas para ejecutar el programa sin salir del editor.

### Características principales

| Área | Incluye |
| --- | --- |
| Edición | Detección automática de `.hz`, pares de brackets, comentarios con `~`, autocierre y selección envolvente |
| Sintaxis | Resaltado de palabras clave, funciones, objetos, números, strings, comentarios y operadores matemáticos |
| LSP | Diagnósticos en tiempo real, autocompletado contextual, hover, ayuda de firma, ir a definición, símbolos del documento y resaltado semántico |
| Análisis | Identificadores no declarados, uso antes de la declaración y variables no utilizadas |
| Matemáticas | `∑`, `∏`, `∫`, `∂`, `√`, `∀`, `∃`, `∈`, `∪`, `∩`, `→`, `¬`, `∧`, `∨` y más |
| Productividad | Snippets para funciones, condicionales, bucles, objetos, módulos y expresiones matemáticas |
| Ejecución | Comando **Ejecutar script Heza**, botón en el título del editor, menú contextual y `Ctrl+F5` |

## Instalación

### Desde un `.vsix`

1. Descarga el `.vsix` desde [Releases](https://github.com/bellosprojects/heza-support/releases).
2. En VS Code abre la paleta (`Ctrl+Shift+P`).
3. Selecciona **Extensions: Install from VSIX...** y elige el archivo.

### Preparar el servidor de lenguaje

El servidor LSP está escrito en Python. Instala Python 3.8 o posterior y sus dependencias:

```powershell
python -m pip install -r requirements.txt
```

La extensión busca primero un intérprete en `.venv\Scripts\python.exe`, después en `.env\Scripts\python.exe` y finalmente utiliza `python` del `PATH`. Para una instalación reproducible se recomienda crear un entorno virtual en la carpeta de la extensión:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para usar **Ejecutar script Heza**, el intérprete `heza` también debe estar instalado y disponible en el `PATH`. En Windows, la extensión ofrece descargar el instalador desde la última release de [Heza-Lang](https://github.com/bellosprojects/Heza-Lang/releases) si no lo encuentra.

## Primeros pasos

1. Crea o abre un archivo con extensión `.hz`.
2. Escribe `fun` o `summation` y selecciona un snippet.
3. Pasa el cursor sobre un símbolo, usa `Ctrl+Click` para ir a su definición o escribe `(` para ver la firma.
4. Ejecuta el archivo con `Ctrl+F5`, el botón de reproducción del editor o el comando **Ejecutar script Heza**.

```heza
fun main() {
    conjunto = {1, 2, 3, 4, 5}
    suma = ∑(i ∈ conjunto, i^2)
    Sys.out << suma
}
```

## Ejemplos de Heza

### Conjuntos, filtros y bucles

```heza
pares = {n | n ∈ [0..10], n % 2 == 0}

∀ i ∈ pares do {
    Sys.out << i
}
```

### Funciones, objetos y módulos

```heza
fun distancia(x, y) {
    return √(x^2 + y^2)
}

object Punto {
    x = 0,
    y = 0
}

use "math" as math
```

## Comandos y atajos

| Acción | Cómo usarla |
| --- | --- |
| Ejecutar el archivo Heza activo | `Ctrl+F5` |
| Ejecutar el archivo Heza activo | Paleta de comandos → **Ejecutar script Heza** |
| Ejecutar el archivo Heza activo | Menú contextual o botón de reproducción del editor |

## Capturas recomendadas para la página del proyecto

Las imágenes deben guardarse en una carpeta `media/` en la raíz del repositorio. Conviene usar PNG de 1280×720 o 1600×900, con el código ampliado y sin rutas de usuario, tokens ni datos personales.

| Archivo sugerido | Qué debe mostrar | Dónde se usará |
| --- | --- | --- |
| `media/hero.png` | Un archivo `.hz` con resaltado matemático y el logo de Heza | Debajo del título, como imagen principal |
| `media/diagnostics.png` | Un diagnóstico visible y el panel de problemas | Sección LSP y análisis |
| `media/completion.png` | Autocompletado, hover o ayuda de firma | Sección de productividad |
| `media/run-script.png` | `Ctrl+F5` y la salida en la terminal integrada | Sección de ejecución |
| `media/marketplace-icon.png` | Logo cuadrado, idealmente PNG de 128×128 | Icono del Marketplace; reemplaza el `.ico` cuando se publique |

Cuando existan, se pueden insertar así:

```markdown
![Diagnósticos de Heza](media/diagnostics.png)
```

## Estado y soporte

Heza Support está evolucionando junto con el lenguaje Heza. Si encuentras un error o quieres proponer una mejora, abre un [issue](https://github.com/bellosprojects/heza-support/issues) incluyendo:

- versión de VS Code y del sistema operativo;
- versión de la extensión;
- versión de Python y Heza;
- un ejemplo mínimo que reproduzca el problema;
- el mensaje del panel **Output** cuando corresponda.

Consulta el [CHANGELOG](CHANGELOG.md) para conocer los cambios de cada versión.

## Licencia

La licencia del proyecto se publicará junto con la primera versión distribuida en el Marketplace.
