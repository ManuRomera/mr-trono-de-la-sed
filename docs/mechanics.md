# Mecánicas e integración nativa — MR · El Trono de la Sed

Estado: datos de contenido preparados para `mist-engine-fvtt` 14.5.4. Las comprobaciones estructurales locales no equivalen a una apertura y una partida real en Foundry. No se ha afirmado que las fichas se hayan probado visualmente.

## Evidencia consultada

Se ha inspeccionado el código público de la etiqueta `14.5.4` del repositorio oficial, conservado como referencia en `research/mist-engine/`. No se distribuyen sus ilustraciones ni sus textos de personajes dentro del módulo.

| Función | Fuente del sistema consultada | Decisión del proyecto |
| --- | --- | --- |
| Registro de tipos | `module/mist-engine-fvtt.mjs`, `CONFIG.Actor.dataModels` y `CONFIG.Item.dataModels` | Actores `litm-character`, `litm-npc` y `litm-fellowship-themecard`; Items `themebook`, `backpack` y `rote`. |
| Temas | `module/data/item-themebook.mjs` y `templates/item/item-themebook-sheet.hbs` | Etiquetas en `powertags` y `weaknesstags`; búsqueda en `quest`; pistas de evolución en `improve`, `abandon`, `milestone`. |
| Héroes iniciales | `src/packs/pregen-characters/*.json` | Se verifica la estructura de cuatro temas y tres etiquetas activas por tema, sin copiar contenido ni mejoras especiales oficiales. |
| Color y escala | Plantilla oficial del tema; ejemplo Rosamund | Los temas mundanos tienen `type: litm-origin`. Los de magia usan `litm-variable`, con `color: litm-origin`, igual que el mecanismo de ejemplo; su alcance inicial es local y humano. No se otorga Greatness. |
| Compañía | `module/data/actor-fellowship-themecard.mjs`; `loadFellowshipThemecard()` en `module/sheets/litm-character-sheet.mjs` | Un actor compartido y `actorSharedSingleThemecardId` con su ID de mundo. No se usa UUID en ese campo. |
| Relaciones | `module/data/actor-character.mjs`; `templates/actor/parts/actor-fellowship-partial.hbs` | `companion` es texto de nombre y `relationshipTag` es una etiqueta. Una relación mecánica inicial por héroe; las demás están descritas en la biografía. |
| Inventario | `module/data/item-backpack.mjs`; `_onDrop()` en `module/sheets/litm-character-sheet.mjs` | Cada héroe tiene una única mochila. Al soltar una tarjeta Backpack, el sistema 14.5.4 combina sus entradas con la mochila existente. No se usa el Item genérico de dados d20. |
| Rotes | `module/data/item-rote.mjs`; preparación de tarjetas en la ficha | Técnicas adquiribles con `actionType`, `success`, `consequences` y selección nativa. Su título es una etiqueta positiva seleccionable; no se añade un motor de magia. |
| Estados | `module/data/util.mjs`, `buildFloatingTagsAndStatuses()` | Los estados viven exclusivamente en `system.floatingTagsAndStatuses`; `markings` tiene seis booleanos. `value` se deriva de las marcas. |
| Desafíos | `module/data/actor-npc.mjs` | Límites, aspectos de Might, amenazas, consecuencias, secretos y rasgos nativos. Los límites se guardan como cadenas según el esquema. |
| Fondo ilustrado | `module/data/base-actor.mjs` | El fondo irá en `system.customBackground` solo después de existir el recurso real. No se incluyen rutas de imágenes imaginarias. |

Las rutas anteriores son evidencia de implementación, no una licencia para redistribuir todos los recursos del sistema.

## Contenido generado

`content/actors.json` contiene 34 actores: cinco protagonistas, el tema compartido, los siete PNJ principales, las seis víctimas, Henut, tres adversarios menores y once desafíos de situación. Khety y Serekh actúan además como sus propios desafíos; no se duplica su estado en dos actores.

Los protagonistas tienen 20 temas en total, 60 etiquetas de poder activas y 20 debilidades, sin mejoras especiales compradas ni progreso previo. Cada uno tiene su mochila y su relación mecánica inicial. Todos los ID son estables, alfanuméricos, de 16 caracteres, derivados de claves de contenido.

`content/items.json` contiene cuatro Rotes de adquisición durante la aventura y 16 tarjetas de objetos Backpack. Seis tarjetas representan las seis vasijas identificadas; otra representa la séptima vacía. Las tarjetas no suponen que un héroe posea el objeto: la entrega requiere que lo obtenga en la ficción. El altar no genera objetos repetidos ni da bonificaciones adicionales.

