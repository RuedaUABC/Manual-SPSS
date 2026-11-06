---
author:
- Equipo de Servicio Social Profesional
date: 2 de septiembre de 2026
title: Documento de Especificación de Requerimientos (SRS) para el
  Sistema del Manual SPSS
---

# Introducción al documento

## Propósito

El propósito de este documento es especificar los requerimientos de
software para el desarrollo de una aplicación informática destinada a
funcionar como un manual interactivo del sistema estadístico SPSS. El
documento establece las funcionalidades, características de usabilidad,
confiabilidad, rendimiento, soportabilidad, diseño e implementación que
deberá cumplir el sistema.

El documento SRS servirá como referencia para el análisis, diseño,
desarrollo, pruebas y validación de la aplicación, permitiendo
establecer de manera clara las características que deberá presentar el
producto final y ayudarnos a los desarrolladores a mantener un flujo de
trabajo adecuado siguiendo la descripción de funcionalidades.

## Alcance

El sistema consistirá en una aplicación de escritorio orientada a la
consulta y estudio de un manual de SPSS organizado por capítulos,
secciones y subsecciones. Su objetivo principal será transformar el
contenido actualmente disponible en documentos PDF en una experiencia de
consulta interactiva, organizada y visualmente homogénea.

La aplicación permitirá al usuario navegar por la estructura del manual
mediante un menú de contenidos y controles de navegación para avanzar o
retroceder entre secciones. Asimismo, permitirá consultar texto,
imágenes, tablas, capturas de pantalla y demás recursos asociados al
contenido.

Como característica principal de accesibilidad, el sistema incorporará
una funcionalidad de texto a voz, mediante la cual el estudiante podrá
reproducir el contenido de una sección completa desde su inicio o
seleccionar un fragmento específico para convertirlo en audio. También
se contemplarán controles para pausar, reanudar, detener y reiniciar la
reproducción, así como opciones para ajustar la velocidad y la voz
utilizada.

El sistema estará orientado principalmente a la consulta del manual y no
tendrá como objetivo ejecutar SPSS, realizar análisis estadísticos ni
sustituir las funcionalidades propias del software estadístico.

## Personal Involucrado

::: tabularx
\|p4.8cm\|X\| **Nombre** & Luis Ernesto Mellín Pineda\
**Rol** & Líder del equipo\
**Responsabilidades** & Coordinar al equipo, diseñador de prototipos y
UX, auditor de código y primer encargado de la documentación del
proyecto\
**Información de contacto** & mellin.luis@uabc.edu.mx\
:::

::: tabularx
\|p4.8cm\|X\| **Nombre** & Kevin Misael García Vargas\
**Rol** & Ayudante de diseño\
**Responsabilidades** & Diseño de UI, segundo encargado de la
documentación y ayudante para las auditorías de código\
**Información de contacto** & k2208005@uabc.edu.mx\
:::

::: tabularx
\|p4.8cm\|X\| **Nombre** & Jorge Alberto Rueda Gallegos\
**Rol** & Programador\
**Responsabilidades** & Programación principal de la UI, Backend y
módulos correspondientes al manual interactivo\
**Información de contacto** & rueda.jorge@uabc.edu.mx\
:::

::: tabularx
\|p4.8cm\|X\| **Nombre** & Alan Alexis Galvez Necoechea\
**Rol** & Programador\
**Responsabilidades** & Segundo programador a cargo de la implementación
y diseño del motor de texto a voz\
**Información de contacto** & alan.galvez@uabc.edu.mx\
:::

## Definiciones, acrónimos y abreviaturas

