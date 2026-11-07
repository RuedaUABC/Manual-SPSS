# Spec: `reader-navigation`

## Estado

Borrador para revisión. El mapa de capacidades aprobado incluye este módulo. Por
prioridad del equipo se planificará después de `tts-engine`; sus dependencias
`content-model` y `ui-foundation` ya están implementadas.

## Objective

Permitir que estudiantes encuentren y recorran el manual por capítulos,
secciones y subsecciones; sepan dónde están dentro del manual; y consulten el
contenido visual correspondiente sin perder la posición de lectura.

El catálogo actual tiene ocho capítulos raíz y conserva sus encabezados dentro
de HTML. La navegación del lector solo expone esos ocho capítulos. El módulo
debe aprovechar la jerarquía y los identificadores estables del manifiesto para
exponer las divisiones pedagógicas del manual.

## Supuestos para esta propuesta

1. `content-model` y `ui-foundation` están terminados y son contratos estables;
   el modelo de contenido ya admite `chapter`, `section` y `subsection`.
2. El manifiesto será la fuente de verdad para la jerarquía y el orden. La UI no
   inferirá IDs a partir del texto de encabezados al abrir cada pantalla.
3. Se conservarán el estilo y la paleta aprobados en Figma. Se aplicarán los
   criterios Material 3 de legibilidad y adaptación donde no contradigan ese
   diseño.
4. Un elemento del menú representa una división pedagógica navegable. Rótulos
   genéricos como “Pasos”, “Ejemplo” e “Interpretación” permanecen dentro del
   contenido, salvo que el inventario editorial los declare secciones propias.
5. El progreso cuenta las secciones con contenido en orden de lectura; los
   capítulos que agrupan subsecciones no se cuentan otra vez.

## Tech Stack

- Python 3.12 o posterior.
- PyQt6 `>=6.7,<6.12` para la interfaz.
- `content_model` como proveedor de secciones, jerarquía, orden y recursos; la
  capa `ui` continúa aislada y consume modelos de vista.
- Catálogo HTML y recursos locales en `content/`; sin servicio de red.

## Comportamiento y requisitos trazados

- **RF-01, RF-02, RF-14:** el menú muestra capítulos, secciones y subsecciones en
  orden jerárquico; seleccionar una entrada abre su contenido directamente.
- **RF-03, RF-04:** Anterior/Siguiente recorren las entradas con contenido en
  orden de lectura global y se deshabilitan correctamente en los extremos.
- **RF-05:** la vista identifica el título actual y su ruta jerárquica, por
  ejemplo, `Capítulo 7 › 7.2 Gráfico de barras simple`.
- **RF-15:** imágenes, capturas, fórmulas y tablas locales se muestran en el
  orden del HTML de su sección.
- **RF-16:** Inicio vuelve al nodo inicial definido por el catálogo.
- **RF-17:** el progreso indica la posición actual respecto al total de
  secciones con contenido, por ejemplo, `4 de 27`, y una representación visual
  equivalente.
- Mantener la posición de desplazamiento de cada sección cuando se sale y se
  vuelve a ella, siguiendo el comportamiento ya implementado por capítulo.
- Mantener navegación por teclado, foco visible, nombres accesibles y selección
  actual identificable sin depender únicamente del color.
- Refluir la navegación y el panel de lectura en los tamaños de ventana ya
  soportados, sin perder acceso a los rótulos de sección.

## Commands

```bash
uv run --python 3.12 pytest tests/unit/content_model -q
uv run --python 3.12 pytest tests/integration/ui -q
uv run --python 3.12 pytest -q
uv run ruff check .
uv run mypy src/manual_spss
uv run manual-spss
```

## Project Structure

- `content/manifest.json` — IDs estables, jerarquía y orden editorial.
- `content/sections/` — cuerpos HTML de las unidades de lectura.
- `content/assets/` — imágenes y otros recursos locales asociados.
- `src/manual_spss/content_model/` — repositorio y operaciones de jerarquía ya
  disponibles.
- `src/manual_spss/app.py` — adaptación entre repositorio y modelos de vista.
- `src/manual_spss/ui/models.py` — contrato de vista que puede ampliarse sin
  importar el modelo de contenido desde widgets.
- `src/manual_spss/ui/main_window.py` — menú jerárquico, selección, progreso y
  navegación del lector.
- `tests/unit/content_model/` y `tests/integration/ui/` — contrato y flujos Qt.

## Code Style

Conservar dataclasses inmutables para contratos de vista y usar IDs del
manifiesto para las acciones; no usar índices visibles como identidad estable.

```python
@dataclass(frozen=True, slots=True)
class NavigationEntry:
    identifier: str
    title: str
    parent_id: str | None
    depth: int
```

Seguir Ruff (88 columnas), anotaciones completas, nombres `snake_case` y señales
Qt conectadas a métodos pequeños. La adaptación de datos permanece en el punto
de composición de `app.py`.

## Testing Strategy

- **Unidad:** orden de lectura estable, relación padre/hijo, cálculo de posición
  y total, nodos vacíos y límites de anterior/siguiente.
- **Integración Qt:** selección de capítulo y sección; actualización de título,
  ruta y progreso; desplazamiento por teclado; navegación anterior/siguiente;
  preservación de scroll; imágenes y tablas locales; extremos del catálogo.
- **Regresión:** mantener pruebas del tema, inicio, error y estado vacío.
- **Visual:** capturas en 1440×1024 y 1024×768 con capítulo largo y submenú
  expandido, revisadas contra Figma.
- Aplicar Red → Green → Refactor para cada incremento y cerrar con pytest,
  Ruff y mypy.

## Boundaries

- **Always:** conservar IDs estables; respetar el orden del manifiesto; mantener
  HTML y recursos locales; preservar accesibilidad de teclado; no importar
  PyQt desde `content_model`; cotejar cambios editoriales con el manual fuente.
- **Ask first:** cambiar el esquema del manifiesto o los IDs ya publicados;
  reemplazar el diseño de Figma por componentes Material literales; añadir
  dependencias; modificar capítulos cuyo orden o segmentación no se desprenda de
  la fuente.
- **Never:** asignar IDs a partir de rótulos traducibles; duplicar texto para
  representar varios niveles de navegación; cargar recursos remotos; inventar
  contenido o atribuciones.

## Success Criteria

1. Los ocho capítulos y sus divisiones navegables aparecen en orden, con IDs
   estables y sin nodos huérfanos.
2. Seleccionar cualquier nodo con contenido muestra su texto y recursos locales,
   y actualiza título, ubicación jerárquica y progreso.
3. Anterior/Siguiente atraviesan todas las secciones con contenido en el orden
   definido, conservan scroll al regresar y respetan los extremos.
4. Las acciones principales funcionan con teclado y sus estados se anuncian de
   forma accesible.
5. El lector mantiene legibilidad y acceso al menú en 1440×1024 y 1024×768.
6. La suite completa, Ruff y mypy pasan.

## Open Questions

- ¿Confirmas que “Pasos”, “Ejemplo” e “Interpretación” permanezcan como
  encabezados dentro de una sección y no como entradas independientes del menú,
  salvo que el inventario editorial indique que son secciones formales?
- ¿Confirmas que el progreso cuente secciones con contenido y no los capítulos
  agrupadores? Esa es la regla propuesta para evitar contar dos veces el mismo
  contenido.