Se han omitido `img` y los fondos hasta que existan imágenes propias aprobadas. Este estado de preparación no cumple todavía la aceptación visual del encargo.

## Decisiones de creación y equilibrio

El punto de partida elegido es una compañía de personas de Muhar con capacidades locales. Los cuatro temas de cada héroe poseen tres etiquetas activas y una debilidad. No hay poderes absolutos como «recordarlo todo», «dominar cualquier sello» o «curar todo olvido».

Las búsquedas y etiquetas son originales. No se han copiado cuestionarios, mejoras especiales de pago ni reglas de una clase de otro juego. Los campos de mejoras especiales se mantienen vacíos e inactivos.

Las relaciones con los otros cuatro personajes están desarrolladas en la biografía; solo una es una etiqueta nativa inicial. Es una decisión conservadora de preparación, no una afirmación de que la regla universal prohíba más relaciones. Se crean o recuperan otras mediante las herramientas oficiales y la ficción.

Los Rotes se han preparado como técnicas que pueden aprenderse en escenas. No se han añadido gratuitamente a las fichas iniciales: el esquema oficial hace seleccionable su título como etiqueta positiva y no se ha verificado una asignación inicial universal de Rotes que permita regalar ese Poder. La magia de Zahra, Seneb e Iru ya está habilitada por temas limitados. Aprender una técnica nueva requiere el permiso ficticio indicado y una entrega expresa del Narrador. No hace falta comprar el módulo comercial de los libros para usar estos documentos nativos.

Las técnicas de infiltración de Neset y la protección de Khaem son etiquetas de sus temas; no se convierten artificialmente en hechizos o Rotes. Sus herramientas, armas y protecciones figuran en Backpack, sin daño, puntos de golpe, valores de armadura ni iniciativa añadida.

## El Peso del Olvido

Es una adaptación temática original: no añade una reserva de cordura ni un contador universal de deterioro. Una consecuencia pertinente puede producir un estado negativo nativo como `recuerdos-desvanecidos-1` o `identidad-confusa-2`. No son peldaños que deban recorrerse en orden. Las amenazas de los desafíos usan el marcado `[/sn estado-2]` para señalar su carácter negativo.

Antes de introducir una consecuencia, se explica qué la provoca y qué efecto tiene en la situación. Un estado no decide que alguien ama al vampiro, consiente un sacrificio o cambia de tema. Los límites de los héroes y la resolución de reacciones pertenecen al sistema oficial.

No se suman intensidades como si fueran puntos de daño. Para acumular, reducir, crear o eliminar estados se emplean los controles oficiales. El Libro de los Recuerdos debe leer la matriz nativa de estados; no puede guardar una segunda copia autoritativa de sus niveles.

Una canción, una carta, una relación o una prueba de identidad ofrece una acción concreta para recuperar un recuerdo. Si basta con realizar una tarea segura, se resuelve de forma simple. Si existe incertidumbre o riesgo, se plantea una acción rápida o detallada y se utilizan los efectos nativos correspondientes. Una recuperación no se concede por pulsar un botón del panel ni por abrir una ficha.

Se han contrastado las opciones generales en la documentación pública del sistema `src/packs/system-documentation/How_To_Play_*.json` y en los artículos oficiales de Son of Oak «How to Play Legend in the Mist Episode 6 — Advanced Actions» y «Episode 8 — Camping». Se citan como referencia de consulta; no se reproducen sus textos completos.

