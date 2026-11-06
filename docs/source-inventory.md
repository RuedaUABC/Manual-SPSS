# Inventario de la fuente: Manual SPSS

## Archivos y alcance

| PDF de origen | Páginas | Formato | Capítulos | Objetos de imagen informados por Poppler |
| --- | ---: | --- | --- | --- |
| `cap1y2_SPSS.pdf` | 9 | Carta horizontal | 1: pp. 1–4; 2: pp. 5–9 | 39 imágenes y 18 máscaras de transparencia |
| `MANUAL SPSS CAPITULO 3 Y 4.pdf` | 13 | Carta horizontal | 3: pp. 1–9; 4: pp. 10–13 | 69 imágenes y 32 máscaras de transparencia |
| `Capitulo 5 y 6 Manual SPSS.pdf` | 11 | A4 vertical | 5: pp. 1–6; 6: pp. 7–11 | 16 imágenes |
| `MANUAL SPSS - CAPÍTULO 7 y 8.pdf` | 17 | A4 vertical | 7: pp. 1–13; 8: pp. 14–17 | 29 imágenes |

Total: 50 páginas y 8 capítulos. Los números de imagen son filas de objetos
del PDF, no figuras editoriales únicas: algunas referencias se repiten y los
PDF de capítulos 1–4 almacenan 50 máscaras de transparencia por separado.

## Revisión visual y criterio de extracción

Se revisaron visualmente todas las páginas en cuatro hojas de contacto
generadas con `pdftoppm`. El texto se extrajo con `pdftotext -raw` para
mantener el orden de lectura de las columnas y los pasos. `pdfimages -list`
permitió distinguir imágenes de máscaras.

En el capítulo 2, la fuente deja incompleto el inciso «Longitud máxima de
hasta» y no muestra una cifra; se conservará esa limitación y no se completará
por inferencia. Se corregirán únicamente artefactos de extracción como
caracteres de ancho cero y el acento de «máxima».

Se conservarán como recursos las capturas, ventanas, tablas y gráficos que
explican los pasos o resultados. Se omiten las máscaras técnicas, logotipos
pequeños repetidos, iconos sueltos y adornos; sus formas visibles dentro de las
capturas útiles quedan intactas. Las páginas de portada de capítulo se
representan mediante el encabezado del capítulo en el HTML. Las páginas sin
figuras explicativas conservan el texto extraído.

## Mapa página por página

### `cap1y2_SPSS.pdf`

| Página | Capítulo | Texto y estructura identificados | Elementos visuales |
| ---: | --- | --- | --- |
| 1 | 1 | Portadilla «CAPÍTULO 1». | Portada; se integra al encabezado HTML. |
| 2 | 1 | Introducción, qué es SPSS, para qué sirve y cómo iniciarlo. | Búsqueda/arranque de SPSS y marcas de la interfaz. |
| 3 | 1 | Continuación del inicio: licencia, ventana de bienvenida, abrir o crear trabajo. | Ventanas de licencia y bienvenida; accesos resaltados. |
| 4 | 1 | Vista de datos y vista de variables; menú, barra de herramientas y visor de resultados. | Capturas de la interfaz principal y sus barras. |
| 5 | 2 | Portadilla «CAPÍTULO 2». | Portada; se integra al encabezado HTML. |
| 6 | 2 | Concepto de base de datos y primeros campos de una variable. | Vista de datos/variables y nombre de variable. |
| 7 | 2 | Tipo, anchura, decimales, etiqueta y valores. | Diálogos de propiedades y etiquetas. |
| 8 | 2 | Valores perdidos, columnas y alineación. | Diálogo de valores perdidos y opciones de columna. |
| 9 | 2 | Medida y rol de una variable: nominal, ordinal, entrada, objetivo y otros. | Menús de medida y rol. |

### `MANUAL SPSS CAPITULO 3 Y 4.pdf`

| Página | Capítulo | Texto y estructura identificados | Elementos visuales |
| ---: | --- | --- | --- |
| 1 | 3 | Portadilla «CAPÍTULO 3». | Portada; se integra al encabezado HTML. |
| 2 | 3 | Estadísticos descriptivos, tendencia central y pasos para obtener la media. | Menús, selector de descriptivos y lista de variables. |
| 3 | 3 | Ventana de análisis; mover una variable y abrir opciones. | Selectores de variables y botones de traslado. |
| 4 | 3 | Selección de media, visor de resultados y entrada a frecuencias. | Opciones estadísticas y tabla de resultados. |
| 5 | 3 | Selección de variable y cálculo de mediana. | Frecuencias, lista de variables y opciones. |
| 6 | 3 | Mediana, distribución, dispersión y varianza. | Visor/tabla estadística y opciones de frecuencias. |
| 7 | 3 | Varianza y preparación de respuestas de selección múltiple. | Opciones y cuadros de análisis. |
| 8 | 3 | Definición de conjuntos de respuestas múltiples. | Diálogos para definir el conjunto y seleccionar variables. |
| 9 | 3 | Ejecución y tabla de porcentajes por opción. | Tabla de resultados de frecuencias. |
| 10 | 4 | Portadilla «CAPÍTULO 4». | Portada; se integra al encabezado HTML. |
| 11 | 4 | Variables categóricas y tablas de contingencia; inicio del procedimiento. | Menú Analizar y tabla de variables. |
| 12 | 4 | Elegir variables y configurar porcentajes para la tabla. | Selector de variables y opciones de casillas. |
| 13 | 4 | Ejecutar análisis y conclusión sobre tablas cruzadas. | Salida tabular de SPSS. |

