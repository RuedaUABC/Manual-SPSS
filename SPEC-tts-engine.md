# Spec: `tts-engine`

## Estado

Aprobada por el usuario el 2026-11-06. La lectura en español es indispensable,
con preferencia por varias voces en Ajustes. `content-model` y `ui-foundation`
están implementados; TTS se adelanta a `reader-navigation` según
`CAPABILITY-MAP.md`.

## Objetivo

Permitir escuchar una sección del Manual SPSS o solo el texto seleccionado.
Incluir reproducción, pausa, reanudación, detención, reinicio, velocidad,
volumen y progreso. La ventana debe seguir respondiendo mientras se sintetiza y
reproduce voz.

## Requisitos obligatorios

1. Toda lectura generada por la aplicación debe estar en español. No usar una
   voz en inglés como sustitución silenciosa cuando falten archivos o falle el
   motor.
2. Incluir al menos dos voces españolas locales en la distribución, disponibles
   sin conexión y seleccionables desde **Ajustes > Voz**. Mostrar el idioma y la
   región del modelo.
3. Incluir una escucha de muestra para comparar las voces antes de iniciar la
   lectura.
4. No enviar texto del manual a servicios remotos ni descargar modelos durante
   la ejecución normal de la aplicación.
5. Si un modelo no se puede cargar, mostrar un error recuperable y mantener la
   aplicación disponible.

## Propuesta técnica

- Objetivo: Windows 10/11 x64, Python 3.12 o posterior, PyQt6.
- Motor local: `piper-tts` con ONNX Runtime. Piper publica ruedas Python para
  Windows y ofrece síntesis en fragmentos; no requiere que el usuario instale
  voces de Windows.
- Voces iniciales incluidas:
  - `es_MX-ald-medium`: español de México, modelo de calidad media, ~63.2 MB.
  - `es_ES-davefx-medium`: español de España, modelo de calidad media,
    ~63.2 MB.
- Los modelos comparten el motor, pero son dos modelos de voz independientes.
  La voz elegida se identifica en Ajustes con región y nombre de modelo; no se
  deduce ni se promete género a partir del nombre.
- Cada voz se distribuye con su configuración `.onnx.json` y su ficha de
  licencia. La ficha de `ald` declara Unlicense para su conjunto de datos; la
  ficha de `davefx` declara CC0. El motor Piper actual es GPL-3.0-or-later. La
  carpeta de distribución deberá incluir sus avisos y licencias, además de los
  avisos de terceros aplicables.
- Los pesos no se guardan en Git. Un manifiesto de recursos fijará las URLs,
  versiones y SHA-256 de cada archivo; un comando de desarrollo/paquete los
  obtiene antes de generar la distribución. La aplicación solo los carga desde
  la carpeta local `assets/tts/voices/` y no accede a la red.
- Usar `PyQt6.QtMultimedia.QAudioSink` (incluido con PyQt6 en el entorno del
  proyecto) para emitir PCM. Piper sintetiza fuera
  del hilo de UI en fragmentos acotados; la cola de audio también tiene límite
  para evitar acumular una sección completa en memoria. Los eventos de control,
  error y progreso cruzan a la UI mediante señales Qt.
- Aplicar Red → Green → Refactor por incremento. Los tests Linux usan un motor
  falso; Windows valida Piper y audio real.

## Comportamiento

- **Leer:** lee el texto seleccionado si no está vacío; en otro caso, lee el
  texto plano de la sección actual. El título puede anunciarse antes del cuerpo
  si forma parte del texto entregado por el modelo de contenido.
- **Voz:** ofrecer como mínimo las dos voces incluidas. Mostrar, por ejemplo,
  «Español (México) — Ald» y «Español (España) — Davefx». Cambiar la voz afecta
  a la siguiente reproducción. El selector forma parte de **Ajustes > Voz**.
- **Probar voz:** reproducir una muestra breve en español con la voz elegida;
  no requiere conexión y no modifica la sección activa.
- **Pausa/Reanudar:** detener inmediatamente la salida y continuar desde el
  audio pendiente. La generación se suspende al límite del fragmento actual y
  la cola permanece acotada.
