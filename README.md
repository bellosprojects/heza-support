# Heza Language Support para VS Code

¡El soporte oficial y definitivo para el lenguaje de programación Heza en Visual Studio Code! 

Esta extensión proporciona una experiencia de desarrollo de primera clase, convirtiendo a VS Code en un IDE completo para Heza mediante un Servidor de Lenguaje (LSP) personalizado y altamente optimizado.

## ✨ Características Principales

*   🎨 **Resaltado Semántico Inteligente:** No es solo colorear palabras. El editor entiende el contexto y colorea variables, clases y funciones de manera distinta dependiendo de su alcance (Scope).
*   ⚡ **Autocompletado Sensible al Contexto:** 
    *   Sugerencias de variables y funciones limitadas inteligentemente al scope actual.
    *   **Autocompletado de Objetos:** Escribe `instancia.` y obtén acceso inmediato a los atributos específicos de esa clase.
    *   **Snippets Automáticos:** Al autocompletar funciones o clases, se generan las plantillas con los parámetros listos para rellenar usando la tecla `Tab`.
*   📖 **Documentación Emergente (Hover):** Pasa el cursor sobre cualquier función, variable o clase para ver su firma, tipo y la documentación (docstrings) extraída directamente de tus comentarios.
*   🧭 **Navegación de Código (Go to Definition):** Haz `Ctrl + Click` (o `F12`) sobre cualquier identificador para viajar instantáneamente a la línea exacta donde fue definido.

## 🚀 Instalación y Uso

1. Instala la extensión desde el Marketplace.
2. Abre cualquier archivo con la extensión `.heza`.
3. ¡Comienza a escribir! El servidor LSP se iniciará automáticamente en segundo plano.

## 🛠️ Cómo Funciona (Para Geeks)

Heza Language Support no usa simples expresiones regulares para adivinar el código. Por debajo, ejecuta un **Árbol de Sintaxis Abstracta (AST)** en tiempo real que mapea los scopes léxicos, las instancias y las declaraciones de tu código milisegundo a milisegundo, comunicándose con VS Code a través del Language Server Protocol.

---
*Hecho con ❤️ para la comunidad de Heza.*