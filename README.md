# Manual SPSS

Proyecto para consultar y estudiar el manual de SPSS desde una aplicación de
escritorio. El catálogo local y la primera interfaz de escritorio PyQt6 están
implementados; el motor de voz, las preferencias completas y el instalador se
incorporarán en módulos posteriores.

## Inicio rápido

Se requiere Python 3.12 o posterior. Con `uv`:

```bash
uv sync --extra dev --python 3.12
uv run manual-spss
uv run pytest -q
```

También puedes iniciar el mismo punto de entrada con
`uv run python -m manual_spss`. En Windows, ejecuta `manual-spss` desde el
entorno virtual después de instalar el paquete. La carpeta `content/` debe
estar junto al proyecto o al ejecutable; para seleccionar otra ubicación,
define `MANUAL_SPSS_CONTENT` con la ruta del catálogo.

En Windows también puedes preparar el entorno con `pip`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\manual-spss.exe
```

## Cargar el catálogo

El comando siguiente carga los ocho capítulos y muestra el número de capítulos
y recursos gráficos:

```bash
uv run python -c 'from pathlib import Path; from manual_spss.content_model import ManualRepository; repository = ManualRepository.load(Path("content")); print(repository.manual.title, len(repository.root_sections()), sum(len(section.resources) for section in repository.root_sections()))'
```

Salida esperada para el catálogo actual:

```text
Manual SPSS 8 87
```

El repositorio también puede recibir una ruta explícita como
`dist/ManualSPSS/content/`. La prueba de distribución copia el catálogo a esa
estructura dentro de una carpeta temporal y verifica la carga independiente de
la ruta de desarrollo.

## Comandos de desarrollo

| Comando | Propósito |
| --- | --- |
| `uv run pytest -q` | Ejecutar las pruebas unitarias y de integración. |
| `uv run pytest -q --cov=manual_spss --cov-branch --cov-report=term-missing` | Medir cobertura de líneas y ramas. |
| `uv run ruff check .` | Revisar estilo y errores estáticos. |
| `uv run mypy src/manual_spss` | Verificar tipos. |

Para abrir la interfaz en una máquina Linux sin pantalla y ejecutar su prueba
de integración:

```bash
QT_QPA_PLATFORM=offscreen uv run pytest tests/integration/ui -q
```

La ventana inicial muestra los capítulos del catálogo, controles de navegación,
el selector de tema claro/oscuro y las pantallas de Ajustes. Los controles de
audio se muestran como una vista estática hasta integrar el motor TTS. La
interfaz no importa el modelo de contenido; `app.py` adapta el catálogo al
contrato de vista.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `src/manual_spss/content_model/` | Modelos, validación y repositorio Python puro. |
| `src/manual_spss/ui/` | Ventana PyQt6, pantallas, tokens, temas y recursos Figma locales. |
| `SPEC-ui-foundation.md` | Diseño, interacciones y estados aceptados para la interfaz. |
| `artifacts/ui-foundation/` | Capturas de la ventana en escritorio y tamaño reducido. |
| `src/manual_spss/app.py` | Composición de catálogo e interfaz y punto de entrada. |
| `content/manifest.json` | Metadatos e índice de capítulos. |
| `content/sections/` | Texto HTML seleccionable. |
| `content/assets/` | Imágenes locales con texto alternativo. |
| `docs/source-inventory.md` | Mapa de las 50 páginas PDF y datos de procedencia. |
| `docs/content-format.md` | Esquema, rutas, reglas HTML y carga desde distribución. |
| `tests/` | Pruebas unitarias y de integración, incluida la copia externa del catálogo. |

El paquete `content_model` no importa PyQt ni realiza llamadas de red. La
carpeta `ui/assets/` contiene los recursos visuales en el paquete para que el
ejecutable pueda incluirlos; el catálogo permanece externo y actualizable para
el empaquetado futuro.
