# Plan de implementación: `content-model`

## Resumen

Crear el modelo y repositorio local que validan el catálogo del Manual SPSS,
exponen cada sección en orden de lectura y entregan HTML, texto plano,
recursos y atribuciones a las capacidades consumidoras. El contenido inicial
se curará desde los cuatro PDF suministrados (capítulos 1–8, 50 páginas) y se
distribuirá como una carpeta externa al código, compatible con el futuro
instalador Windows.

## Decisiones de arquitectura

- Mantener `content-model` como paquete Python puro, sin PyQt ni dependencias
  de Windows.
- Usar `manifest.json` versionado, archivos HTML locales por sección y
  recursos gráficos bajo `content/assets/`.
- Mantener los PDF originales como fuentes editoriales, no como dependencias
  de ejecución. Generar el contenido de la app offline y revisar su estructura
  y capturas contra las páginas originales.
- Resolver el directorio de contenido desde la capa de arranque. El modelo
  recibe una ruta explícita y no conoce las rutas temporales de PyInstaller.
- Mantener el contenido fuera del ejecutable principal para permitir que un
  instalador o actualización sustituya `content/` sin cambiar la lógica.
- Usar PyQt6 en la aplicación conforme a la decisión del equipo. Los créditos
  seguirán la pantalla de Figma e incluirán los avisos aplicables de PyQt6;
  la aplicación no asignará una licencia global nueva al contenido del manual.
- Aplicar Red → Green → Refactor en cada incremento funcional.

## Orden de trabajo

### Fase 1: Contrato y modelos

Definir dataclasses inmutables para manual, sección, recurso y atribución;
excepciones de dominio; formato del manifiesto y reglas de compatibilidad de
esquema.

**Verificación:** pruebas de modelos y contrato para datos válidos e inválidos.

### Fase 2: Carga y validación integral

Implementar lectura UTF-8, validación del esquema, normalización HTML a texto
plano, referencias a archivos locales, prevención de escape de rutas,
integridad de recursos, jerarquía sin ciclos y orden estable.

**Verificación:** pruebas unitarias de cada regla y pruebas de repositorio con
directorios temporales; ningún catálogo parcial se publica ante errores.

### Fase 3: Catálogo consultable

Exponer acceso por ID, raíces e hijos, secciones en orden de lectura y
resolución de recursos. Mantener texto y metadatos de atribución disponibles
para lector, búsqueda, TTS, favoritos y créditos.

**Verificación:** pruebas de contrato de las operaciones públicas y del orden
de lectura de capítulos, secciones y subsecciones.

### Fase 4: Incorporación del manual fuente

Inventariar títulos, estructura, texto e imágenes de los cuatro PDF; convertir
el contenido a secciones HTML locales; crear el manifiesto con IDs estables,
metadatos disponibles y referencias de recursos; revisar visualmente cada
sección contra el PDF fuente.

**Verificación:** comprobar que están representados los capítulos 1–8, que
todas las referencias del manifiesto resuelven y que una lista de control por
página detecta páginas o recursos omitidos. La conversión conservará el texto
en forma seleccionable para búsqueda y TTS.

### Fase 5: Preparación para distribución

Documentar el contrato del contenido y verificar que el repositorio lo carga
desde `content/` tanto en el árbol de trabajo como desde una carpeta de
distribución simulada `dist/ManualSPSS/content/`.

**Verificación:** ejecutar el mismo conjunto de pruebas sobre ambas rutas y
confirmar que los recursos resueltos permanecen dentro de la carpeta externa.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La extracción de PDF intercale columnas o listas | Alto: lectura, búsqueda y TTS incorrectos | Revisar texto por página, comparar con el PDF y corregir el HTML manualmente cuando haga falta. |
| Capturas embebidas no se asignen a la sección correcta | Alto: pérdida de contexto visual | Inventariar y validar cada imagen por página; guardar alt text descriptivo cuando se conozca. |
| El formato de PDF varíe entre capítulos | Medio: importación inconsistente | Tratar los PDF como fuentes editoriales, no diseñar un convertidor general que dependa del layout. |
| Se actualice el catálogo sin mantener IDs | Alto: favoritos y enlaces dejan de apuntar a su sección | Definir IDs estables y comprobar duplicados antes de cargar el catálogo. |
| Recursos del contenido se incluyan dentro de una ruta temporal del bundle | Alto: el contenido instalado deja de ser actualizable | Exigir una raíz explícita y probar la ubicación externa de `content/`. |
| No se confirma autoría/licencia de un elemento de origen | Medio: aviso incompleto | Conservar la información disponible y marcar lo demás como no confirmado, sin inventar una licencia. |

