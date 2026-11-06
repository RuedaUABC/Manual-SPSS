# Spec: `content-model`

## Estado

Propuesta para revisión. Este módulo es el primer módulo del mapa aprobado y
no debe avanzar a plan o implementación hasta que esta especificación sea
aprobada.

## Objetivo

Definir un modelo de contenido independiente de PyQt que permita cargar,
validar y consultar el manual de SPSS desde recursos distribuidos con la
aplicación. El módulo será la fuente de verdad para el lector, la navegación,
la búsqueda, los favoritos y la información de créditos/licencias.

El modelo debe conservar la jerarquía del manual, sus cuerpos enriquecidos,
imágenes, tablas, identificadores estables y metadatos de atribución. Debe
funcionar igual desde el árbol de trabajo y desde una aplicación empaquetada
para Windows.

### Requerimientos trazados

- RF-01, RF-02, RF-14 y RF-15: estructura y recursos consultables.
- RF-18: texto indexable para búsquedas posteriores.
- RF-21: identificadores estables para favoritos.
- RF-23 a RF-26: créditos, licencias y atribuciones mantenibles.
- RNF-R-01, RNF-R-02 y RNF-R-03: integridad y errores de carga explícitos.
- RNF-P-01 y RNF-P-04: carga local y texto utilizable por TTS.
- RNF-S-01 a RNF-S-04: contenido sustituible sin modificar la lógica.
- RI-02 a RI-05: separación, identificación y distribución de recursos.

## Supuestos explícitos

1. El contenido oficial estará disponible como archivos locales distribuidos
   junto con la aplicación; la aplicación no dependerá de Internet para
   cargar el manual.
2. El formato canónico de distribución será un `manifest.json` más un archivo
   HTML por sección y una carpeta de recursos locales. HTML permite conservar
   texto enriquecido, tablas e imágenes sin acoplar el contenido a widgets de
   PyQt.
3. Los identificadores de capítulos y secciones serán definidos por el
   equipo editorial y permanecerán estables entre versiones para no invalidar
   favoritos ni enlaces internos.
4. El contenido se entregará en UTF-8 y las rutas de recursos serán relativas
   a la raíz del contenido.
5. La primera versión del instalable usará un bundle Windows de 64 bits con
   PyInstaller en modo `onedir`. El instalador final envolverá ese directorio.
   `onedir` se elige porque permite mantener el contenido como recurso externo
   actualizable y simplifica el diagnóstico de recursos faltantes.
6. El módulo no importará PyQt ni dependerá de Windows; la capa de interfaz
   adaptará el HTML y las rutas locales al componente visual.

## Contrato de contenido

La raíz de contenido tendrá esta forma:

```text
content/
├── manifest.json
├── sections/
│   ├── inicio.html
│   └── que-es-spss.html
└── assets/
    ├── logo-spss.png
    └── captura-01.png
```

El manifiesto tendrá, como mínimo, esta forma lógica:

```json
{
  "schema_version": 1,
  "manual_id": "manual-spss",
  "title": "Manual SPSS",
  "version": "0.1.0",
  "locale": "es-MX",
  "sections": [
    {
      "id": "capitulo-1.inicio",
      "parent_id": null,
      "kind": "chapter",
      "title": "¿Qué es SPSS?",
      "order": 1,
      "body": "sections/inicio.html",
      "search_terms": ["SPSS", "Statistical Package for the Social Sciences"],
      "resources": [
        {
          "path": "assets/logo-spss.png",
          "mime_type": "image/png",
          "alt_text": "Logotipo de SPSS"
        }
      ],
      "attributions": []
    }
  ]
}
```

Reglas del contrato:

- `schema_version`, `manual_id`, `title`, `version`, `locale` y `sections`
  son obligatorios.
- `id` es único, no vacío y limitado a caracteres ASCII seguros para URL o
  almacenamiento (`a-z`, `0-9`, `-`, `_`, `.`).
- `parent_id` debe referir a una sección existente o ser `null` para una raíz.
  No se permiten ciclos ni padres inexistentes.
- `kind` será inicialmente `chapter`, `section` o `subsection`.
- `order` es un entero positivo y define el orden entre hermanos.
- `body` debe apuntar a un archivo `.html` local existente dentro de
  `sections/`; no puede escapar de la raíz mediante `..` ni rutas absolutas.