::: tabularx
\|p4.5cm\|X\| **Término / Acrónimo** & **Definición / Significado**\
**Requerimiento** & Condición o capacidad que debe cumplir el sistema
para satisfacer un contrato, norma, especificación u otro documento
formalmente impuesto.\
**FURPS+** & Modelo de clasificación de requerimientos de software que
abarca: Funcionalidad (*Functionality*), Usabilidad (*Usability*),
Confiabilidad (*Reliability*), Rendimiento (*Performance*),
Soportabilidad (*Supportability*) y el símbolo **+** para restricciones
adicionales (diseño, implementación, interfaz y físicas).\
**RF** & **Requerimiento Funcional**: Requisito que especifica una
función, comportamiento o servicio concreto que el sistema debe
realizar.\
**RNF** & **Requerimiento No Funcional**: Requisito que especifica
atributos de calidad, restricciones o propiedades globales del sistema
(como rendimiento, seguridad, usabilidad o mantenibilidad).\
**SPSS** & **Statistical Package for the Social Sciences** (*Paquete
Estadístico para las Ciencias Sociales*): Software de análisis
estadístico utilizado para el procesamiento y gestión de datos.\
:::

## Resumen

El presente documento está organizado en tres secciones principales. La
primera sección presenta el propósito, alcance y contexto general del
documento de especificación de requerimientos.

La segunda sección describe las características generales del sistema,
incluyendo su perspectiva, funcionalidades principales, usuarios,
restricciones, suposiciones y dependencias.

La tercera sección contiene la especificación detallada de los
requerimientos del sistema, organizados de acuerdo con el modelo FURPS+,
contemplando requerimientos de funcionalidad, usabilidad, confiabilidad,
rendimiento, soportabilidad, diseño e implementación.

# Descripción General

## Perspectiva del producto

El sistema será una aplicación de escritorio independiente destinada a
proporcionar una interfaz interactiva para la consulta de un manual de
SPSS. El producto se desarrollará como una alternativa al formato
tradicional de consulta mediante documentos PDF, proporcionando una
estructura de navegación más organizada y una presentación visual
homogénea.

La aplicación estará compuesta conceptualmente por varios elementos
principales: un módulo de presentación del contenido, un sistema de
navegación, un componente de procesamiento de texto a voz, un mecanismo
de configuración de la interfaz y una estructura de almacenamiento para
el contenido del manual.

El contenido del manual será gestionado de forma independiente de la
lógica principal de la aplicación, de manera que sea posible actualizar,
sustituir o ampliar los capítulos y secciones sin necesidad de modificar
las funcionalidades fundamentales del sistema.

El sistema estará orientado a funcionar en un entorno de escritorio
Windows y deberá contar con los recursos necesarios para proporcionar la
funcionalidad de texto a voz sin depender de una conexión a Internet, de
acuerdo con las restricciones de implementación establecidas.

## Funcionalidad del producto

Las principales funcionalidades que proporcionará el producto serán:

1.  **Consulta del manual:** permitirá visualizar el contenido de los
    capítulos, secciones y subsecciones que conforman el manual de SPSS.

2.  **Navegación estructurada:** permitirá acceder a las diferentes
    partes del manual mediante un menú jerárquico y mediante botones
    para avanzar y retroceder.

3.  **Identificación de la ubicación:** mostrará al usuario el capítulo
    o sección que está consultando y su posición dentro de la estructura
    del manual.

4.  **Búsqueda de contenido:** permitirá localizar conceptos y temas
    mediante palabras clave o términos relacionados con SPSS.

5.  **Visualización de recursos:** permitirá consultar imágenes,
    capturas de pantalla, tablas y otros elementos gráficos asociados
    con el contenido.

6.  **Texto a voz:** permitirá convertir el contenido textual del manual
    en audio.

7.  **Lectura de texto seleccionado:** permitirá seleccionar un
    fragmento específico del contenido y reproducir mediante texto a voz
    únicamente dicho fragmento.

8.  **Control de reproducción:** permitirá iniciar, pausar, reanudar,
    detener y reiniciar la reproducción del contenido mediante texto a
    voz.

9.  **Configuración del lector de voz:** permitirá ajustar parámetros
    como la velocidad de reproducción y la voz utilizada.

10. **Personalización visual:** permitirá modificar determinados
    aspectos de la presentación del contenido, como el tamaño de fuente
    y el modo de contraste.

11. **Favoritos:** permitirá marcar determinadas secciones como
    favoritas para acceder posteriormente a ellas mediante una lista de
    accesos rápidos.

12. **Indicador de progreso:** permitirá conocer la posición actual del
    usuario respecto al contenido total del manual.

## Características de los usuarios

