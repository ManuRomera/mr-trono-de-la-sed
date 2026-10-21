# Cambios

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
