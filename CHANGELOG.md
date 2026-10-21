# Cambios

## 1.5.0 — 22 de octubre de 2026

- **Neb-Sekhem es un dios.** Nuevo apartado «Un dios en la arena»: qué puede hacer en su corte, cómo mostrar su escala, cinco demostraciones de poder (el Primer Gesto, la sed, su gracia…), Palabra de Retirada, sombra arrodillada y las tres únicas vías para dañarlo. Aspecto de Might «Greatness» en su ficha.
- **Se nota Egipto.** Nuevo capítulo 2 «Har’Akir, el reino del nombre»: las cinco partes del alma (Ren, Ka, Ba, Ib, Sheut) aplicadas a la trama, tabla de símbolos, las vasijas como canopes deformados, el cartucho vacío, la confesión negativa en la balanza, fórmulas, paleta y olores. Línea **Símbolos** en los lugares clave.
- **Muertos dominados de horror gótico, sin momias.** Nuevo capítulo 3: **Borrados** (multitud sin rostro), **Plañideras** (heraldos), **Pesadores** (guardia) y sombras arrodilladas, con arte nuevo, fichas de desafío, tarjetas y tokens.
- **Acción e infiltración:** A1 (los Borrados en el camino), C4b (la huida del dormitorio), C5b (la cámara que pesa), el cincel, la coronación en tres actos (P5) y la caída de la corte (P6), con una tarea para cada héroe. Tabla «Cuándo brilla cada héroe».
- **Reloj de las siete lámparas** y **sed de la corte**, con marcador solo para el Narrador en el panel de hitos.
- Fallos de guión corregidos: por qué Neb necesita a Khety (solo un sacerdote consagrado rompe el sello y los muertos no obran sin un vivo), el villano tiene dientes (el cincel) y la aventura tiene urgencia.
- Manual de 87 páginas, 7 desafíos y 3 criaturas nuevos, dos láminas nuevas.

## 1.4.0 — 21 de octubre de 2026

- **Escala por perspectiva real:** cada fondo declara su línea de horizonte (la cabeza de una persona de pie queda en ella) y puntos de apoyo solo sobre suelo firme; el tamaño de cada figura sale de su altura en el cuadro (más pequeña junto al trono, grande ante la mesa y las sillas) y se recalcula al arrastrarla.
- La marca MR de los tokens pasa a ser un sello diminuto y muy discreto cosido en la ropa de cada figura (antes iba bajo los pies).
- **Ambiente por escena:** claro, penumbra u oscuro cambian la luz de la escena y el volumen del fondo a la vez; se recuerda por escena.
- **Hitos de la investigación:** doce descubrimientos sin spoilers que marca el Narrador; insignia y panel visibles para toda la mesa (Alt+H) con aviso en cada hito nuevo.
- **Tutoriales:** nuevo recorrido de dirección de escena (barra arrastrable, figuras, escala por profundidad, ambiente y hitos) y paso de hitos en el de jugadores.
- Las 22 presentaciones de personajes y criaturas, revisadas y ampliadas, con el mismo texto en fichas, diarios y manual.
- **Tarjetas de PNJ** recortables (PDF aparte) y **edición de imprenta** del manual con 3 mm de sangrado.
- README con GIF de recorrido y capturas nuevas.

## 1.3.0 — 21 de octubre de 2026

- **Figuras con profundidad.** Cada fondo declara su zona de suelo y puntos de apoyo reales (`content/stage.json`). Al colocar protagonistas y PNJ, cada figura pisa un lugar de la escena y su tamaño depende de la distancia; al arrastrarla hacia el fondo se encoge y hacia el frente crece, conservando el apoyo. Opción «Escala por profundidad» en el menú Figuras.
- **Barra del Narrador rediseñada.** Botones nuevos con grupos y acción principal destacada, chips de efectos, menús con cristal, monograma MR, plegado a una fila y **arrastre con el botón derecho** con posición recordada por usuario («Centrar barra» la restablece).
- **Marca MR en todo.** Monograma en escenas, mapas, láminas, retratos, fichas y bajo los pies de cada token (`tools/brand.py`, idempotente), en la cabecera de los libros y en la barra; portada, cabecera de página, colofón y contraportada del manual y del cuaderno; banner y tarjeta social del repositorio.
- **Libros del Narrador y de los recuerdos** con pestañas y botones renovados.
- **Capturas reales de Foundry** con los tokens a su escala, nueva página de repositorio y manual de 74 páginas (con contraportada) y cuaderno de 10.
- Corrección de la portada del PDF (el monograma ya no se escala a toda la página).