El sistema estará dirigido principalmente a usuarios que necesiten
consultar y estudiar el contenido de un manual de SPSS, sin requerir
conocimientos técnicos sobre el funcionamiento interno de la aplicación.

Se considera que los usuarios tendrán conocimientos básicos de
informática y estarán familiarizados con operaciones comunes como
seleccionar opciones de un menú, utilizar botones, desplazarse por
contenido y seleccionar texto.

El sistema no estará dirigido exclusivamente a usuarios expertos en
SPSS. Por el contrario, su interfaz deberá facilitar la consulta tanto a
personas que se encuentren aprendiendo a utilizar el software como a
usuarios que necesiten consultar determinados procedimientos o conceptos
estadísticos.

Debido a que una de las funciones principales será la reproducción del
contenido mediante texto a voz, la aplicación también deberá considerar
a usuarios que prefieran o necesiten utilizar el contenido mediante
reproducción auditiva.

### Perfil general del usuario

  **Característica**                **Descripción**
  --------------------------------- --------------------------------------------------------
  Tipo de usuario                   Estudiante buscando aprender SPSS
  Conocimientos informáticos        Básicos
  Conocimientos de SPSS             Básicos, intermedios o avanzados
  Interacción principal             Consulta y navegación
  Funciones principales             Lectura, búsqueda, navegación y dictado de texto a voz
  Nivel de capacitación requerido   Bajo

## Restricciones

El desarrollo y funcionamiento del sistema estará sujeto a las
siguientes restricciones:

-   El sistema deberá estar orientado a un entorno de escritorio Windows
    en sus versiones 10 u 11.

-   La funcionalidad de texto a voz deberá utilizar una tecnología
    compatible con dicho entorno y deberá funcionar sin conexión a
    Internet.

-   El contenido del manual deberá integrarse dentro de la aplicación o
    distribuirse junto con ella, de acuerdo con la arquitectura
    seleccionada.

-   El contenido deberá conservar su estructura y elementos relevantes
    durante el proceso de incorporación al sistema.

-   La aplicación deberá mantener una separación entre el contenido del
    manual y la lógica de funcionamiento del programa.

-   El desarrollo deberá considerar las restricciones presupuestarias
    propias de un proyecto de servicio social, evitando depender de
    licencias de software de pago para la compilación y generación del
    instalador.

-   La interfaz deberá mantener una estructura visual homogénea en las
    diferentes secciones de la aplicación.

-   Las tecnologías y bibliotecas utilizadas deberán ser compatibles con
    el entorno de ejecución definido para el proyecto.

-   El sistema deberá ejecutarse sin requerir que el usuario realice
    configuraciones técnicas complejas después de la instalación.

## Suposiciones y dependencias

### Suposiciones

-   Se supone que el contenido del manual proporcionado para el proyecto
    representa la fuente oficial que será integrada en la aplicación.

-   Se supone que el contenido del manual se encuentra disponible en un
    formato que permita su procesamiento e incorporación al sistema.

-   Se supone que el usuario dispone de un equipo compatible con el
    entorno de ejecución de la aplicación.

-   Se supone que el usuario utilizará la aplicación principalmente para
    consultar el contenido del manual y no para ejecutar directamente
    procedimientos estadísticos dentro de la aplicación.

-   Se supone que el usuario cuenta con un dispositivo de salida de
    audio cuando desee utilizar la funcionalidad de texto a voz.

### Dependencias

-   La funcionalidad de texto a voz dependerá de la disponibilidad de un
    motor de síntesis de voz compatible con Windows.

-   La aplicación dependerá de los recursos gráficos y archivos que
    conformen el contenido del manual.

-   La correcta visualización de determinados elementos dependerá del
    formato utilizado para almacenar e integrar el contenido.

-   El funcionamiento del sistema dependerá de las bibliotecas y
    componentes utilizados durante su desarrollo.

-   La generación del instalador dependerá de herramientas de
    compilación y empaquetado compatibles con las tecnologías
    seleccionadas para el proyecto.

-   Las futuras actualizaciones del contenido dependerán de que los
    nuevos capítulos y secciones mantengan la estructura requerida por
    el sistema.

