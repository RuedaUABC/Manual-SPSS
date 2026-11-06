# Especificación: `ui-foundation`

## Propósito y usuario

Proveer la ventana PyQt6 reutilizable para que una persona consulte el manual,
navegue entre sus capítulos y ajuste la apariencia. La pantalla inicial prioriza
el capítulo actual; Ajustes queda a un paso y permite regresar al lector.

## Evidencia visual y decisiones

- Figma `Capitulo 1 - Inicio` (`1:3`): referencia de 1440×1024, fondo rosa
  claro, panel marfil, barra de capítulos vino, acciones de Ajustes/Inicio,
  control de audio superior, contenido centrado y navegación inferior.
- Figma `Ajustes – Voz` (`44:160`): barra lateral de ajustes y navegación entre
  Voz, Apariencia y Créditos y derechos de autor.
- Figma `Ajustes – Apariencia – Grises – Oscuro` (`47:684`): contraste oscuro
  con superficie grafito y texto claro.
- Audiencia: estudiantes que necesitan leer capítulos largos e ilustrados.
  Acción principal: seleccionar un capítulo y consultar su contenido.
- Tono: editorial y sereno; Inter/Segoe UI, esquinas redondeadas y acento vino.
- Vistas verificables: 1440×1024 (diseño) y 1024×768 (ventana reducida).
- PyQt6 y recursos locales empacables; la capa `ui` no importa
  `content_model`. El punto de composición convierte el catálogo a modelos de
  vista e inyecta sus rutas locales.

## Comportamiento

- Seleccionar un capítulo, avanzar/retroceder y volver al primero actualiza el
  título y el HTML local del panel de lectura.
- Ajustes cambia a una pantalla propia; Apariencia conmuta entre los temas claro
  y oscuro. Volver al manual y el botón Inicio regresan al lector.
- El catálogo vacío muestra un estado útil sin fallar; un catálogo inválido se
  informa al iniciar con una ruta de recuperación.
- La navegación por voz queda identificada como pendiente del módulo TTS. Los
  controles de audio del diseño se muestran como no disponibles mientras no haya
  motor de voz.
- Créditos y derechos de autor presenta atribuciones disponibles en el catálogo
  y deja explícito cuando la licencia no está confirmada.

## Accesibilidad y estados

- Todo botón tiene nombre accesible, foco visible y orden de tabulación lógico;
  la lista y los controles segmentados son operables con teclado.
- El cambio de tema actualiza texto, controles y contenido HTML. El lector
  conserva su scroll por capítulo mientras no se seleccione otro.
- Carga: abre directamente el catálogo local validado; no hay descarga ni una
  espera independiente que requiera animación.
- Vacío: mensaje y acción de regresar a Inicio.
- Error: mensaje de inicio con la ruta para corregir el catálogo.
- Parcial: no aplica. `content_model` valida el catálogo completo antes de
  devolverlo; la aplicación no presenta catálogos incompletos.
- Éxito: cambio de capítulo o tema se refleja de inmediato.
- Permisos: no aplican; la lectura usa archivos locales sin cuenta ni permisos
  de aplicación.