- **Detener:** cancela la solicitud, descarta audio pendiente y deja el estado
  en detenido; ningún fragmento tardío debe reanudar la lectura.
- **Reiniciar:** inicia de nuevo el mismo texto desde el comienzo.
- **Velocidad:** mostrar lenta, normal y rápida; traducirlas a valores Piper
  calibrados y mantener las etiquetas iguales para todas las voces.
- **Volumen/silencio:** aplicar el volumen de salida y permitir silenciar y
  restaurar el valor anterior.
- **Progreso:** actualizar según los fotogramas de audio reproducidos. En esta
  entrega es informativo y no permite buscar una posición.
- **Estados:** `idle`, `starting`, `playing`, `paused`, `stopped`, `finished` y
  `error`. Cada transición actualiza controles, nombres accesibles y mensaje
  visible.
- Al cerrar la ventana se detiene la síntesis, se vacía la cola y se libera el
  dispositivo de audio.
- Si el audio no está disponible, falta un modelo o el texto está vacío, mostrar
  una explicación clara y una acción de recuperación apropiada. No sustituir
  una voz española por una voz del sistema o de otro idioma.
- La elección de voz y velocidad vive en la sesión de TTS. Su persistencia al
  reiniciar la aplicación se conecta con `settings-accessibility`.

## Comandos de desarrollo y verificación

```bash
uv run --python 3.12 pytest tests/unit/tts_engine -q
uv run --python 3.12 pytest tests/integration/tts -q
uv run --python 3.12 pytest -q
uv run ruff check .
uv run mypy src/manual_spss
uv run manual-spss
```

La prueba manual de voz real se ejecutará en Windows 10/11 x64, sin Internet,
con ambos modelos incluidos en los recursos locales. Se comprobarán voz,
reproducción, pausa, reanudación, detención, reinicio, volumen y cierre.

## Estructura prevista

- `src/manual_spss/tts_engine/` — contrato, estados, solicitudes, adaptador
  Piper y puente de audio Qt.
- `src/manual_spss/app.py` — composición e inyección del servicio y paso de
  `Section.plain_text` al adaptador de UI.
- `src/manual_spss/ui/models.py` — transportar texto plano junto al HTML en
  `ManualPage`.
- `src/manual_spss/ui/main_window.py` — selección de texto, controles del
  reproductor, mensajes y selector/muestra de voz en Ajustes > Voz.
- `assets/tts/voices/` — modelos ONNX, configuraciones, fichas de licencia y
  manifiesto de checksums para desarrollo y distribución.
- `scripts/fetch_tts_assets.py` — descargar y validar recursos solo durante el
  desarrollo o la preparación del paquete.
- `tests/unit/tts_engine/` — transiciones, cola, selección, velocidad y errores
  con motor falso.
- `tests/integration/tts/` — señales Qt, reproducción simulada y prueba real de
  Piper marcada para Windows.
- `pyproject.toml` — dependencia de Piper; reutilizar PyQt6 Multimedia.
- Módulo futuro `packaging` — incluir modelos, configuración y avisos en el
  instalador; verificar que arranque offline.

## Estilo de código

El contrato desacopla el motor de los widgets. Los objetos ONNX y el estado del
motor permanecen dentro del trabajador; la UI recibe tipos simples y señales.

```python
class SpeechEngine(Protocol):
    def voices(self) -> tuple[VoiceInfo, ...]: ...
    def synthesize(
        self, text: str, voice_id: str, speed: float
    ) -> Iterator[AudioChunk]: ...
    def cancel(self) -> None: ...
```

Usar dataclasses inmutables para voces, fragmentos y solicitudes; `Enum` para
estados; anotaciones completas; Ruff con 88 columnas; y adaptadores para aislar
Piper, Qt Multimedia y el sistema de archivos. No pasar objetos Piper o Qt de
audio al resto de la aplicación.

## Estrategia de pruebas

- **Unidad:** selección exacta, texto vacío, división en fragmentos, orden de
  audio, cancelación sin fragmentos tardíos, transiciones, límites de velocidad
  y errores de modelos/dispositivo.
- **Integración Qt:** botones, selector y muestra de voz, accesibilidad, barra de
  progreso, silencio, cola acotada y cierre ordenado con motor falso.