# Especificación de Requerimientos

A continuación, se especifican los requerimientos del sistema modelados
y redactados bajo el modelo FURPS+.

## Requerimientos de funcionalidad (F)

**RF-01 - Visualización del contenido del manual**

El usuario debe poder consultar el contenido del manual de SPSS,
seleccionando un capítulo o sección desde la interfaz, y visualizando en
pantalla el texto, imágenes y demás elementos correspondientes a la
sección seleccionada.

**RF-02 - Navegación mediante menú**

El usuario debe poder acceder a cualquier capítulo o sección del manual,
seleccionando la opción correspondiente desde un menú de navegación, y
visualizando directamente el contenido de la sección seleccionada.

**RF-03 - Avance a la siguiente sección**

El usuario debe poder avanzar a la siguiente sección del manual,
utilizando un botón de navegación, y visualizando el contenido
correspondiente a la siguiente sección en el orden establecido.

**RF-04 - Retroceso a la sección anterior**

El usuario debe poder regresar a la sección anterior del manual,
utilizando un botón de navegación, y visualizando el contenido
correspondiente a la sección anterior en el orden establecido.

**RF-05 - Identificación de la sección actual**

El usuario debe poder identificar la sección del manual que está
consultando, visualizando en la interfaz el título y la ubicación de la
sección dentro de la estructura del manual.

**RF-06 - Inicio de lectura de una sección mediante texto a voz**

El usuario debe poder iniciar la lectura mediante texto a voz de una
sección del manual, activando el botón de reproducción, y escuchando el
contenido textual de la sección desde su inicio.

**RF-07 - Selección de texto para lectura mediante texto a voz**

El usuario debe poder seleccionar un fragmento de texto dentro de una
sección del manual, utilizando los mecanismos de selección disponibles
en la interfaz, y estableciendo dicho fragmento como el contenido que
será procesado mediante texto a voz.

**RF-08 - Lectura del texto seleccionado mediante texto a voz**

El usuario debe poder reproducir mediante texto a voz únicamente el
fragmento seleccionado del manual, activando la función de lectura, y
escuchando el contenido seleccionado desde su inicio.

**RF-09 - Pausa de la lectura mediante texto a voz**

El usuario debe poder pausar la reproducción mediante texto a voz,
activando el botón de pausa durante la lectura, y deteniendo
temporalmente la reproducción del contenido.

**RF-10 - Reanudación de la lectura mediante texto a voz**

El usuario debe poder reanudar una reproducción pausada mediante texto a
voz, activando el botón de reproducción o reanudación, y continuando la
lectura desde el punto en que fue pausada.

**RF-11 - Detención de la lectura mediante texto a voz**

El usuario debe poder detener la reproducción mediante texto a voz,
activando el botón de detención, y finalizando la reproducción del
contenido actual.

**RF-12 - Reinicio de la lectura mediante texto a voz**

El usuario debe poder reiniciar la lectura mediante texto a voz,
activando la opción de reinicio, y comenzando nuevamente la reproducción
desde el inicio de la sección o del fragmento seleccionado.

**RF-13 - Indicación visual del estado del texto a voz**

El usuario debe poder conocer el estado actual de la reproducción
mediante texto a voz, visualizando en la interfaz si la lectura se
encuentra reproduciéndose, pausada, detenida o finalizada.

**RF-14 - Navegación conservando la estructura del manual**

El usuario debe poder recorrer el manual respetando el orden jerárquico
establecido, seleccionando capítulos, apartados y subapartados, y
accediendo al contenido correspondiente sin perder la estructura de
navegación.

**RF-15 - Visualización de elementos gráficos del manual**

El usuario debe poder consultar las imágenes, capturas de pantalla,
tablas y demás elementos gráficos asociados a una sección, accediendo a
dicha sección, y visualizando los elementos en la posición
correspondiente dentro del contenido.

**RF-16 - Acceso al inicio del manual**

El usuario debe poder regresar al inicio del manual desde cualquier
sección, seleccionando la opción correspondiente, y visualizando la
portada, introducción o primera sección definida del manual.

**RF-17 - Indicador de progreso de navegación**