## Hitos de revisión

1. Contrato y modelos listos antes de implementar el repositorio.
2. Repositorio completo y validaciones críticas con cobertura integral antes
   de incorporar el corpus PDF.
3. Catálogo de capítulos 1–8 íntegro antes de conectar lector y búsqueda.
4. Prueba de carga desde la ruta de distribución antes de iniciar
   `packaging`.

## Comandos de verificación previstos

```powershell
py -3.12 -m pytest tests/unit/content_model -q
py -3.12 -m pytest --cov=manual_spss.content_model --cov-report=term-missing
py -3.12 -m ruff check .
py -3.12 -m mypy src/manual_spss/content_model
```

## Fuentes

- `SPEC-content-model.md`
- `Manual_SPSS_Requerimientos.md`
- `Manual SPSS original/` (capítulos 1–8, cuatro PDF)
- Diseño de Figma del equipo

---

# Plan de implementación: `tts-engine`

## Resumen

Implementar la lectura offline del manual en español con Piper y dos modelos
locales seleccionables: español de México (`es_MX-ald-medium`) y español de
España (`es_ES-davefx-medium`). El reproductor existente conservará su
presentación y pestaña plegable, pero sus controles dejarán de ser una imagen
decorativa. El usuario aprobó el motor, las voces, el tamaño aproximado de
126 MB y los avisos GPL/modelo en el instalador futuro.

## Estado y límites

- Spec aprobada: `SPEC-tts-engine.md`.
- Las preferencias de voz/velocidad son de sesión; persistirlas queda para
  `settings-accessibility`.
- No guardar pesos grandes en Git ni descargar desde la aplicación. Un comando
  de desarrollo/distribución obtendrá recursos fijados por versión y SHA-256;
  la app los cargará del disco local.
- No modificar todavía el plan completado de `content-model` ni cerrar sus
  tareas. Este documento mantiene ambos módulos como historial del proyecto.
- No incluir el instalador completo en esta entrega; `packaging` añadirá los
  recursos y avisos a la futura distribución.

## Arquitectura y orden de implementación

### 1. Viabilidad de Piper, formatos y recursos

Fijar una versión de `piper-tts` compatible con Python 3.12 y Windows x64;
verificar su API por fragmentos, salida PCM y parámetros de velocidad. Añadir
un manifiesto para las dos voces con URL inmutable, versión/revisión, archivos
`.onnx`/`.onnx.json`, SHA-256 y ficha de licencia. Crear un comando de
desarrollo para descargar y validar los archivos y conservar los avisos.

Este tramo es primero porque el tamaño, la licencia y la integración ONNX
condicionan el futuro instalador. Comprobar la síntesis de una muestra en CPU
antes de completar la integración visual.

### 2. Contratos TTS y ciclo de vida

Crear los tipos `VoiceInfo`, solicitud de lectura, `AudioChunk` y estados; un
protocolo de motor; un adaptador Piper que reciba rutas de recursos explícitas;
y un motor falso para pruebas. La cancelación debe invalidar solicitudes
anteriores y evitar que fragmentos tardíos vuelvan a sonar. El motor no debe
depender de widgets ni importar PyQt en su núcleo.

### 3. Salida de audio y controles funcionales

Conectar el productor Piper en segundo plano a una cola acotada de PCM y a
`PyQt6.QtMultimedia.QAudioSink`. Separar los comandos de reproducción de la
síntesis: pausa/reanudación actúan en la salida y detienen el avance del
productor en el siguiente límite de fragmento; detener descarta la cola. Medir
progreso desde el audio consumido, no desde lo ya sintetizado. Probar pronto el
formato de audio y el dispositivo real en Windows; Linux puede cubrir la lógica
con fakes aunque no haya salida de audio disponible.

