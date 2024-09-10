![GitHub release (latest by date)](https://img.shields.io/github/v/release/Paco8/plugin.video.orange.spain)
![GitHub all releases](https://img.shields.io/github/downloads/Paco8/plugin.video.orange.spain/total)

# Orange TV Spain for Kodi

_This addon is not officially commissioned/supported by Orange. All product names, logos, and trademarks mentioned in this project are property of their respective owners._

## Description
Watch live channels, recordings and video on demand content from Orange TV Spain in Kodi. Requires a subscription.
This addon is compatible with Kodi 18-21.

---

## Descripción
Con este addon puedes ver los canales en directo, grabaciones, últimos 7 días y TV a la carta de Orange TV España en Kodi. Es necesario estar abonado.
El addon es compatible con Kodi 18-21.

## Instalación
### Instalación manual
Descarga `script.module.ttml2ssa-x.x.x.zip` y `plugin.video.orange.spain-x.x.x.zip` de [la página Releases](https://github.com/Paco8/plugin.video.orange.spain/releases) e instálalos en Kodi en ese orden.

### Instalación por repositorio
- Añade esta URL como fuente en Kodi: `https://paco8.github.io/kodi-repo/`
- En addons selecciona la opción _Instalar desde un archivo zip_ e instala desde la fuente anterior el paquete **repository.spain**
- Ahora en _Instalar desde repositorio_ entra en _Spain OTT repository_, _Addons de vídeo_ e instala **Orange TV**


## Inicio de sesión
Tras la instalación, la primera vez que entres en el addon tienes que ir a la opción `Cuentas` y añadir una cuenta nueva (te pedirá tu nombre de usuario y clave de Orange TV). Después vuelve al menú principal, y si las credenciales son correctas ya podrás empezar a disfrutar Orange TV en Kodi.

## Dispositivos
Orange TV solo permite 5 dispositivos. Como ese límite me parece excesivamente bajo, el addon puede funcionar usando el identificador de otro dispositivo existente, de modo que puedes tener el addon instalado en diferentes dispositivos y solo contará como uno (o ninguno). En la opción `Gestionar dispositivos` puedes elegir qué dispositivo usar para el addon. Hay que tener en cuenta que solo unos cuantos permiten HD (SmartTV, FireTV y Chromecast). Por defecto el addon usará uno de esos dispositivos si ya tienes uno. Si no es así y hay menos de 5 dispositivos, el addon creará automáticamente y usará un dispositivo SmartTV. Si ya había 5 entonces el addon usará el primer dispositivo que encuentre.

## IMPORTANTE
Si tienes problemas a la hora de reproducir un vídeo, trata de seleccionar un dispositivo diferente en "Gestionar dispositivos". En concreto parece que los dispositivos "PC" funcionan con cualquier tipo de vídeo.

En algunos dispositivos también puede ser necesario activar la opción "Usar proxy para la licencia" en la sección "Proxy" de los ajustes.

## Configuración
### Principal
- **`Solo mostrar el contenido incluido en la suscripción`**: si está activada esta opcion el contenido fuera de tu abono no aparecerá en los listados. Si está desactivada sí aparecerá pero marcado en gris, y aunque te dejará intentar reproducirlo seguramente dará un error.
- **`Mostrar el programa en emisión en los canales de TV`**: la lista de canales mostrará además el programa que se está emitiendo en esos momentos en cada canal.
- **`Descargar información extra`**: se descargará información complementaria para cada título, que puede incluir el listado de actores, posters, año, etc.
- **`Intentar reproducir HD en dispositivos SD`**: cuando el addon esté funcionando como dispositivo SD, se intentará reproducir en HD, si es posible.
- **`Enviar progreso al servidor de la plataforma`**: se enviará el progreso de las películas y series que veas, de modo que puedas reanudar la reproducción desde otro dispositivo.
- **`Configurar InputStream Adaptive`**: abre la configuración del addon `InputStream Adaptive`.

### Proxy
- **`Modificar manifiesto`**: Permite modificar las siguientes opciones.
- **`Tratar de solucionar parones`**: trata de solucionar parones en la reproducción en contenido de TV en directo y a la carta.
- **`Subtítulos mejorados`**: por defecto los subtítulos de Orange TV pueden aparecer en posiciones incorrectas o mal alineados. Esta opción modifica los subtítulos para que aparezcan correctamente.
- **`Arreglar los nombres de idiomas`**: arregla el nombre de los idiomas de audio y subtítulos para que puedan mostrarse correctamente en Kodi.
- **`Usar proxy para la licencia`**: esta opción puede ser necesaria para que se puedan reproducir los contenidos en determinados dispositivos o versiones antiguas de Kodi.


## Capturas de pantalla
<img src="https://github.com/Paco8/plugin.video.orange.spain/raw/main/resources/screen1.jpg" width="600"/>
<img src="https://github.com/Paco8/plugin.video.orange.spain/raw/main/resources/screen2.jpg" width="600"/>
<img src="https://github.com/Paco8/plugin.video.orange.spain/raw/main/resources/screen3.jpg" width="600"/>

---

## Soporte para IPTV
Opcionalmente es posible configurar el plugin para IPTV. Esto permite ver los canales en un entorno más parecido a un receptor de TV, y hacer zapping con los botones arriba y abajo y OK. Unas capturas:

<img src="https://github.com/Paco8/plugin.video.orange.spain/raw/main/resources/screen4.jpg" width="600"/>
<img src="https://github.com/Paco8/plugin.video.orange.spain/raw/main/resources/screen5.jpg" width="600"/>

A continuación van las instrucciones para configurarlo. Es necesario instalar el plugin `IPTV Simple Client`. Se encargará de mostrar los canales y la guía en el apartado TV de Kodi.
Este plugin lo puedes encontrar en Addons, Instalar desde repositorio, Kodi addon repository, Clientes PVR, con el nombre **PVR IPTV Simple Client**. Si no está ahí es posible que ya esté instalado pero desactivado. En ese caso hay que ir a Mis addons, Clientes PVR y activarlo.

Una vez instalado IPTV Simple Client vamos a los ajustes de Orange TV.

- En la sección **IPTV** pulsamos en la opción **Crear configuración para IPTV Simple**.
- Reiniciamos Kodi.

Si todo ha ido bien ahora en la sección TV de Kodi podrás acceder a los canales y a la guía de Orange TV.
