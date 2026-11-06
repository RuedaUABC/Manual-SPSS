# Manual SPSS

Aplicación de escritorio para consultar y estudiar el manual de SPSS. El
contenido se mantiene separado del código para facilitar su actualización y
la futura distribución como instalador de Windows.

## Desarrollo

Se requiere Python 3.12 o posterior.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Comandos de calidad

```powershell
py -3.12 -m pytest -q
py -3.12 -m pytest --cov=manual_spss.content_model --cov-report=term-missing
py -3.12 -m ruff check .
py -3.12 -m mypy src/manual_spss/content_model
```

La especificación y el mapa del proyecto están en `SPEC-content-model.md` y
`CAPABILITY-MAP.md`. El formato del catálogo y su contenido se documentarán
en `docs/content-format.md`.
