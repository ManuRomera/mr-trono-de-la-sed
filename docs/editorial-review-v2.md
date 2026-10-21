# Revisión editorial 02 · 21 de octubre de 2026

Actualización 0.2.1: los tres mapas se han sustituido por grabados sobre piedra; véase [la revisión de mapas](stone-maps-review.md). El resto de este informe conserva el alcance original de 0.2.0.

El manual pasa de 81 a 47 páginas y el cuaderno de protagonistas de 15 a 8. La reducción procede de retirar saltos y portadillas vacías, reunir las amenazas en columnas continuas y componer cinco fichas completas de una página. No se ha abreviado el manuscrito para obtener ese recuento.

## Composición

- Seis pinturas nuevas concebidas en vertical: funeral, descenso a la corte, nombres cautivos, corazón, Merit y Khety. La identidad de los dos últimos toma como referencia sus retratos existentes.
- Siete páginas de arte completo en el manual: cubierta, cinco aperturas narrativas y cierre. El cuaderno utiliza una cubierta ilustrada propia con el funeral.
- Texto a dos columnas, EB Garamond de 11,2 puntos e interlínea de 14,2; fichas a 10,8/12,8. Las notas y tablas mantienen un mínimo de 10 puntos, salvo pies y encabezados.
- Tablas de cronología, rutas de pistas, sellos y relaciones reunidas en dos páginas con ilustración contextual. Los tres planos se incluyen como gráficos vectoriales legibles con sus claves.
- Recuadros ilustrados al terminar las partes que dejaban una columna vacía. Resumen de las dos prisiones, comprobación del desenlace y orientación para interpretar a las voces.
- Documentos breves reunidos en tarjetas recortables. Las revelaciones no se incluyen en el cuaderno común.
- Índice enlazado y marcadores; cubiertas sin las franjas de transparencia detectadas durante la revisión.

## Integridad y revisión

Se han renderizado las 55 páginas de los dos documentos. Se han inspeccionado sus vistas de conjunto y páginas ampliadas de cubiertas, láminas, texto, tablas, mapas, fichas y ayudas. La comprobación geométrica no detecta texto fuera de la página. Una comprobación adicional descuenta encabezados y folios para evitar considerar válida una página vacía por tener solo cabecera.

La auditoría compara los 209 párrafos narrativos, todas las celdas de las tablas, las ayudas, las cinco biografías, motivaciones, etiquetas y equipo con el texto extraído. También comprueba los secretos personales en el manual y su ausencia del cuaderno. Los campos de límites, rasgos y amenazas de los desafíos se han cotejado con su fuente sin omisiones. Resultados en pdf-review.json y pdf-source-coverage.json.

## Foundry

El módulo local 0.2.0 incorpora las seis láminas WebP como escenas narrativas verticales, sin cuadrícula. El Adventure contiene ahora 27 escenas, incluidos los tres planos, y 75 recursos distribuidos. Todos los recursos tienen referencia en los documentos y pasan la comprobación de integridad. Las 32 pruebas automatizadas del módulo siguen pasando. La ejecución real previa de Foundry 13 y Mist Engine 14.5.4 corresponde a 0.1.0; esta revisión no cambia el motor, las fichas ni la privacidad y no se presenta como otra prueba completa de juego.

## Originales y alcance

Prompts, referencias y rutas en editorial-art-v2.json. Método: herramienta integrada image_gen. Originales PNG en art/masters/lamina-*.png y variantes WebP en assets/scenes/lamina-*.webp. Se mantienen los originales nativos de 1024 × 1536 sin ampliación artificial; esta es una edición digital local, no una certificación de imprenta a 300 ppp. La edición anterior se conserva en editorial/archive/v0.1.0.

Siguen pendientes la referencia original de Neb-Sekhem y el arte que exige su identidad, además de una prueba de mesa. Ravenloft y Har’Akir permanecen en uso local por decisión del autor; no se ha publicado ningún repositorio ni Release.