- [Acciones avanzadas, fuente oficial](https://sonofoak.com/en-eu/blogs/news/how-to-play-legend-in-the-mist-episode-6-advanced-actions).
- [Descansos, fuente oficial](https://sonofoak.com/blogs/news/how-to-play-legend-in-the-mist-episode-8-camping).
- [Sistema oficial en Foundry](https://foundryvtt.com/packages/mist-engine-fvtt).
- [Código de la versión consultada](https://github.com/MrTheBino/mist-engine-fvtt/tree/14.5.4).

## Ejemplos de acción situados

- Zahra coteja una ofrenda con un registro alterado. Puede proponer «Acólita de los registros» y «Reconocer tinta alterada». «Mis superiores esperan obediencia» solo entorpece si la presión de una autoridad afecta realmente a esa acción. Una pista esencial sigue apareciendo si la tirada tiene consecuencias; el coste puede ser quedar vigilada.
- Khaem sostiene una salida mientras pasan las víctimas. «Interponerme a tiempo» y «Aguantar una carga» pueden ayudar; el escudo solo cuenta si su uso protege en esa situación. No concede una reducción automática de daño por estar en la mochila.
- Neset busca la pieza que oculta una puerta. «Detectar una piedra falsa» puede ayudar. «Quiero comprobar una última cosa» puede causar una demora significativa, no un penalizador gratuito a toda acción.
- Seneb responde a un recuerdo amenazado con un canto que otro héroe reconoce. «Sostener un recuerdo compartido» necesita un recuerdo ya establecido. La canción puede dar permiso para una recuperación; el estado se modifica en el sistema oficial.
- Iru estudia el cofre con la pluma y el testimonio de Merit. «Interpretar un sello funerario» y «Reconocer un vínculo ritual» pueden ser pertinentes. Abrir el cofre sigue requiriendo reconocer su voluntad; no basta con acumular etiquetas ajenas al propósito.

No se fija aquí un total de Poder universal: depende de etiquetas disponibles, estados, ayuda, Might y del propósito exacto de la acción. El diálogo oficial calcula las opciones seleccionadas.

## Desafíos, límites y Might

Los desafíos sociales y rituales son actores `litm-npc`, no diarios que imitan fichas. Un límite como `desvelado: 4` describe cuándo la manipulación queda expuesta; no significa cuatro heridas. Si la situación se resuelve plenamente por una decisión o una prueba suficiente, no se obliga a hacer tiradas redundantes hasta rellenar un medidor.

Cada límite tiene una consecuencia explícita y limitada: apartar un custodio abre una salida; comprender la cámara permite elegir; desproteger el corazón abre el cofre. Ninguno concede por error una victoria adicional sobre otra tarea.

La detección visual automática del sistema compara el comienzo del nombre del estado con el del límite. Los nombres propuestos evitan sinónimos que impedirían esa detección; el Narrador conserva el juicio sobre la pertinencia de un estado. La aplicación no convierte ese indicador en una regla semántica universal.

Might se expresa mediante aspectos situados: las sombras pueden rastrear recuerdos, pero se vuelven vulnerables a la luz y al testimonio; Neb-Sekhem domina ecos dentro de su corte, pero no conoce secretos que nadie le ha revelado. No se aplica una bonificación global por la mera etiqueta de «vampiro».

## Continuidad de los sellos y del corazón

1. Hori, Paser, Tamerit, Kasa, Beset y Dedi están vivos y cautivos al comienzo. El funeral de Hori se apoya en una desaparición manipulada. El recipiente vacío no demuestra su muerte.
2. Henut, lavandera adulta, es la candidata anunciada para la séptima entrega. La séptima vasija empieza vacía. Si se la protege, se conserva ese éxito: no aparece una víctima sustituta ya sacrificada fuera de escena.
3. Una extracción completa del séptimo nombre rompe el sello sacerdotal. Matar a una persona no equivale a realizar esa extracción.
4. El sello de Merit se mantiene mientras sobreviva un testimonio auténtico que reúna su nombre y su negativa. Los protagonistas que comprenden y conservan esa verdad también son testigos. Destruir solo una tablilla no basta.
5. Neb-Sekhem solo abandona la corte si caen ambos sellos. No abandona Ravenloft.
6. La cámara tiene rutas alternativas: corredor tras liberar un nombre, puerta de la pluma y acceso de servicio de Khety. No se exigen las tres. El cofre tiene una protección distinta: puede abrirse con un acto que restituya agencia —liberar un nombre ante su dueño, devolver la pluma reconociendo la negativa de Merit o pedir al eco que decida y aceptar su respuesta—. Un rescate ya realizado cuenta. También puede forzarse con oposición sobrenatural y riesgos anunciados. Las llaves de servicio no abren automáticamente el cofre y el nombre de Merit no funciona como contraseña.
7. Destruir el corazón termina con el vampiro, pero no libera automáticamente los nombres cautivos. Resolver las vasijas y atender los cuerpos sigue siendo necesario.
8. Romper mal una vasija dispersa una identidad que todavía puede rescatarse; no declara muerta a su víctima.
9. Renovar el juramento exige una elección libre, informada y concreta. No se produce por un fallo de dados ni como coste retroactivo de una acción.

## Información privada y permisos

Los protagonistas contienen solo biografía, relaciones, preguntas de creación y mecánicas conocidas. No se han ocultado secretos del Narrador en sus flags: un propietario de Actor podría leerlos. Los secretos generales se guardan en los actores privados de PNJ y en los documentos reservados al Narrador.

Todos los actores se entregan con propiedad predeterminada `0`. Al importar, el Narrador debe asignar el héroe correspondiente y la propiedad del tema compartido a sus jugadores. Un módulo no debe conceder por defecto a cada usuario acceso a las historias personales de todos.

Los PNJ con `system.secrets`, sus desafíos y los objetos aún desconocidos deben seguir privados. Conceder OBSERVER a un desafío puede revelar sus datos aunque una aplicación personalizada oculte un panel. No se consideran seguros los secretos que solo desaparecen visualmente de una ventana.

### Secretos personales para entrega privada

- Zahra falsificó un registro para proteger a un inocente. La identidad del protegido se acuerda con su jugador; no es necesariamente ninguna de las seis víctimas. El vampiro no conoce ese hecho sin una vía de información.
- Khaem cerró una tumba mientras alguien golpeaba desde dentro. Reconoció la voz, pero ya no recuerda a quién pertenecía. La aventura no fija retroactivamente que fuera culpable de una muerte no establecida.
- Neset rechazó un encargo de transporte de seis vasijas que parecían susurrar nombres. Conoce la sensación y algunos detalles del encargo, no el destino de las víctimas por omnisciencia.
- Seneb sueña con una mujer de blanco que le pide que la recuerde. Un sueño es una invitación a investigar; no constituye consentimiento a ser poseído ni demuestra que ya conozca el nombre de Merit.
- Iru ha visto en un relieve el símbolo de los escarabajos del vampiro. Ese reconocimiento enlaza pistas, pero no le otorga el conocimiento automático de todos los ritos.

### Consecuencias de las preguntas de creación

- Zahra establece una palabra pronunciada de forma particular por quien la enseñó a escribir. Un eco demasiado perfecto puede equivocarse en esa imperfección afectuosa.
- Khaem establece una pertenencia entregada como promesa. Una copia puede reconocerse, pero el portador no tiene por qué conocer su significado.
- Neset establece un nombre de infancia y un gesto de hogar. Neb-Sekhem necesita averiguarlos antes de usarlos; el Narrador no se los transmite por conocer la ficha.
- Seneb establece una canción incompleta y quién comparte su final. Otro héroe puede responder con esa verdad durante una recuperación.
- Iru establece una enseñanza agradecida demasiado tarde y el objeto prestado. Recordar a la persona permite sostener la identidad frente a una oferta de poder sin vínculo.

No se decide por anticipado que estas personas estén muertas ni se las convierte automáticamente en rehenes. Su función es dar a los jugadores material sobre el que elegir.

## Validaciones realizadas y pendientes

Realizado: lectura de esquemas; comparación de cardinalidades con los pregenerados; JSON válido; IDs únicos por colección; cuatro temas por héroe; tres etiquetas activas y una debilidad en cada tema; vínculo de compañía existente; exactamente una mochila por héroe; secretos ausentes de los campos de los héroes; ninguna ruta de imagen inexistente añadida por estos archivos.

Pendiente: instanciación de cada documento con los DataModels efectivos de Foundry; importación del Adventure; asignación y sincronización real de la compañía entre dos usuarios; apertura de fichas completas y compactas; selección de etiquetas; tiradas; adquisición de Rotes; arrastre y fusión de objetos; estados y límites en escena; conservación después de reiniciar; revisión visual con el arte definitivo.

La colección no debe presentarse como validada en Foundry hasta ejecutar esas pruebas. Tampoco certifica que un módulo basado en dos propiedades ajenas pueda publicarse bajo una licencia cualquiera.

## Alineación final de continuidad y arte

La procesión transporta agua, lienzos y la séptima vasija todavía vacía; las seis identidades iniciales ya permanecen en la sala de la corte. Henut solo está en el cortejo si se jugó su captura. Si los héroes conservan o destruyen el séptimo recipiente, no aparece una copia automática. Preparar un sustituto requiere al menos una jornada de trabajo visible y nuevos materiales.

Las profesiones de las víctimas siguen el manuscrito: Hori ayuda en el archivo de Panehsy; Paser es alfarero; Tamerit atiende partos y convalecientes; Kasa trabaja como porteador; Beset reparte remedios junto a Nefru; Dedi repara sandalias y correas.

Los motivos que identifican los recipientes se han alineado con las ilustraciones originales ejecutadas. Deben mantenerse iguales en diario, ayuda y panel:

| Víctima | Motivo visual de su vasija |
| --- | --- |
| Hori | Dos cálamos cruzados |
| Paser | Espiral de alfarería |
| Tamerit | Plantas y tapa de ibis |
| Kasa | Cuerda y tapa de chacal |
| Beset | Dos anillos enlazados y tapa de gata |
| Dedi | Candil y tapa de halcón |

Estos motivos permiten reconocer el recipiente. El nombre puede leerse en su base con la iluminación adecuada; no se exige acertar una adivinanza para avanzar. Los recuerdos y objetos de anclaje siguen procediendo de las vidas descritas en el manuscrito, no del animal de la tapa.
