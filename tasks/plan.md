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
