# Tareas: `content-model`

Las tareas siguen el orden aprobado en `tasks/plan.md`. Cada implementación
funcional se trabaja en ciclos Red → Green → Refactor: prueba fallida,
implementación mínima y refactor con la suite verde.

## Fase 1: Base y contrato

- [x] **Tarea 1: Preparar el paquete Python y los comandos de calidad**
  - Descripción: crear la estructura `src/`, configurar `pyproject.toml` para
    Python 3.12 y pytest, y dejar documentados los comandos de desarrollo.
  - Aceptación:
    - El paquete `manual_spss` se importa desde el entorno del proyecto.
    - pytest, pytest-cov, Ruff y mypy quedan configurados sin dependencias de
      PyQt en `content-model`.
  - Verificación:
    - `py -3.12 -m pip install -e ".[dev]"`
    - `py -3.12 -m pytest -q`
    - `py -3.12 -m ruff check .`
  - Archivos: `pyproject.toml`, `uv.lock`, `.gitignore`, `README.md`,
    `src/manual_spss/__init__.py`, `tests/conftest.py`.
  - Dependencias: ninguna.
  - Alcance: pequeño.
  - Resultado: verificado con `uv sync --extra dev --python 3.12`,
    `uv run pytest tests/unit/test_package.py -q`, `uv run ruff check .` y
    `uv run mypy src/manual_spss` usando Python 3.12.14.

- [x] **Tarea 2: Definir modelos inmutables y errores del dominio**
  - Descripción: establecer el contrato tipado para Manual, Section, Resource
    y Attribution, junto con errores base, validación y no encontrado.
  - Aceptación:
    - Los modelos rechazan valores estructuralmente inválidos y no exponen
      colecciones mutables.
    - Los errores de carga comparten una excepción base estable.
  - Verificación:
    - `py -3.12 -m pytest tests/unit/content_model/test_models.py -q`
    - `py -3.12 -m mypy src/manual_spss/content_model`
  - Archivos previstos: `src/manual_spss/content_model/__init__.py`,
    `errors.py`, `models.py`, `tests/unit/content_model/test_models.py`.
  - Dependencias: Tarea 1.
  - Alcance: pequeño.
  - Resultado: 16 pruebas de modelos pasan; Ruff y mypy pasan.

## Fase 2: Lectura y validación segura

- [x] **Tarea 3: Convertir HTML local a texto determinista para búsqueda y TTS**
  - Descripción: extraer texto legible de cuerpos HTML con parser de biblioteca
    estándar, ignorando scripts, estilos y etiquetas de presentación.
  - Aceptación:
    - Se preservan espacios entre bloques y texto acentuado en UTF-8.
    - El texto no incluye contenido de `script`, `style` ni comentarios HTML.
  - Verificación:
    - `py -3.12 -m pytest tests/unit/content_model/test_html_text.py -q`
    - `py -3.12 -m ruff check .`
  - Archivos previstos: `src/manual_spss/content_model/html_text.py`,
    `tests/unit/content_model/test_html_text.py`.
  - Dependencias: Tareas 1 y 2.
  - Alcance: pequeño.
  - Resultado: 4 pruebas HTML pasan; Ruff y mypy pasan.

- [x] **Tarea 4: Validar manifiesto y resolver rutas confinadas al contenido**
  - Descripción: validar campos requeridos, tipos, IDs, clases de sección,
    rutas relativas y archivos existentes; bloquear rutas absolutas, escapes y
    esquemas remotos.
  - Aceptación:
    - Errores de JSON, esquema, codificación y recursos se expresan como
      `ContentValidationError` con el campo/ruta asociado.
    - `..`, rutas absolutas, symlinks que salgan del directorio y URLs remotas
      no pueden leer archivos fuera de la raíz.
    - Se valida el catálogo completo antes de devolver resultado alguno.
  - Verificación:
    - `py -3.12 -m pytest tests/unit/content_model/test_validation.py -q`
    - `py -3.12 -m pytest --cov=manual_spss.content_model --cov-report=term-missing`
  - Archivos previstos: `src/manual_spss/content_model/validation.py`,
    `errors.py`, `tests/unit/content_model/test_validation.py`.
  - Dependencias: Tareas 1–3.
  - Alcance: pequeño.
  - Resultado: 24 pruebas de esquema/rutas pasan; Ruff y mypy pasan.

