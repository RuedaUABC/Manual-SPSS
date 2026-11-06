# Formato del catálogo del Manual SPSS

El contenido se distribuye como una carpeta independiente de `src/`. El
arranque de la aplicación entregará al repositorio una ruta explícita; el
repositorio no deduce rutas de instalación ni depende del directorio actual.
Esto permite cargar el mismo catálogo desde el árbol de desarrollo y desde
`dist/ManualSPSS/content/`.

## Estructura de carpetas

```text
content/
├── manifest.json
├── sections/
│   ├── chapter-1.html
│   └── ...
└── assets/
    ├── chapter-1/
    │   └── page-02-figure-01.png
    └── ...
```

`manifest.json` es el índice del catálogo. Cada sección refiere a un cuerpo
HTML bajo `sections/`; sus recursos se declaran bajo `assets/`. Los PDF fuente
no son dependencias en tiempo de ejecución.

## Manifiesto, esquema 1

La codificación del manifiesto y los cuerpos HTML es UTF-8. El esquema 1
requiere estos campos de nivel superior:

| Campo | Tipo y regla |
| --- | --- |
| `schema_version` | Entero positivo; la implementación actual acepta `1`. |
| `manual_id` | Cadena no vacía que identifica el catálogo. |
| `title` | Cadena no vacía. |
| `version` | Cadena no vacía; el cargador no impone SemVer. |
| `locale` | Cadena no vacía, por ejemplo `es-MX`; no se valida contra una lista de locales. |
| `sections` | Lista no vacía de secciones. |

Cada sección contiene:

| Campo | Tipo y regla |
| --- | --- |
| `id` | ID único en el catálogo; debe comenzar con una letra ASCII minúscula o dígito y continuar con minúsculas, dígitos, `.`, `_` o `-`. |
| `parent_id` | Campo requerido: ID de otra sección o `null` para una raíz. |
| `kind` | `chapter`, `section` o `subsection`. |
| `title` | Cadena no vacía. |
| `order` | Entero positivo. Los hermanos no pueden repetir el mismo orden. |
| `body` | Ruta POSIX existente dentro de `sections/`, con extensión `.html`. |
| `search_terms` | Opcional; lista de cadenas no vacías para sinónimos y términos de búsqueda. |
| `resources` | Opcional; lista de recursos locales declarados por la sección. |
| `attributions` | Opcional; lista de datos de autoría/procedencia disponibles. |

Un recurso contiene `path` (ruta POSIX existente bajo `assets/`), `mime_type`
(cadena con forma `tipo/subtipo`) y `alt_text` (cadena, vacía si no se conoce).
El cargador comprueba la forma del MIME declarado; no inspecciona los bytes
para comprobar que coincidan con ese MIME. Conviene describir cada imagen con
un texto alternativo útil.

Cada atribución acepta los campos opcionales `author`, `source`, `license` y
`url`, cada uno como cadena o `null`. Se dejan vacíos los datos que la fuente
no confirma; el formato no asigna una licencia por defecto.

Los campos opcionales pueden omitirse. El cargador ignora campos desconocidos
para permitir extensiones aditivas. Los IDs y el orden sí forman parte del
contrato: conservarlos mantiene referencias estables para favoritos y
navegación.

### Ejemplo

```json
{
  "schema_version": 1,
  "manual_id": "manual-spss",
  "title": "Manual SPSS",
  "version": "0.1.0",
  "locale": "es-MX",
  "sections": [
    {
      "id": "chapter-1",
      "parent_id": null,
      "kind": "chapter",
      "title": "Introducción al SPSS",
      "order": 1,
      "body": "sections/chapter-1.html",
      "search_terms": ["iniciar SPSS", "vista de datos"],
      "resources": [
        {
          "path": "assets/chapter-1/page-02-figure-01.png",
          "mime_type": "image/png",
          "alt_text": "Resultado de búsqueda de IBM SPSS Statistics 25 en Windows."
        }
      ],
      "attributions": [
        {
          "author": null,
          "source": "cap1y2_SPSS.pdf, páginas 1–4",
          "license": null,
          "url": null
        }
      ]
    }
  ]
}
```

