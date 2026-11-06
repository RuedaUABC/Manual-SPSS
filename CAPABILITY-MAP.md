# Capability Map: Manual SPSS

## Contexto

Aplicación de escritorio para Windows 10/11, desarrollada en Python con
PyQt, que convierte el contenido del manual de SPSS en una experiencia de
consulta interactiva y accesible. La interfaz debe seguir el diseño de Figma
proporcionado por el equipo:

<https://www.figma.com/design/31JawBRaqdqo4OH1YJ3qSu/Manual-SPSS?node-id=0-1&t=wbvR5UdOBLjSjaBg-1>

El documento fuente de requisitos es `Manual_SPSS_Requerimientos.md`.

La arquitectura deberá permitir generar posteriormente un instalador de
Windows autocontenido. Las decisiones técnicas de empaquetado, distribución de
recursos y compatibilidad quedan delegadas al desarrollo; como línea base se
evaluará un bundle de 64 bits con PyInstaller en modo `onedir` y un instalador
Windows que conserve el contenido del manual como recurso actualizable.

## Módulos

| Module id | Responsabilidad | Depende de |
|---|---|---|
| `content-model` | Modelo estructurado del manual, carga de capítulos/secciones/subsecciones, recursos gráficos, identificadores únicos y metadatos de atribución/licencia. | — |
| `ui-foundation` | Ventana PyQt, tokens visuales derivados de Figma, componentes reutilizables, estados visuales, navegación entre pantallas y soporte de tema claro/oscuro. | — |
| `reader-navigation` | Lector del contenido, menú jerárquico lateral, sección actual, inicio, anterior/siguiente, progreso y visualización de texto, imágenes y tablas. | `content-model`, `ui-foundation` |
| `search-bookmarks` | Búsqueda por palabras clave, resultados con acceso directo, favoritos y accesos rápidos persistentes. | `content-model`, `reader-navigation` |
| `tts-engine` | Adaptador de síntesis de voz offline para Windows, lectura de sección o selección, controles de reproducción, estado, velocidad y voz. | `content-model`, `ui-foundation` |
| `settings-accessibility` | Pantallas de Ajustes, configuración de voz, tamaño de fuente, contraste/tema, persistencia de preferencias y créditos/derechos de autor. | `ui-foundation`, `tts-engine` |
| `packaging` | Recursos autocontenidos, empaquetado de dependencias y generación de instalador/actualización para Windows sin licencias de pago. | Todos los módulos anteriores |

## Dependencias y orden de construcción

```text
content-model ─────┐
                   ├──> reader-navigation ──┐
ui-foundation ─────┘                         ├──> settings-accessibility ──┐
content-model ───────────────> search-bookmarks                              ├──> packaging
content-model ─────┐                                                        │
ui-foundation ─────┴──> tts-engine ─────────────────────────────────────────┘
```

Orden recomendado por incrementos verticales:

1. `content-model` y `ui-foundation`.
2. `reader-navigation` con una sección demostrable del manual.
3. `tts-engine` con un adaptador offline y controles básicos.
4. `search-bookmarks` integrado con el lector.
5. `settings-accessibility`, incluyendo créditos y licencias.
6. `packaging` y verificación de instalación en Windows 10/11.

## Metodología de desarrollo

Cada módulo se implementará con ciclos Red → Green → Refactor:

1. Red: escribir una prueba que exprese el comportamiento requerido y falle.
2. Green: implementar la solución mínima que haga pasar la prueba.
3. Refactor: mejorar diseño y legibilidad manteniendo todas las pruebas verdes.

La especificación de cada módulo se redactará después de aprobar este mapa,
siguiendo el orden de dependencias.

## Decisiones visuales observadas en Figma

- Lienzo principal de referencia de 1440×1024.
- Barra lateral vertical para capítulos/secciones.
- Panel central claro para el contenido, con título destacado, texto y
  recursos visuales.
- Controles de audio en la parte superior: velocidad, reproducción, pausa,
  detención, reinicio, volumen y progreso.
- Navegación anterior/siguiente en la parte inferior derecha y acceso a inicio
  y ajustes en la barra superior.
- Pantalla de Ajustes con navegación lateral para `Voz`, `Apariencia` y
  `Créditos y derechos de autor`, además de `Volver al manual`.
- Paleta base observada: fondo claro `#f3dedd`, superficie `#fff6f5`, vino
  `#7f3f43`, acento `#a8454d`, texto vino `#5a2528` y controles secundarios
  `#b98486`; debe validarse contra el archivo final antes de implementar.

## Alcance excluido del mapa

- Ejecutar SPSS o realizar análisis estadísticos dentro de la aplicación.
- Reemplazar el contenido oficial del manual por contenido generado por la
  aplicación.
- Sincronización en la nube o dependencia obligatoria de Internet para TTS.