- [x] **Tarea 5: Implementar el repositorio y el orden jerárquico de lectura**
  - Descripción: cargar manifiesto, HTML y recursos locales; construir el
    catálogo; exponer lookup por ID, raíces/hijos y recorrido estable.
  - Aceptación:
    - IDs repetidos, padres ausentes, ciclos y órdenes duplicados entre
      hermanos producen errores de validación.
    - `get_section()` produce `ContentNotFoundError` para IDs inexistentes.
    - El recorrido es estable por orden del hermano y jerarquía, y cada
      sección incluye HTML y `plain_text`.
  - Verificación:
    - `py -3.12 -m pytest tests/unit/content_model/test_repository.py tests/unit/content_model/test_reading_order.py -q`
    - `py -3.12 -m pytest --cov=manual_spss.content_model --cov-report=term-missing`
    - `py -3.12 -m mypy src/manual_spss/content_model`
  - Archivos previstos: `src/manual_spss/content_model/repository.py`,
    `tests/unit/content_model/test_repository.py`,
    `tests/unit/content_model/test_reading_order.py`.
  - Dependencias: Tareas 2–4.
  - Alcance: mediano.
  - Resultado: repositorio tipado, carga integral del catálogo, validación de
    jerarquía y recorrido estable; pruebas de repositorio y orden completas.
    La suite del modelo pasa, la cobertura global supera 80% y la validación
    de `validation.py` alcanza 100% de líneas y ramas; Ruff y mypy pasan.

### Punto de control: catálogo funcional

- [x] Pruebas del módulo verdes y cobertura global ≥80%.
- [x] Rutas, esquema y errores críticos cubiertos al 100%.
- [x] Importación independiente de PyQt y sin llamadas de red.

## Fase 3: Manual fuente y recursos

- [x] **Tarea 6: Crear inventario editorial por página y sección**
  - Descripción: documentar los títulos, páginas, orden de lectura, tablas,
    imágenes y avisos de autoría/licencia disponibles en los cuatro PDF.
  - Aceptación:
    - Los capítulos 1–8 quedan mapeados a páginas de origen.
    - Se distinguen imágenes de contenido de máscaras/logotipos repetidos y
      otros objetos auxiliares del PDF.
    - La información de autoría no disponible queda marcada como no
      confirmada.
  - Verificación: cotejar inventario con `pdfinfo`, `pdftotext` y `pdfimages`
    y revisar visualmente cada página fuente.
  - Archivos previstos: `docs/source-inventory.md`.
  - Dependencias: ninguna; puede hacerse en paralelo con Tareas 1–5.
  - Alcance: pequeño.
  - Resultado: inventario de las 50 páginas cotejado visualmente; mapeo de
    capítulos, capturas y objetos auxiliares; autoría/licencia no confirmada
    documentada sin inferir datos ausentes.

- [x] **Tarea 7: Incorporar capítulos 1 y 2 al catálogo local**
  - Descripción: convertir el primer PDF a contenido HTML seleccionable,
    extraer los recursos visuales que sí pertenecen al contenido y registrar
    IDs/metadatos en el manifiesto.
  - Aceptación:
    - El texto y la jerarquía de ambos capítulos se consultan desde el
      repositorio.
    - Las capturas relevantes se muestran en contexto y se referencian por
      rutas locales con texto alternativo cuando sea identificable.
    - Cada página fuente queda cotejada contra su representación HTML.
  - Verificación:
    - `py -3.12 -m pytest tests/unit/content_model -q`
    - Cotejo visual y de texto usando `docs/source-inventory.md`.
  - Archivos previstos: `content/manifest.json`,
    `content/sections/chapter-1.html`, `content/sections/chapter-2.html` y
    recursos de `content/assets/chapter-1/` y `content/assets/chapter-2/`.
  - Dependencias: Tareas 4–6.
  - Alcance: mediano; dividir el lote de recursos por páginas si excede una
    sesión enfocada.
  - Resultado: capítulos 1–2 con texto HTML, páginas fuente identificadas y
    14 capturas locales con alt text; carga validada por el repositorio.

