# Mapas grabados en piedra · 0.2.1

Los mapas de Muhar, la Corte y el Pozo se han reinterpretado como incisiones sobre piedra caliza envejecida, vistas de frente. Se muestra únicamente el mapa sobre su superficie: no una sala, una pirámide ni una pared fotografiada en perspectiva. Se han inspeccionado los tres originales, sus recorridos, la numeración de las siete estancias y las seis ranuras marcadas más la séptima limpia.

El manual utiliza los nuevos originales en sus dos páginas de mapas. Muhar incorpora una clave exterior para los cinco lugares numerados. Los PNG se conservan en art/masters/mapa-*-piedra.png; las versiones WebP a calidad 94, en assets/maps/*-piedra.webp. Prompts, referencias y tamaños nativos se registran en stone-maps-art.json. Método: herramienta integrada image_gen, edición a partir de las referencias cartográficas del proyecto.

Foundry conserva las rutas SVG anteriores mediante contenedores que incorporan los WebP. Esto permite que los mundos importados con una versión anterior vean el nuevo arte tras actualizar y recargar, sin reimportar ni reemplazar sus escenas. Se verifican identidad, tamaños, cuadrícula, muros, tokens y demás campos almacenados contra el estado anterior: no cambian. La interpretación pictórica no se presenta como cartografía métrica.

Se ha comprobado la carga de los tres contenedores como imágenes en Chrome, con sus tamaños originales de lienzo y lectura correcta desde un lienzo gráfico. La comprobación de recursos valida que cada contenedor incorpora exactamente el WebP distribuido. El paquete 0.2.1 contiene 27 escenas y 78 recursos, sin rutas ausentes. El ZIP se ha reabierto y comprobado. Esta verificación de imágenes no se presenta como una nueva sesión completa de Foundry.

Se han renderizado y vuelto a comprobar los PDF. El manual conserva 47 páginas y mantiene el contenido auditado; el cuaderno de protagonistas permanece intacto. Los resultados están en pdf-review.json, pdf-source-coverage.json, stone-maps-browser.json y stone-maps-geometry.json. La edición anterior del manual y los generadores de referencia se conservan en editorial/archive/v0.2.0.