### `Capitulo 5 y 6 Manual SPSS.pdf`

| Página | Capítulo | Texto y estructura identificados | Elementos visuales |
| ---: | --- | --- | --- |
| 1 | 5 | Pruebas de hipótesis: introducción, formulación y criterio del valor p; inicio de prueba T independiente. | Texto y fórmulas; sin captura relevante. |
| 2 | 5 | Objetivo, ejemplo y procedimiento de prueba T para muestras independientes. | Menú, cuadro de prueba T y definición de grupos. |
| 3 | 5 | Interpretación de prueba T independiente e introducción a prueba T de una muestra. | Tabla de resultados; no se añade figura independiente. |
| 4 | 5 | Procedimiento de prueba T para una muestra e interpretación. | Menú, diálogo y tabla de resultados. |
| 5 | 5 | Prueba T para muestras relacionadas: objetivo, ejemplo y selección. | Menú y diálogo para variables relacionadas. |
| 6 | 5 | Interpretación de muestras relacionadas y consideraciones finales. | Tablas de resultados de prueba T. |
| 7 | 6 | Introducción, hipótesis y fundamento de ANOVA; inicio del procedimiento. | Menú y ventana ANOVA de un factor. |
| 8 | 6 | Selección de dependiente/factor e interpretación del valor Sig. | Menú, diálogo y tabla ANOVA. |
| 9 | 6 | Pruebas Post Hoc y selección de Tukey. | Tabla de ANOVA y opciones Post Hoc. |
| 10 | 6 | Ejemplo de satisfacción entre localidades y comparaciones múltiples. | Diálogo Post Hoc y tabla de comparaciones. |
| 11 | 6 | Resultado del ejemplo y consideraciones finales. | Texto de conclusión; sin figura adicional relevante. |

### `MANUAL SPSS - CAPÍTULO 7 y 8.pdf`

| Página | Capítulo | Texto y estructura identificados | Elementos visuales |
| ---: | --- | --- | --- |
| 1 | 7 | Introducción a gráficos; tipos y arranque de gráfico de pastel. | Menú Gráficos y hoja de datos. |
| 2 | 7 | Configuración de gráfico circular y selección de variable. | Cuadros de diálogo y selector de variable. |
| 3 | 7 | Título, continuación y aceptación del gráfico circular. | Diálogos de título y botones resaltados. |
| 4 | 7 | Generación y edición del gráfico de pastel. | Gráfico circular y ventana de edición. |
| 5 | 7 | Interpretación del pastel e inicio de barras simples. | Resultado circular; menú de barras. |
| 6 | 7 | Selección de variable, eje de categorías y título para barras. | Diálogo de barras y ejes. |
| 7 | 7 | Generación e interpretación del gráfico de barras. | Resultado gráfico y ventana de edición. |
| 8 | 7 | Interpretación y comienzo de barras agrupadas. | Gráfico de barras; menú de agrupación. |
| 9 | 7 | Asignación de categoría y variable de agrupación. | Diálogos para barras agrupadas. |
| 10 | 7 | Título, ejecución y edición del gráfico agrupado. | Cuadros de título y gráfico resultante. |
| 11 | 7 | Interpretación de barras agrupadas e inicio de dispersión. | Gráfico agrupado y menú de dispersión. |
| 12 | 7 | Asignación de ejes X/Y y título del gráfico de dispersión. | Diálogos de dispersión y variables. |
| 13 | 7 | Gráfico de dispersión e interpretación. | Gráfico de puntos y salida de SPSS. |
| 14 | 8 | Introducción a correlación, tipos de relación y correlación bivariada. | Menú Analizar/Correlacionar. |
| 15 | 8 | Selección de variables y opciones Pearson/bilateral. | Diálogos de correlaciones bivariadas. |
| 16 | 8 | Tabla de correlación e interpretación del coeficiente. | Ventana de resultados y matriz de correlaciones. |
| 17 | 8 | Ejemplo: correlación Edad–Último gasto de −0.075. | Tabla de ejemplo y explicación textual. |

## Autoría, procedencia y licencia

Los cuatro PDF proceden de la carpeta `Manual SPSS original/` entregada para
este proyecto. Los metadatos PDF de `Capitulo 5 y 6 Manual SPSS.pdf` muestran
el campo Author como «ANA MARIA»; esto se conserva como dato de origen, pero no
confirma la titularidad de derechos. Los otros tres PDF no declaran un autor en
sus metadatos. Los archivos no indican una licencia de uso verificable; por
tanto, la autoría legal y la licencia del manual y de sus capturas quedan **no
confirmadas**. No se atribuye al contenido la licencia de PyQt6 ni la de
Figma.
