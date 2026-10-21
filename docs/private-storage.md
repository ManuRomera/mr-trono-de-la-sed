# Notas privadas de campaña

Foundry v13 transmite datos completos de documentos del mundo a sus clientes, incluso cuando el usuario no puede abrir su ficha. La propiedad NONE de un diario no constituye un filtro de transmisión: tampoco protege flags ni el texto de una página contra su lectura desde herramientas del navegador.

El Libro de los Muertos cifra sus notas privadas con AES-GCM de 256 bits antes de enviarlas a Foundry. El diario de registro contiene únicamente un indicador de registro y un sobre `privateCampaign: {v, iv, ciphertext}`. Cada escritura utiliza un vector de inicialización aleatorio nuevo de 96 bits y una etiqueta de autenticación de 128 bits. No se guarda una copia en claro en actores, páginas, ajustes del mundo ni mensajes de socket.

La clave se guarda como ajuste de alcance **client**, exclusivamente en el navegador del Narrador, bajo una identidad formada por `world.id:user.id`. No se publica en ajustes de alcance world ni se transmite mediante sockets. Los datos descifrados permanecen en memoria del módulo para dibujar el panel privado. Los jugadores no inicializan ni utilizan este almacén.

## Acceso al mundo

El navegador del Narrador debe disponer de WebCrypto: abre el servidor local mediante localhost o 127.0.0.1, o utiliza HTTPS. Una dirección de red local por HTTP puede no proporcionar esta función. No se sustituye el cifrado por almacenamiento en claro cuando falta.

## Respaldo y recuperación

En el Libro de los Muertos → Guía, «Descargar respaldo privado» crea localmente un JSON que contiene las notas en texto claro. Consérvalo en un lugar privado, separado de los archivos distribuidos a jugadores. La descarga no se sube a Foundry ni a servicios externos.

Para cambiar de navegador o recuperar una campaña después de borrar datos del navegador, pega el contenido del JSON en «Recuperar respaldo local». Se valida el formato y se pide confirmar que se reemplacen las notas. El módulo cifra el respaldo con la clave de ese navegador y conserva el resto de los documentos del mundo.

Si un navegador no tiene la clave válida para el sobre del mundo, el panel queda bloqueado y ofrece recuperación. No genera una nueva campaña, no sustituye el sobre y no muestra un estado inicial falso. Un sobre alterado o una clave errónea también bloquean la lectura.

## Límites prácticos

- El navegador del Narrador y su perfil son un entorno de confianza. Quien controle ese perfil puede acceder a su almacenamiento y a las notas abiertas; el cifrado protege la transmisión a los otros clientes del mundo.
- La pérdida del perfil o de sus datos requiere un respaldo para recuperar las notas. Haz una copia al cerrar la sesión.
- El estado privado tiene un Narrador activo. Otro navegador o usuario GM necesita una copia local para recuperarlo. Al recuperarlo con otra clave, los navegadores anteriores necesitarán importar el respaldo actualizado.
- Este mecanismo protege las notas privadas creadas durante la campaña. El texto original de la aventura, los actores oficiales, sus biografías, los compendios y otros documentos normales siguen usando las herramientas y los permisos habituales de Foundry.
- La primera apertura por el Narrador activo migra el antiguo flag `campaign`: crea el sobre cifrado y elimina el texto claro en una sola actualización. No reinicia progreso ni vacía las notas existentes. Los clientes que recibieron anteriormente texto claro pueden haber conservado una copia; la migración evita nuevas transmisiones en claro, pero no puede retirar datos ya entregados.