- `resources[].path` debe ser local, existir y permanecer dentro de `assets/`.
- Las URLs remotas (`http`, `https`, `file`, `javascript`) no serán recursos
  válidos del contenido. El manual debe ser autocontenido y offline.
- `attributions` debe conservar autor, fuente, licencia y URL de referencia
  cuando estén disponibles; no se inventarán datos faltantes.
- Los campos nuevos deberán ser opcionales y aditivos para mantener
  compatibilidad hacia adelante.

## Interfaz pública entre módulos

El contrato se expresará con tipos Python y excepciones específicas, no con
diccionarios sin validar. El nombre exacto de los archivos podrá ajustarse en
el plan, pero la responsabilidad observable será equivalente a la siguiente:

```python
from pathlib import Path
from typing import Protocol


class ContentRepository(Protocol):
    def load(self, root: Path) -> "Manual": ...
    def get_section(self, section_id: str) -> "Section": ...
    def sections_in_reading_order(self) -> tuple["Section", ...]: ...


class Section:
    id: str
    parent_id: str | None
    kind: str
    title: str
    order: int
    body_html: str
    plain_text: str
    resources: tuple["Resource", ...]
    attributions: tuple["Attribution", ...]


class ContentError(Exception): ...
class ContentNotFoundError(ContentError): ...
class ContentValidationError(ContentError): ...
```

Detalles de comportamiento del contrato:

- `load()` valida todo el manifiesto y las referencias locales antes de
  devolver un `Manual`; no entregará un catálogo parcialmente válido.
- `get_section()` lanzará `ContentNotFoundError` cuando el ID no exista.
- Los errores de JSON, UTF-8, esquema, ciclo, ruta insegura o recurso faltante
  se normalizarán a `ContentValidationError` con la ruta y el campo afectado.
- `plain_text` será determinista y se derivará del HTML para que búsqueda y
  TTS no necesiten interpretar HTML por su cuenta.
- El orden de `sections_in_reading_order()` será estable: profundidad de la
  jerarquía y `order` de cada hermano; los empates serán un error de validación.
- La interfaz no expondrá rutas temporales de PyInstaller. El repositorio
  resolverá recursos a partir de la raíz efectiva que le entregue la capa de
  arranque.

## Tech Stack

- Python 3.12 de 64 bits como versión objetivo inicial para Windows 10/11.
- Biblioteca estándar para `json`, `pathlib`, `html.parser`, dataclasses y
  validaciones propias del módulo.
- `pytest` y `pytest-cov` para pruebas.
- `ruff` para formato/lint y `mypy` para comprobación estática.
- PyQt6 quedará fuera de este módulo y será responsabilidad de la capa de UI.
- PyInstaller se reservará para `packaging`, pero este módulo debe poder leer
  una carpeta `content/` externa dentro del directorio instalado.

La decisión de Python 3.12 y PyInstaller se basa en que Python 3.12 tiene
soporte documentado para Windows 8.1 o posterior y PyInstaller empaqueta
aplicaciones con sus dependencias, pero debe ejecutarse en Windows para crear
el bundle de Windows. PyQt6 se mantiene en la capa visual y sus obligaciones
de licencia deberán quedar reflejadas en créditos y documentación.

## Comandos previstos

Los comandos serán ejecutables después de crear el esqueleto del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests/unit/content_model -q
.\.venv\Scripts\python.exe -m pytest --cov=manual_spss --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
```

El comando de empaquetado se definirá en `SPEC-packaging.md`, pero deberá
generar al menos un directorio `dist/ManualSPSS/` que contenga el ejecutable,
dependencias Qt, contenido y recursos gráficos necesarios.

## Estructura de proyecto prevista

```text
src/manual_spss/
├── content_model/
│   ├── __init__.py
│   ├── errors.py
│   ├── models.py
│   ├── repository.py
│   └── validation.py
tests/
├── unit/content_model/
│   ├── test_manifest_validation.py
│   ├── test_repository.py
│   └── test_reading_order.py
content/
├── manifest.json
├── sections/
└── assets/
docs/
└── content-format.md
pyproject.toml
```

La separación entre `content/` y `src/` es obligatoria. El instalador incluirá
ambos como recursos, pero una actualización del manual podrá sustituir
`content/` sin modificar `src/`.

## Estilo de código

Se usarán dataclasses tipadas, nombres descriptivos, `pathlib.Path`, imports
explícitos y excepciones específicas. Las funciones públicas documentarán sus
precondiciones y errores. No se usarán imports globales de PyQt ni efectos
secundarios al importar el paquete.

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Resource:
    """Local resource referenced by a manual section."""

    path: Path
    mime_type: str
    alt_text: str


def ensure_local_resource(root: Path, relative_path: str) -> Path:
    """Resolve a resource or raise a validation error for unsafe paths."""
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise ContentValidationError(
            f"Resource escapes content root: {relative_path}"
        ) from error
    return candidate
```