## 1.2.0 — 21 de octubre de 2026

- **Manual del Narrador reescrito** con la estructura de una gran campaña gótica: introducción con resumen, estructura y «Cómo describir el horror»; capítulo del villano con historia, metas, interpretación y los dos sellos; capítulo de Muhar con costumbres, rumores y encuentros; tres partes con lugares claveados (M1–M7, C1–C6, P1–P5) y bloques fijos *Qué hay · Qué quieren · Pistas · Desarrollo · Etiquetas · Riesgos*; tarjetas de personaje (presencia, ideal, vínculo, defecto, voz); acontecimientos especiales; epílogo en seis finales; tablas aleatorias; documentos con referencia desde cada lugar.
- **La Lectura de la Arena**: tres tablas (dónde duerme la séptima vasija, cómo abre la mesa el rey, último argumento de Khety) para variar la partida; el resultado 1 de cada una es la versión de siempre.
- **Maquetación nueva** (HTML + Chrome): dos columnas justificadas con guionado en español, capitulares, cajas de lectura, tablas a ancho completo, planos de Muhar, el pozo y la Corte, y siluetas de personajes con el texto ajustado a su contorno. Manual de 73 páginas y cuaderno de 9.
- Fuente única en `content/manual/*.md`; `tools/manual.py --sync` regenera narrativa, lecturas y dirección de escenas. Los diarios de Foundry usan el texto nuevo y tienen estilo propio para las cajas.
- La validación del PDF usa PyMuPDF y comprueba frases en lugar de párrafos enteros.

### Escenas y dirección incluidas en 1.2.0

- Los 29 fondos de escena pasan a 1920 × 1080 (16:9). Se retiran personajes, multitudes, criaturas y apariciones integrados; las figuras se colocan solo mediante tokens. Las estatuas y relieves arquitectónicos permanecen.
- Nuevas composiciones panorámicas para las láminas y los tres mapas grabados en piedra. Las ilustraciones editoriales del PDF conservan sus versiones propias.
- Encuadre de cobertura en cada cliente, con zoom y paneo limitados a la ilustración para evitar bandas grises. Botón Ajustar pantalla y opción para desactivar la cobertura.
- Menú Figuras con tamaño numérico al aparecer, botones de 240/360/480 px y aplicación a seleccionadas o a todas las figuras de la escena. El reparto se alinea en el primer plano y evita duplicados.
- Bloqueo de giro mediante TokenDocument y ocultación del historial, recorrido y trazado de movimiento mediante la regla nativa de tokens de Foundry v13. Ajustes independientes que no cambian otras escenas.
- 21 introducciones de unas 200 palabras y 22 presentaciones ampliadas, enlazadas en diarios y fichas. Nueva sección de consulta de presentaciones en el manual. El cortejo tiene lectura propia.
- Manual de 73 páginas y cuaderno de nueve páginas, con revisión de páginas casi vacías y láminas de arte completo en el manual.
- Capítulos reorganizados con identificadores nuevos y conservación de los capítulos anteriores; actualización de lecturas y biografías originales sin tocar las modificadas por la mesa; se conservan fichas, recuerdos, secretos, música personal y registro privado cifrado. Escenas originales se adaptan junto con sus objetos; las escenas con fondo o dimensiones personalizados se conservan.


## 1.0.0 — 21 de octubre de 2026

Primera publicación de MR · El Trono de la Sed — La Corte del Rey sin Nombre.

- Cubierta con nueva jerarquía tipográfica, letras ornamentales y composición de horror gótico; se conserva la ilustración aprobada.
- 68 ilustraciones de la misma colección y 22 siluetas completas con transparencia para personajes y criaturas.
- Barra superior del Narrador: lectura, escena, música, volumen, modo de lectura, efectos y reparto.
- 29 diarios de dirección enlazados a sus escenas, con lectura en voz alta y accesos a personajes, PNJ y objetos.
- Nueve bucles instrumentales acreditados y diez efectos y ambientes sin voces, integrados en listas nativas.
- Cinco héroes nativos con fichas amplias y compactas, 34 actores, ayudas y libros de campaña y recuerdos.
- Importación aditiva y actualización de vínculos de dirección sin sustituir imágenes, textos ni progreso personalizados.
- Manifiesto instalable y ambos PDF incluidos en la publicación de GitHub.

Las ediciones 0.1–0.3 fueron revisiones locales de desarrollo.