El usuario debe poder conocer su posición dentro del manual, navegando
entre sus secciones, y visualizando un indicador que represente la
sección actual respecto al total de secciones disponibles.

**RF-18 - Localización de conceptos o temas**

El usuario debe poder localizar conceptos o temas de SPSS, ingresando
palabras clave o términos estadísticos en la barra de búsqueda, y
obtener un listado de resultados coincidentes con accesos directos a los
capítulos.

**RF-19 - Ajuste de la velocidad de reproducción**

El usuario debe poder ajustar la velocidad de reproducción del audio
generado, seleccionando una opción de velocidad (lenta, normal, rápida)
desde el panel de configuración del lector de voz, y escuchar la
narración con el ritmo seleccionado.

**RF-20 - Modificación del tipo de voz**

El usuario debe poder ajustar la voz utilizada por el sistema de texto a
voz, seleccionando una opción de voz disponible en el panel de
configuración, y escuchar la narración con la voz seleccionada a partir
de la siguiente reproducción.

**RF-21 - Marcadores de sección/es favorita/s**

El usuario debe poder marcar una sección como favorita o de referencia
rápida, presionando el ícono de marcador ubicado en el encabezado de la
sección, y visualizar dicha sección posteriormente en un listado de
"Accesos rápidos" o "Favoritos".

**RF-22 - Ajuste del tamaño de fuente**

El usuario debe poder ajustar el tamaño de la fuente del texto
visualizado, seleccionando una opción de tamaño (pequeño, mediano o
grande) desde el panel de configuración visual, y visualizar el
contenido del manual con el tamaño de letra seleccionado.

## Requerimientos de Usabilidad (U)

**RNF-U-01 - Interfaz intuitiva**

La aplicación debe proporcionar una interfaz sencilla e intuitiva que
permita al usuario acceder al contenido del manual y utilizar sus
funciones principales sin requerir conocimientos técnicos sobre el
funcionamiento interno del sistema.

**RNF-U-02 - Consistencia visual**

La aplicación debe mantener una estructura visual homogénea en todas las
secciones del manual, utilizando de manera consistente tipografías,
tamaños, estilos, botones, iconografía y distribución de elementos.

**RNF-U-03 - Organización del contenido**

La aplicación debe presentar el contenido del manual de forma jerárquica
y organizada, diferenciando visualmente capítulos, secciones,
subsecciones, texto, imágenes, tablas y elementos complementarios.

**RNF-U-04 - Facilidad de navegación**

La aplicación debe permitir que el usuario identifique fácilmente las
opciones para avanzar, retroceder, seleccionar una sección y regresar al
inicio del manual.

**RNF-U-05 - Accesibilidad de la función de texto a voz**

La aplicación debe proporcionar controles de texto a voz claramente
identificables y accesibles desde las secciones donde se encuentre
disponible dicha funcionalidad.

**RNF-U-06 - Retroalimentación de acciones**

La aplicación debe proporcionar retroalimentación visual al usuario
después de ejecutar acciones relevantes, tales como iniciar, pausar o
detener la lectura mediante texto a voz, así como cambiar de sección.

**RNF-U-07 - Ajustes de interfaz**

El usuario debe poder adaptar la presentación visual del texto,
seleccionando entre opciones de tamaño de letra o modo de contraste
(claro/oscuro), y ajustar la interfaz para una lectura cómoda y
accesible.

## Requerimientos de Confiabilidad (R)

**RNF-R-01 - Disponibilidad del contenido**

La aplicación debe garantizar que el contenido integrado del manual
pueda ser consultado durante el funcionamiento normal del sistema,
evitando pérdidas o alteraciones de la información almacenada.

**RNF-R-02 - Integridad del contenido**

La aplicación debe conservar íntegramente el contenido del manual,
incluyendo texto, imágenes, tablas y demás elementos necesarios para su
correcta consulta.

**RNF-R-03 - Manejo de errores**

La aplicación debe detectar y gestionar errores relacionados con la
carga del contenido o con el procesamiento de texto a voz,
proporcionando al usuario un mensaje que indique la situación ocurrida.

**RNF-R-04 - Recuperación ante errores**