- **Windows:** cargar ambos modelos offline; verificar que cada opción emite
  español, respuesta de UI, pausa/reanudación, detener/reiniciar y salida real.
- **Instalador futuro:** comprobar que recursos y avisos están presentes, que
  los hashes coinciden y que el primer arranque no necesita Internet.
- **Regresión:** pytest, Ruff y mypy para cada entrega.

## Límites

- **Siempre:** voces locales en español; incluir al menos una opción de México y
  una de España; mostrar ambas en Ajustes; no recurrir a red ni a voces de otro
  idioma; limitar colas y trabajo por hilo; mantener licencias junto a los
  modelos; probar con backend falso en Linux y Piper real en Windows.
- **Pedir decisión:** añadir voces que aumenten sustancialmente el instalador o
  impliquen una licencia distinta; sustituir Piper por un motor en línea; leer
  texto distinto de la selección o sección visible; añadir búsqueda dentro del
  audio; cambiar PyQt6.
- **Nunca:** descargar voces mientras se ejecuta la aplicación; transmitir el
  manual a terceros; sintetizar en el hilo de UI; ocultar errores de idioma o
  anunciar como funcional un control que no opera.

## Criterios de aceptación

1. Sin conexión a Internet, el menú Ajustes > Voz muestra y permite seleccionar
   las voces de México y España incluidas en la distribución.
2. La escucha de muestra y la lectura de una sección/selección funcionan con
   ambas voces; el idioma generado es español.
3. Si faltan archivos, no hay dispositivo de salida o falla Piper, se informa
   el problema sin cerrar la aplicación ni usar una voz no española.
4. Reproducir, pausar, reanudar, detener y reiniciar controlan el audio
   correspondiente; detener impide reproducir fragmentos que quedaron en cola.
5. Velocidad, volumen y silencio modifican la salida. El progreso coincide con
   el audio ya reproducido.
6. La ventana permanece interactiva mientras se sintetiza y reproduce; la cola
   de fragmentos está limitada.
7. Los tests del backend falso pasan en Linux y el smoke test Piper pasa en
   Windows con los dos modelos locales.
8. Pytest, Ruff y mypy pasan.
9. El futuro paquete contiene avisos de Piper y licencias de cada modelo, junto
   con recursos verificables por checksum.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Dos voces añaden ~126 MB de pesos | Instalador más grande | Distribuir ONNX de calidad media y mantener modelos fuera del ejecutable principal. |
| Piper tiene licencia GPL-3.0-or-later | Condiciones para distribuir la aplicación | Incluir licencia, avisos y materiales requeridos por GPL en el futuro paquete; confirmar condiciones de distribución antes de publicar. |
| Licencias de voces varían | Restricción o aviso omitido | Fijar modelos concretos; incluir sus `MODEL_CARD` y revisar avisos antes de cada actualización. |
| La inferencia tarda en dispositivos modestos | Silencios o respuesta lenta al iniciar | Sintetizar en segundo plano, emitir fragmentos pequeños y limitar la cola. |
| Pausa y cancelación compiten con generación activa | Audio residual tras detener | Cancelación cooperativa, cola acotada y pruebas de carrera con eventos tardíos. |
| Recursos no se encuentran en el instalador | TTS no inicia offline | Manifiesto versionado, hashes y smoke test de distribución en `packaging`. |

## Referencias técnicas

- [Piper: instalación, API Python y emisión por fragmentos](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md).
- [Piper: voces españolas, archivos de modelo y advertencia de licencias por voz](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md).
- [Licencia GPL-3.0-or-later de Piper](https://github.com/OHF-Voice/piper1-gpl/blob/main/COPYING).
- [Ficha del modelo español mexicano `ald`](https://huggingface.co/datasets/rhasspy/piper-checkpoints/blob/main/es/es_MX/ald/medium/MODEL_CARD).
- [Ficha del modelo español de España `davefx`](https://huggingface.co/datasets/rhasspy/piper-checkpoints/blob/main/es/es_ES/davefx/medium/MODEL_CARD).
- `PyQt6.QtMultimedia` está disponible en el entorno instalado del proyecto; no
  requiere declarar una distribución independiente.