- [x] **Tarea 8: Incorporar capítulos 3 y 4 al catálogo local**
  - Descripción: convertir el segundo PDF, que incluye pasos ilustrados,
    estadísticas descriptivas y frecuencias, a las secciones del catálogo.
  - Aceptación:
    - Ambos capítulos tienen IDs estables, texto seleccionable y recursos
      asociados a su sección/página.
    - Listas, fórmulas, nombres de opciones y pasos mantienen su orden.
    - Todas las referencias locales se resuelven al cargar el manifiesto.
  - Verificación: pruebas del repositorio y cotejo visual página por página
    con `docs/source-inventory.md`.
  - Archivos previstos: `content/manifest.json`,
    `content/sections/chapter-3.html`, `content/sections/chapter-4.html` y
    recursos de `content/assets/chapter-3/` y `content/assets/chapter-4/`.
  - Dependencias: Tareas 4–7.
  - Alcance: mediano; dividir el lote de recursos por páginas si excede una
    sesión enfocada.
  - Resultado: capítulos 3–4 con pasos, resultados y 30 capturas locales;
    términos de estadística y orden de lectura verificados.

- [x] **Tarea 9: Incorporar capítulos 5 y 6 al catálogo local**
  - Descripción: convertir el tercer PDF y preservar encabezados, ejemplos,
    símbolos estadísticos, tablas y capturas.
  - Aceptación:
    - Los capítulos se encuentran con búsqueda de texto plano y se pueden
      narrar en orden natural.
    - Las figuras/tablas locales están asociadas a la sección correcta.
    - El manifiesto no asigna licencias o autores que la fuente no confirme.
  - Verificación: pruebas del repositorio y cotejo visual página por página
    con `docs/source-inventory.md`.
  - Archivos previstos: `content/manifest.json`,
    `content/sections/chapter-5.html`, `content/sections/chapter-6.html` y
    recursos de `content/assets/chapter-5/` y `content/assets/chapter-6/`.
  - Dependencias: Tareas 4–8.
  - Alcance: mediano; dividir el lote de recursos por páginas si excede una
    sesión enfocada.
  - Resultado: capítulos 5–6 con hipótesis, fórmulas, procedimientos, tablas y
    16 imágenes locales; sin atribuciones de autoría o licencia no confirmadas.

- [x] **Tarea 10: Incorporar capítulos 7 y 8 al catálogo local**
  - Descripción: convertir el cuarto PDF y asociar los ejemplos ilustrados de
    creación de gráficos con sus secciones.
  - Aceptación:
    - Los capítulos quedan completos en jerarquía, texto, imágenes y orden.
    - El catálogo carga sin referencias rotas y los recursos son locales.
    - Cada página fuente queda cotejada contra la representación HTML.
  - Verificación: pruebas del repositorio y cotejo visual página por página
    con `docs/source-inventory.md`.
  - Archivos previstos: `content/manifest.json`,
    `content/sections/chapter-7.html`, `content/sections/chapter-8.html` y
    recursos de `content/assets/chapter-7/` y `content/assets/chapter-8/`.
  - Dependencias: Tareas 4–9.
  - Alcance: mediano; dividir el lote de recursos por páginas si excede una
    sesión enfocada.
  - Resultado: capítulos 7–8 con procedimientos ilustrados, gráficos y
    resultados de correlación; 27 imágenes locales cotejadas visualmente.

### Punto de control: corpus completo

- [x] Capítulos 1–8 cargan y recorren en orden sin errores.
- [x] Todas las páginas están representadas o documentadas como material
  introductorio/portada deliberadamente omitido.