La aplicación debe evitar que un error en una función, como el
procesamiento de texto a voz, provoque el cierre inesperado o la pérdida
de la navegación dentro del manual.

**RNF-R-05 - Control de flujo seguro**

El usuario debe poder pausar, reanudar o detener el dictado de audio,
interactuando con la barra de controles del reproductor de texto a voz,
y mantener el control del flujo de lectura sin fallos en la reproducción
ni desincronización del texto.

## Requerimientos de Rendimiento (P)

**RNF-P-01 - Tiempo de carga de secciones**

La aplicación debe cargar y mostrar una sección seleccionada del manual
en un tiempo que permita una navegación fluida y sin esperas
perceptibles para el usuario (menor a 2 segundos).

**RNF-P-02 - Respuesta de la interfaz**

La aplicación debe responder a las acciones de navegación y selección
realizadas por el usuario sin presentar bloqueos o retrasos que
dificulten la consulta del manual (menor a 1 segundo).

**RNF-P-03 - Inicio del texto a voz**

La aplicación debe iniciar el procesamiento de texto a voz en un tiempo
adecuado después de que el usuario active la función de lectura.

**RNF-P-04 - Procesamiento de fragmentos seleccionados**

La aplicación debe procesar únicamente el texto seleccionado cuando el
usuario solicite la lectura de un fragmento, evitando procesar
innecesariamente el contenido restante de la sección.

## Requerimientos de Soportabilidad (S)

**RNF-S-01 - Mantenimiento del contenido**

La aplicación debe permitir que el contenido del manual pueda ser
actualizado o sustituido sin requerir modificaciones innecesarias en las
funcionalidades de navegación y texto a voz.

**RNF-S-02 - Modularidad**

La aplicación debe mantener separadas las funcionalidades de
presentación del contenido, navegación y procesamiento de texto a voz,
facilitando futuras modificaciones o ampliaciones.

**RNF-S-03 - Extensibilidad**

La aplicación debe permitir incorporar nuevos capítulos, secciones o
contenidos al manual sin alterar la estructura general de navegación.

**RNF-S-04 - Documentación del sistema**

El código fuente y los componentes principales de la aplicación deben
contar con documentación suficiente para facilitar su mantenimiento y
futuras modificaciones.

**RNF-S-05 - Actualización de versiones**

El sistema debe permitir la actualización de versiones futuras del
manual mediante un instalador de actualización o parche, sin requerir la
desinstalación completa de la versión anterior.

## Requerimientos de Diseño (+)

**RD-01 - Diseño de interfaz homogéneo**

El sistema debe utilizar un diseño de interfaz visualmente homogéneo en
todas las pantallas y secciones, manteniendo una distribución
consistente de los elementos de navegación y consulta.

**RD-02 - Diseño adaptable del contenido**

El sistema debe organizar el contenido de manera que los elementos
textuales y gráficos puedan visualizarse correctamente dentro del área
disponible de la interfaz.

**RD-03 - Separación de componentes**

El sistema debe diseñarse mediante componentes independientes para la
gestión del contenido, navegación, interfaz gráfica y procesamiento de
texto a voz, permitiendo modificar cada componente sin afectar
innecesariamente a los demás.

## Requerimientos de Implementación (+)

**RI-01 - Tecnología de procesamiento de texto a voz**

El sistema debe utilizar una biblioteca o API de síntesis de voz
compatible con entorno de escritorio en Windows (por ejemplo, Microsoft
Speech API/SAPI 5, System.Speech en .NET, o motores TTS de terceros de
bajo costo/gratuitos), garantizando que el texto a voz funcione sin
conexión a internet.

**RI-02 - Separación entre contenido y aplicación**

El contenido del manual debe almacenarse de manera independiente de la
lógica de funcionamiento de la aplicación, permitiendo actualizar el
contenido sin modificar las funcionalidades principales del sistema.

**RI-03 - Identificación estructurada de las secciones**

Cada capítulo, sección y subsección del manual debe contar con un
identificador único que permita establecer relaciones de navegación
entre los diferentes contenidos.

**RI-04 - Compatibilidad con los recursos del manual**