El fragmento HTML referencia imágenes desde la ubicación del propio archivo
HTML. En `sections/chapter-1.html`, la imagen del ejemplo anterior se enlaza
con `../assets/chapter-1/page-02-figure-01.png`:

```html
<article>
  <h1>Introducción al SPSS</h1>
  <p>SPSS permite organizar y analizar datos.</p>
  <figure>
    <img
      src="../assets/chapter-1/page-02-figure-01.png"
      alt="Resultado de búsqueda de IBM SPSS Statistics 25 en Windows."
    >
    <figcaption>Fuente: página 2 del PDF original.</figcaption>
  </figure>
</article>
```

## Jerarquía y orden de lectura

El repositorio comprueba que cada padre exista, que la jerarquía no tenga
ciclos y que los hermanos tengan órdenes distintos. Las raíces se ordenan por
`order`; `sections_in_reading_order()` devuelve un recorrido en profundidad,
respetando el orden de cada grupo de hermanos. `children_of(id)` obtiene los
hijos directos y genera `ContentNotFoundError` si el ID no existe.

El campo `kind` etiqueta las entradas; el cargador no impone que la profundidad
de una entrada coincida con ese campo. El catálogo puede tener capítulos,
secciones y subsecciones con HTML independiente cuando la navegación lo
requiera.

## Rutas y contenido HTML

Las rutas del manifiesto usan `/` y son relativas a la raíz `content/`.
`body` debe permanecer bajo `sections/`; los recursos deben permanecer bajo
`assets/`. Se rechazan rutas absolutas, `..`, separadores `\`, URLs como rutas
de archivo, segmentos vacíos o `.`, los caracteres `:`, `?` y `#`, archivos
inexistentes y enlaces simbólicos que salgan de esas carpetas.

El cuerpo es un fragmento HTML UTF-8. El validador rechaza elementos activos
como `script`, `iframe`, `object`, `form`, `audio`, `video` y `style`; también
rechaza atributos `on*`, estilos en línea, y `srcset`, `poster` y `data`. El
atributo `src` solo se admite en `<img>` y debe apuntar a un recurso local
declarado en la misma sección. Los esquemas `javascript:`, `data:` y `file:` se
rechazan en `href`. El modelo no navega ni descarga enlaces; la capa visual
decide cómo presentar la navegación externa.

`plain_text` se deriva del HTML al cargar el catálogo: normaliza espacios y
conserva separaciones entre bloques para búsqueda y texto a voz. No se guarda
una copia de texto plano en el manifiesto.

## API de carga

El llamador elige la raíz y la pasa explícitamente:

```python
from pathlib import Path

from manual_spss.content_model import ManualRepository

repository = ManualRepository.load(Path("content"))
chapter = repository.get_section("chapter-1")
print(chapter.title)
print(chapter.plain_text)
print(repository.sections_in_reading_order())
```

Para una carpeta externa del bundle, se pasa `Path("dist/ManualSPSS/content")`.
El repositorio valida el manifiesto, todas las rutas, cada cuerpo HTML y la
jerarquía antes de devolver el catálogo. Los errores de lectura o integridad
se informan como `ContentValidationError`; no se entrega un catálogo parcial.

## Prueba de distribución

`tests/integration/content_model/test_distribution_layout.py` copia el
catálogo de desarrollo a una carpeta temporal con la estructura
`dist/ManualSPSS/content/`, lo carga desde esa ruta explícita y comprueba que
todos los recursos resueltos pertenezcan a la copia. Se ejecuta junto con la
suite:

```bash
uv run pytest -q
```

Esta prueba valida el layout de contenido independiente. No genera un
instalador ni un bundle PyInstaller.