## Estrategia de pruebas

Se seguirá Red → Green → Refactor con `pytest`:

- Pruebas unitarias para modelos, normalización de texto, resolución segura
  de rutas y reglas del manifiesto.
- Pruebas parametrizadas para IDs inválidos, padres faltantes, ciclos,
  empates de orden, UTF-8 inválido y recursos ausentes.
- Pruebas de integración del repositorio con `tmp_path`, sin depender del
  contenido real ni de Windows.
- Pruebas de contrato que verifiquen que un catálogo válido expone la
  información necesaria para lector, búsqueda, TTS y créditos.
- Cobertura mínima objetivo de 80% para el módulo y 100% para validación de
  rutas, esquema y errores críticos.
- Ninguna prueba llamará a Internet ni a PyQt.

## Límites

- **Siempre:** validar datos en el borde de carga; usar UTF-8; impedir escape
  de rutas; mantener IDs estables; conservar atribuciones; probar primero;
  mantener el módulo independiente de PyQt; verificar que el contenido pueda
  ser leído desde una carpeta instalada.
- **Preguntar antes:** cambiar el formato canónico; eliminar o renombrar
  campos obligatorios; romper la estabilidad de IDs; introducir una base de
  datos; cambiar PyQt6 por otra biblioteca; cambiar la estrategia de bundle;
  publicar contenido o recursos cuya licencia no esté confirmada.
- **Nunca:** ejecutar HTML remoto; aceptar rutas absolutas o `..`; ocultar
  errores de integridad; inventar atribuciones; guardar contenido editable en
  código fuente; incluir secretos o datos de contacto no autorizados.

## Criterios de éxito

1. Un manifiesto válido carga un catálogo completo con capítulos, secciones,
   HTML, texto plano, recursos y atribuciones.
2. Un manifiesto inválido falla antes de exponer cualquier sección y comunica
   la ruta/campo que causó el error.
3. La jerarquía no permite padres inexistentes, ciclos ni empates de orden.
4. Los recursos locales se resuelven dentro de la raíz de contenido y las
   rutas remotas o inseguras son rechazadas.
5. El lector puede obtener una sección por ID y todas las secciones en orden
   de lectura sin importar PyQt.
6. Búsqueda y TTS pueden consumir `plain_text` sin volver a parsear HTML.
7. Los IDs y metadatos de licencia permanecen disponibles para favoritos y
   créditos.
8. El mismo conjunto de pruebas pasa con el contenido en el árbol del
   proyecto y desde una carpeta equivalente a `dist/ManualSPSS/content/`.
9. El módulo mantiene al menos 80% de cobertura y 100% en validaciones
   críticas.

## Preguntas abiertas

1. ¿El proyecto se distribuirá bajo GPLv3 o una licencia compatible con
   PyQt6 GPL, o existe una restricción que obligue a evaluar PySide6/LGPL o
   una licencia comercial de PyQt6?
2. ¿El equipo ya tiene el manual fuente y sus recursos en PDF, HTML u otro
   formato? Esto determinará el conversor editorial, que queda fuera de este
   módulo.
3. ¿Qué versión y política de actualización tendrá el contenido (`semver`,
   fecha o versión institucional)?

## Referencias

- `Manual_SPSS_Requerimientos.md`
- `CAPABILITY-MAP.md`
- Diseño Figma del equipo: <https://www.figma.com/design/31JawBRaqdqo4OH1YJ3qSu/Manual-SPSS?node-id=0-1&t=wbvR5UdOBLjSjaBg-1>
- Python en Windows: <https://docs.python.org/3.12/using/windows.html>
- PyInstaller: <https://www.pyinstaller.org/en/stable/>
- PyQt6: <https://pypi.org/project/PyQt6/>
