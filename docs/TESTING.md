# Verificación de la edición local 0.1.0

Fecha de cierre de estas pruebas: 21 de octubre de 2026.

## Entorno real

Foundry VTT 13.351 y sistema oficial gratuito mist-engine-fvtt 14.5.4, en un directorio temporal aislado. No se modificaron mundos del usuario. La última instalación se realizó extrayendo el ZIP construido, no enlazando las fuentes de desarrollo.

En un mundo vacío, el sistema añade su Item scene-data y la escena de bienvenida. El módulo los reconoce como auxiliares iniciales, ofrece importar y espera aceptación. La importación creó 34 actores, 20 Items propios, 27 diarios de contenido, 21 escenas propias, una macro y 12 carpetas. El Item auxiliar, el registro privado y la escena de bienvenida explican las diferencias respecto a los totales del mundo.

## Resultados

- 32 pruebas automatizadas aprobadas: importación aditiva, permisos, normalización, HTML seguro, persistencia, tutoriales, migración, cifrado autenticado y recuperación.
- Cinco fichas completas y cinco compactas abiertas realmente. Cada héroe tiene cuatro temas, doce etiquetas de poder, cuatro debilidades y una mochila. La compañía compartida queda vinculada y editable para utilizar sus etiquetas nativas.
- Los Rotes usan MistEngineItemRote y pasan la validación de datos. Una técnica adquirida y seleccionada apareció en la lista de etiquetas de la tirada oficial.
- El arrastre de una tarjeta Backpack añadió una entrada a la mochila existente sin crear una segunda mochila. La etiqueta de equipo puede tener un nombre más concreto que el título de la tarjeta.
- El Libro de los Recuerdos guardó y conservó una entrada tras recargar. El altar conservó el nombre liberado. La segunda importación no duplicó documentos ni reinició esos datos.
- Los siete pasos del tutorial del Narrador encontraron sus elementos reales.
- Las 21 escenas terminaron de dibujarse con textura válida. El plano de la Corte contiene cinco tokens vinculados a sus actores.
- Los 69 recursos distribuidos respondieron correctamente desde Foundry. No hay referencias gráficas ausentes.
- Las páginas de ambos PDF se renderizaron y revisaron. La comprobación de límites no detectó texto fuera de la página ni páginas vacías. El detalle actualizado está en pdf-review.json.

## Privacidad: hallazgo y corrección

La primera prueba descubrió que Foundry transmite los flags y las páginas de los diarios aunque un jugador no tenga permiso para abrirlos. Se sustituyó el almacenamiento en claro de las notas de campaña por AES-GCM, con clave local del navegador del Narrador.

La prueba posterior confirmó: eliminación del flag antiguo, conservación de progreso, ausencia del texto de prueba en los datos recibidos por el jugador, ausencia de claves en su navegador, lectura después de recargar, bloqueo cuando falta la clave y recuperación desde un respaldo local. Ninguna prueba utilizó secretos reales del usuario.

## Incidencias de la prueba

Al cerrar indiscriminadamente aplicaciones del núcleo, una primera automatización desmontó los controles del lienzo y provocó fallos de dibujo. Se corrigió el procedimiento y se repitieron las 21 escenas sin modificar el módulo: todas terminaron de dibujarse. También se descartaron mediante sus controles nativos el registro de cambios y el tutorial inicial del sistema, que cubrían formularios de prueba.

El paquete oficial del sistema contiene algunos ejemplos guardados con una versión posterior a Foundry v13. Su servidor emitió advertencias de migración sobre esos ejemplos. Los documentos de esta aventura se importaron y abrieron correctamente; no se modificó el sistema para silenciar esas advertencias.

## Evidencia

- foundry-final-install.json: mundo vacío, importación, 21 escenas y comprobación de recursos.
- foundry-sheets.json y capturas previews: fichas nativas.
- foundry-integration.json: Rote, recuerdos, altar y reimportación.
- foundry-privacy-fixed.json: privacidad corregida y recuperación real.
- foundry-permissions.json: hallazgo histórico anterior a la corrección, identificado como tal.
- verification.json y assets-inventory.json: contenido, integridad y recursos.

No equivalen a una prueba de mesa con cuatro o cinco jugadores. Queda pendiente la revisión específica de la edición final de imprenta a doble página. La referencia y el arte de Neb-Sekhem se integran en la revisión 0.3.0 descrita más abajo. La versión no se presenta como v1.0.0 ni se ha publicado.

## Revisión editorial y recursos 0.2.0