La implementación debe permitir integrar los formatos de texto e
imágenes utilizados por el manual sin provocar pérdida significativa de
información durante su incorporación al sistema.

**RI-05 - Instalador de aplicación**

El instalador debe empaquetar todas las dependencias necesarias
(bibliotecas de TTS, recursos gráficos, contenido del manual) para que
la aplicación funcione de manera autocontenida tras la instalación.

**RI-06 - Generación de instalador**

El proyecto debe poder compilarse y generar el instalador sin depender
de licencias de pago, considerando que es un proyecto de servicio
social.

## Requerimientos adicionales: Créditos y derechos de autor

Estos requerimientos amplían la especificación para incorporar una interfaz de créditos y derechos de autor accesible desde el apartado **Ajustes**.

### Requerimientos funcionales (F)

**RF-23 — Acceso a la interfaz de créditos y derechos de autor**

El usuario debe poder acceder a la interfaz de créditos y derechos de autor desde el apartado **Ajustes**, seleccionando una opción identificada claramente como “Créditos y derechos de autor”, y visualizando la información correspondiente.

**RF-24 — Visualización de créditos del proyecto**

El usuario debe poder consultar los créditos de las personas que participaron en el desarrollo del manual interactivo, accediendo a la interfaz de créditos, y visualizando el nombre y, cuando corresponda, el rol o contribución de cada integrante.

**RF-25 — Visualización de información sobre derechos de autor**

El usuario debe poder consultar la información sobre los derechos de autor aplicables al contenido del manual y a los recursos incluidos en la aplicación, accediendo a la sección de derechos de autor, y visualizando las atribuciones, licencias y avisos disponibles.

**RF-26 — Atribución de recursos de terceros**

El usuario debe poder identificar la autoría y la licencia de los recursos de terceros incorporados en la aplicación, consultando la información de atribución presentada en la interfaz, y reconociendo la fuente correspondiente cuando esos datos estén disponibles.

**RF-27 — Regreso a Ajustes**

El usuario debe poder regresar al apartado **Ajustes** desde la interfaz de créditos y derechos de autor, utilizando el control de regreso o navegación correspondiente, y retomando la pantalla de configuración.

### Requerimientos de usabilidad (U)

**RNF-U-08 — Claridad de la información legal y de créditos**

La aplicación debe presentar los créditos y la información sobre derechos de autor con títulos y agrupaciones claramente identificables, utilizando una redacción legible y comprensible para los usuarios.

**RNF-U-09 — Acceso sencillo desde Ajustes**

La opción para abrir los créditos y derechos de autor debe estar ubicada de forma visible dentro del apartado **Ajustes**, y debe poder identificarse sin tener que recorrer secciones no relacionadas.

### Requerimientos de confiabilidad (R)

**RNF-R-06 — Integridad de los avisos de autoría y licencia**

La aplicación debe conservar la información de autoría, atribución y licencia asociada con el contenido y los recursos incorporados, evitando omitirla o alterarla durante la actualización del manual o de la aplicación.

### Requerimientos de soportabilidad (S)

**RNF-S-06 — Mantenimiento de créditos y atribuciones**

La información de créditos, derechos de autor y licencias debe mantenerse de forma organizada para permitir su actualización cuando cambien los integrantes, el contenido o los recursos utilizados, sin requerir modificaciones innecesarias en las funciones principales de la aplicación.

### Requerimientos de diseño (+)

**RD-04 — Diseño de la interfaz de créditos**

La interfaz de créditos y derechos de autor debe mantener la consistencia visual del resto de la aplicación, respetar los ajustes de accesibilidad disponibles y ofrecer un control claro para regresar a **Ajustes**.

### Consideraciones de contenido

- Incluir únicamente nombres, roles, atribuciones y datos de contacto que el equipo haya autorizado para su publicación.
- Identificar las licencias aplicables a los textos, imágenes, capturas de pantalla, iconos, bibliotecas y demás recursos de terceros, según corresponda.
- No afirmar que todo el contenido pertenece al equipo si existen materiales sujetos a licencias o derechos de terceros.
- Cuando la información de licencia de un recurso no esté confirmada, verificarla antes de publicar la atribución correspondiente.