- [x] No existen imágenes remotas ni rutas fuera de `content/`.
- [x] Texto plano conserva términos, listas y orden útiles para búsqueda/TTS.

## Fase 4: Distribución y documentación

- [x] **Tarea 11: Documentar formato y comprobar carpeta externa de distribución**
  - Descripción: documentar el manifiesto, IDs, HTML, recursos y errores; probar
    que el mismo catálogo carga desde el árbol del proyecto y desde una copia
    simulada en la ruta futura del bundle.
  - Aceptación:
    - El formato documentado coincide con el validador.
    - El catálogo y sus recursos cargan bajo
      `dist/ManualSPSS/content/` sin depender de la ruta de desarrollo.
    - Los comandos de test, lint y tipos están documentados en README.
  - Verificación:
    - `py -3.12 -m pytest --cov=manual_spss.content_model --cov-report=term-missing`
    - `py -3.12 -m ruff check .`
    - `py -3.12 -m mypy src`
  - Archivos previstos: `docs/content-format.md`,
    `tests/integration/content_model/test_distribution_layout.py`,
    `README.md`.
  - Dependencias: Tareas 1–10.
  - Alcance: pequeño.
  - Resultado: `docs/content-format.md` describe el esquema 1 y coincide con
    el validador; README incluye inicio rápido y comandos; la prueba copia y
    carga el catálogo bajo una raíz temporal `dist/ManualSPSS/content/`.
    Verificado con 83 pruebas, Ruff y mypy.

### Punto de control: `content-model` listo

- [x] Criterios de éxito de `SPEC-content-model.md` cumplidos.
- [x] Cobertura total ≥80% y validación crítica al 100%.
- [x] Catálogo de capítulos 1–8 íntegro y local.
- [x] La carga desde `dist/ManualSPSS/content/` se verificó en la tarea 11.
- [x] Módulo revisado antes de iniciar `reader-navigation`.

## Fase 5: Base de interfaz

- [x] **Tarea 12: Implementar `ui-foundation` con PyQt6**
  - Descripción: crear la ventana ejecutable, navegación del lector, pantallas
    base de Ajustes, temas claro/oscuro y adaptación del catálogo validado.
  - Aceptación:
    - La ventana lee los capítulos locales, cambia entre capítulos y abre/cierra
      Ajustes sin que los widgets dependan de `content_model`.
    - La apariencia claro/oscuro actualiza los paneles, controles y HTML.
    - Los recursos Figma se guardan localmente y viajan como datos del paquete.
    - La aplicación abre desde `manual-spss` y permite una futura distribución
      `onedir` con `content/` externo.
    - Los controles de audio y ajustes de voz informan que dependen del módulo
      TTS todavía pendiente.
  - Verificación: `uv run pytest -q`, `uv run ruff check .`,
    `uv run mypy src/manual_spss` y capturas en 1440×1024 y 1024×768.
  - Archivos: `src/manual_spss/ui/`, `src/manual_spss/app.py`,
    `src/manual_spss/__main__.py`, `SPEC-ui-foundation.md` y README.
  - Dependencias: `content-model`; PyQt6 se fija debajo de 6.12 por errores de
    sintaxis en los stubs de esa versión al analizar con mypy.
  - Resultado: lector y pantallas base de Ajustes, temas claro/oscuro,
    navegación por teclado, ruta CLI, catálogo externo y recursos incluidos en
    el wheel. Ocho pruebas de UI; 91 pruebas totales con 93% de cobertura de
    líneas/ramas, Ruff y mypy verdes. Capturas revisadas en 1440×1024 y
    1024×768; el comprobador ECC de evidencia pasa.

### Punto de control: `ui-foundation` listo

- [x] Lector local y pantallas base de Ajustes abren desde el punto de entrada.
- [x] Los temas claro/oscuro actualizan el contenido y la interfaz.
- [x] Navegación con teclado y accesibilidad básica revisadas.
- [x] Los recursos visuales están incluidos en el wheel; `content/` sigue
  externo y localizable para distribución posterior.
- [x] Capturas y estados visibles registrados en `artifacts/ui-foundation/`.
