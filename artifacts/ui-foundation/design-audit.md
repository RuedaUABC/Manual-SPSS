# Auditoría visual del lector

Fecha: 2026-11-06  
Referencia: [frame “Capitulo 1 - Inicio”](https://www.figma.com/design/31JawBRaqdqo4OH1YJ3qSu/Manual-SPSS?node-id=1-3)

## Resultado

**81/100** en las diez dimensiones de `ecc:design-system`. La comparación se centró
en el frame de escritorio de 1440 × 1024 y en la respuesta de la implementación a
1024 × 768.

| Dimensión | Puntaje | Hallazgo y evidencia |
| --- | ---: | --- |
| Consistencia de color | 8/10 | El lector y Ajustes comparten la paleta de [`theme.py`](../../src/manual_spss/ui/theme.py:27). Los controles de audio aún repiten colores literales en [`main_window.py`](../../src/manual_spss/ui/main_window.py:60). |
| Jerarquía tipográfica | 9/10 | Figma define título de 96 px y cuerpo de 40 px ([título](https://www.figma.com/design/31JawBRaqdqo4OH1YJ3qSu/Manual-SPSS?node-id=2-38), [texto](https://www.figma.com/design/31JawBRaqdqo4OH1YJ3qSu/Manual-SPSS?node-id=2-32)). La implementación usa 72 pt y 40 px en escritorio; en 1024 px cambia a 46 pt y 22 px ([lector](../../src/manual_spss/ui/main_window.py:517), [título](../../src/manual_spss/ui/main_window.py:645)). El título del catálogo “Introducción al SPSS” difiere del texto “¿Qué es SPSS?” del frame; se conserva el contenido del manual. |
| Ritmo y alineación | 9/10 | La introducción ocupa 54% del ancho de lectura, el logotipo mide 451 px y se alinea a la derecha, como en Figma ([distribución](../../src/manual_spss/ui/main_window.py:544)). Las flechas también quedan fuera de la tarjeta y alineadas en el pie del lector ([pie](../../src/manual_spss/ui/main_window.py:244)). |
| Consistencia de componentes | 8/10 | Botones de navegación, lista y ajustes comparten estilos y estados. La pestaña de audio ahora es un control independiente que conserva el arte de Figma ([control](../../src/manual_spss/ui/main_window.py:257)). |
| Comportamiento adaptable | 8/10 | El contenido, tamaño del logotipo y márgenes cambian al cruzar el breakpoint de 1200 px. La pestaña permanece centrada al redimensionar; evidencia en `reader-1440x1024.png` y `reader-1024x768.png`. |
| Tema oscuro | 7/10 | La paleta de texto y superficies tiene tokens para ambos temas. El arte SVG del panel de audio mantiene su fondo blanco en modo oscuro. |
| Movimiento | 8/10 | La apertura y el cierre son inmediatos, sin animaciones que retrasen la lectura. El estado se comunica por el nombre accesible del control ([actualización de estado](../../src/manual_spss/ui/main_window.py:686)). |
| Accesibilidad | 8/10 | El control tiene foco, tooltip y nombre accesible dinámico; funciona con mouse y Espacio. Las pruebas existentes comprueban contraste de texto en ambos temas. Los controles dibujados del reproductor siguen siendo decorativos hasta integrar voz. |
| Densidad de información | 8/10 | El tamaño del cuerpo coincide con Figma y el párrafo largo permanece en un área desplazable. La primera página usa más texto que el fragmento del frame, por lo que parte del párrafo queda bajo el pliegue y se alcanza mediante la barra de desplazamiento. |
| Acabado | 8/10 | Hay estados vacío y error, hover y foco visibles, capturas para dos tamaños y evidencia del reproductor plegado. Falta aplicar una variante oscura al arte de audio y terminar la interacción de reproducción. |

## Cambios aplicados

- Tipografía de escritorio alineada con Figma: título de 96 px equivalentes y cuerpo
  de 40 px; el modo compacto conserva una escala legible de 46 pt y 22 px.
- Columna de texto y logotipo ajustadas a 54% y 451 px. Se quitaron márgenes HTML
  implícitos para alinear el texto con el borde interior del frame.
- Panel de audio plegable con pestaña permanente, centrada y accesible por teclado.
- Navegación inferior separada de la tarjeta, como en el frame de Figma.
- Capturas de los estados expandido y plegado en [`artifacts/ui-foundation`](.).

## Evidencia de interacción

`tests/integration/ui/test_main_window.py` comprueba que el panel se pliega con
click, se despliega con Espacio y la pestaña permanece centrada después de reducir
la ventana a 1024 × 768.