### 4. Adaptación del texto y composición

Extender `ManualPage` con `plain_text` y pasarlo desde `Section.plain_text` en
`load_manual_pages`. La solicitud usa el texto seleccionado del
`QTextBrowser` cuando exista; normaliza separadores de párrafo Qt. Si no hay
selección, usa el texto plano completo de la página activa. El título separado
del cuerpo no se enviará al motor como HTML.

Construir/injectar el servicio desde `app.py` de forma tolerante a recursos
ausentes: el manual debe abrir aunque TTS no cargue. En ese caso se informa el
problema en la zona de voz/reproductor, sin voz alternativa en otro idioma.

### 5. Integración de interfaz y ajustes

Reemplazar `_AudioPreview` por controles accesibles sobre la composición visual
actual y mantener su pestaña de mostrar/ocultar. Enlazar reproducir, pausa,
detener, reiniciar, velocidad, volumen/silencio y progreso con el estado del
servicio. Convertir el marcador actual **Ajustes > Voz** en selector de los dos
modelos y botón de muestra en español. Aplicar voz nueva en la siguiente
reproducción.

### 6. Aceptación y regresión

Completar pruebas unitarias e integración Qt en Linux con motor/audio falsos;
ejecutar suite completa, Ruff y mypy. Hacer smoke test en Windows 10/11 x64 sin
Internet con los dos modelos locales: escuchar muestra/selección/página y
verificar controles, cierre y ausencia de bloqueo. Registrar cualquier
limitación del entorno Linux para no confundirla con una regresión del motor.

## Dependencias entre componentes

```text
manifiesto y recursos fijados ──> adaptador Piper ──> productor/cola PCM
texto plano y selección ────────> solicitud TTS ────┘
cola PCM ──> QAudioSink ──> controles, progreso y estados Qt
voz local ──> Ajustes > Voz / muestra
composición de app ──> servicio TTS tolerante a error ──> UI
```

La secuencia es principalmente serial porque el adaptador fija el contrato de
audio que consumen la cola y la UI. En paralelo pueden prepararse los casos de
prueba del adaptador falso y las pruebas de la adaptación `ManualPage` una vez
definidos sus tipos.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Piper/ONNX o los modelos fallan en Windows empaquetado | Alto: no habría lectura offline | Validar primero Python 3.12 y Windows x64; fijar versiones/checksums y reservar smoke test Windows. |
| QAudioSink no acepta el formato o la cola presenta cortes | Alto: audio interrumpido | Prototipar formato PCM y cola acotada antes de cerrar UI; separar generación y consumo. |
| Parada compite con fragmentos en curso | Alto: audio residual | Token de generación por solicitud, cancelación cooperativa y pruebas de carrera. |
| Bundle crece ~126 MB más dependencias | Medio: instalación grande | Mantener voces fuera del ejecutable principal y cuantificar bundle al llegar a packaging. |
| Licencia GPL/voz omitida | Alto: distribución incompleta | Incluir COPYING, fichas, avisos y revisión de requisitos antes de publicar. |
| Modelos todavía no descargados al abrir desde el repo | Medio: TTS no se puede probar localmente | Comando de preparación explícito; error recuperable en UI y fakes para pruebas comunes. |

## Puntos de control

1. **Motor base:** dependencias y assets verificables; síntesis de una muestra
   local; tests del contrato con fake verdes.
2. **Audio:** cola acotada, pausa/detención/progreso cubiertos; smoke de audio
   reproducible en Windows antes de integrar toda la UI.
3. **Flujo de usuario:** selección/página, selector y muestra de voz conectados;
   UI responde y los controles corresponden al estado real.
4. **Cierre:** suite, Ruff y mypy verdes; verificación offline de ambas voces;
   licencias locales presentes.

## Verificación prevista

```bash
uv run --python 3.12 pytest tests/unit/tts_engine -q
uv run --python 3.12 pytest tests/integration/tts -q
uv run --python 3.12 pytest -q
uv run ruff check .
uv run mypy src/manual_spss
```

Windows: instalar/preparar recursos con el comando de desarrollo una sola vez;
después iniciar la app sin Internet y comprobar las dos voces, selección de
texto, reproductor, preferencias de sesión y cierre.