La evidencia anterior de ejecución real corresponde a 0.1.0 y se conserva sin alterar sus cifras. En 0.2.0 se han añadido seis láminas verticales: el paquete compila 27 escenas y 75 recursos con referencias válidas. Los nuevos WebP se han decodificado y verificado; no se ha repetido la sesión completa del servidor Foundry porque no cambia el código funcional. Las 32 pruebas automatizadas pasan de nuevo.

Los PDF revisados tienen 47 y 8 páginas. Se renderizan todas; no hay páginas sin contenido ni texto fuera de límites. La comprobación de fuentes conserva los 209 párrafos narrativos, las ayudas, tablas y las cinco fichas completas. Las capturas, el alcance de la inspección y la resolución nativa de las láminas se detallan en editorial-review-v2.md.

## Corrección de mapas 0.2.1

Tres mapas sustituidos por grabados frontales sobre piedra. Sus contenedores conservan las rutas, tamaños y geometría de las escenas anteriores, comprobados en stone-maps-geometry.json. La carga y lectura de los tres SVG con WebP incrustado se verifican en Chrome: stone-maps-browser.json. El Adventure conserva 27 escenas y ahora distribuye 78 recursos con referencias válidas. El manual conserva 47 páginas y el cuaderno no se ha regenerado. Alcance y originales en stone-maps-review.md y stone-maps-art.json.


## Reilustración 0.3.0

Los 53 maestros anteriores han sido sustituidos por dibujos nuevos; se añaden 15 maestros para completar 68. Se distribuyen 101 WebP y tres contenedores SVG con los mapas grabados, sin recursos ausentes. Los 34 actores, 20 Items, 27 diarios, 29 escenas y una macro conservan sus identificadores. Las dos escenas adicionales corresponden a Neb-Sekhem y su coronación.

35 pruebas automatizadas pasan, incluidas tres de actualización de imágenes que protegen los retratos y tokens personalizados. Los PNJ propios con iconos anteriores reciben el nuevo arte; los protagonistas y el progreso se conservan.

Se abren las cinco fichas completas de 1100 × 800 y las cinco compactas en Foundry 13.351 con Mist Engine 14.5.4. Se comprueba la asignación artística a Neb-Sekhem, Henut, Hori y Merit, la decodificación de las 101 imágenes referenciadas y el dibujo de las 29 escenas. Los 22 tokens conservan el canal alfa y márgenes exteriores totalmente transparentes. Evidencia: foundry-art-v3.json, token-alpha-v3.json y las capturas v3 de previews.

Los PDF se reconstruyen y renderizan completos: manual 49 páginas, cuaderno 8. La comparación de fuentes conserva 209 párrafos narrativos, ayudas, tablas, biografías, temas, equipo y secretos individuales; ningún secreto se filtra al cuaderno. No se detectan páginas vacías ni texto fuera de página. El manual contiene nueve páginas completas de arte, incluida la cubierta nueva de Neb-Sekhem.

Durante la primera navegación, el tutorial nativo dejó un estado de herramienta de SceneControls que provocó un error del núcleo. Tras cerrar ese tutorial y recargar, la repetición de las 29 escenas terminó sin errores, con todas las texturas válidas. Se conservan ambos registros en foundry-art-v3.json; no se ha modificado el núcleo ni el sistema.

## Publicación 1.0.0

Portada tipográfica nueva sobre la misma ilustración. El manual pasa a 50 páginas; el cuaderno conserva ocho. Se contrastan 214 párrafos, sin pérdidas, páginas vacías ni cortes de texto. La colección artística permanece intacta.

Se añaden 29 diarios privados de dirección y una entrada de créditos. Cada escena contiene su lectura y los enlaces de audio nativos. El Adventure incluye dos listas con nueve bucles instrumentales y diez efectos y ambientes, 123 recursos distribuidos y ninguna ruta ausente.

42 pruebas pasan, incluidas mezcla de lectura, permisos del Narrador activo, deduplicación del reparto y conservación de vínculos personalizados. Los 19 audios se decodifican completos, contienen señal, no saturan y tienen un salto de unión inferior a 0,03 en los bucles.

En Foundry 13.351 con Mist Engine 14.5.4 se prueban botones del diario y la barra, nueve músicas y diez efectos con reproducción real del motor de audio, lectura, ficha de Neb-Sekhem, colocación de seis figuras sin duplicados, activación de escena y parada de audio. Las imágenes de actores y el registro cifrado de campaña se mantienen iguales al actualizar. Evidencia: foundry-direction-v1.json y audio-validation.json.

Se comprueba además con un usuario jugador: recibe el audio sincronizado, no ve la barra, no puede ejecutar acciones de dirección y no tiene permiso de observación sobre los diarios privados. El modo lectura reduce el volumen nativo de 0,30 a 0,08.
