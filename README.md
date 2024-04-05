![GitHub release (latest by date)](https://img.shields.io/github/v/release/Paco8/plugin.video.orange.spain)
![GitHub all releases](https://img.shields.io/github/downloads/Paco8/plugin.video.orange.spain/total)

# Orange TV Spain for Kodi

_This addon is not officially commissioned/supported by Orange. All product names, logos, and trademarks mentioned in this project are property of their respective owners._

## Description
Watch live channels, recordings and video on demand content from Orange TV Spain in Kodi. Requires a subscription.
This addon is compatible with Kodi 18, 19 and 20.

## Installation
Download `script.module.ttml2ssa-x.x.x.zip` and `plugin.video.orange.spain-x.x.x.zip` from the [Releases page](https://github.com/Paco8/plugin.video.orange.spain/releases) and install them in Kodi in that order.

You may also need to install (or activate) the addon inputstream.adaptive.

---

## Descripción
Con este addon puedes ver los canales en directo, grabaciones, últimos 7 días y TV a la carta de Orange TV España en Kodi. Es necesario estar abonado.
El addon es compatible con Kodi 18, 19 y 20.

## Instalación
Descarga `script.module.ttml2ssa-x.x.x.zip` y `plugin.video.orange.spain-x.x.x.zip` de [la página Releases](https://github.com/Paco8/plugin.video.orange.spain/releases) e instálalos en Kodi en ese orden.

También puedes instalarlo más fácilmente usando [este repositorio](https://github.com/Paco8/kodi-repo/raw/master/mini-repo/repository.spain/repository.spain-1.0.1.zip).

También es posible añadir esta URL como fuente a Kodi: https://paco8.github.io/kodi-repo/  
Instala desde ahí el paquete repository.spain-x.x.x.zip

## Inicio de sesión
Tras la instalación, la primera vez que entres en el addon tienes que ir a la opción `Cuentas` y añadir una cuenta nueva (te pedirá tu nombre de usuario y clave de Orange TV). Después vuelve al menú principal, y si las credenciales son correctas ya podrás empezar a disfrutar Orange TV en Kodi.

## Dispositivos
Orange TV solo permite 5 dispositivos. Como ese límite me parece excesivamente bajo, el addon puede funcionar usando el identificador de otro dispositivo existente, de modo que puedes tener el addon instalado en diferentes dispositivos y solo contará como uno (o ninguno). En la opción `Gestionar dispositivos` puedes elegir qué dispositivo usar para el addon. Hay que tener en cuenta que solo unos cuantos permiten HD (SmartTV, FireTV y Chromecast). Por defecto el addon usará uno de esos dispositivos si ya tienes uno. Si no es así y hay menos de 5 dispositivos, el addon creará automáticamente y usará un dispositivo SmartTV. Si ya había 5 entonces el addon usará el primer dispositivo que encuentre.

## IMPORTANTE
Si tienes problemas a la hora de reproducir un vídeo, trata de seleccionar un dispositivo diferente en "Gestionar dispositivos". En concreto parece que los dispositivos "PC" funcionan con cualquier tipo de vídeo.

En algunos dispositivos también puede ser necesario activar la opción "Usar proxy para la licencia" en la sección "Proxy" de los ajustes.

## Configuración
- **`Solo mostrar el contenido incluido en la suscripción`**: si está activada esta opcion el contenido fuera de tu abono no aparecerá en los listados. Si está desactivada sí aparecerá pero marcado en gris, y aunque te dejará intentar reproducirlo seguramente dará un error.
- **`Mostrar el programa en emisión en los canales de TV`**: la lista de canales mostrará además el programa que se está emitiendo en esos momentos en cada canal.
- **`Descargar información extra`**: se descargará información complementaria para cada título, que puede incluir el listado de actores, posters, año, etc.
- **`Intentar reproducir HD en dispositivos SD`**: cuando el addon esté funcionando como dispositivo SD, se intentará reproducir en HD, si es posible.
- **`Configurar InputStream Adaptive`**: abre la configuración del addon `InputStream Adaptive`.

El resto de opciones tratan de solucionar fallos en Kodi para que el addon funcione lo mejor posible.

- **`Modificar manifiesto`**: soluciona un fallo en `inputstream.adaptive` que impide reproducir canales en directo más de 1 minuto. Esta opción también es necesaria para las siguentes opciones.
- **`Solucionar parones en TV a la carta`**: trata de solucionar parones en la reprodución en contenido de TV a la carta.
- **`Subtítulos mejorados`**: por defecto los subtítulos de Orange TV pueden aparecer en posiciones incorrectas o mal alineados. Esta opción modifica los subtítulos para que aparecan correctamente.
- **`Usar proxy para la licencia`**: puede ser necesario en algunos dispositivos para poder reproducir canales en directo cuando se usa un dispositivo `Smartphone_Android` o `Tablet_Android`.
- **Experimental: `Tipo de DRM`**: lo normal es dejarlo en `Widevine`. `Playready` de momento solo funciona en algunos dispositivos android.

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

- En la sección **IPTV** activamos la opción **Exportar automáticamente canales y guía para IPTV**.
- En la opción **Guardar en esta carpeta** tenemos que seleccionar una carpeta donde se guardará esa información. Puedes usar la carpeta `download` o cualquier otra, o crear una nueva.
- Seleccionamos la opción **Exportar los canales y la guía ahora** y esperamos unos segundos hasta que aparezca una notificación en la parte superior izquierda indicando que se han exportado los canales y la guía.
- Entramos otra vez en los ajustes de Orange TV.
- En la sección **IPTV** seleccionamos **Abrir la configuración de IPTV Simple**.
- (**Kodi 20**) Seleccionamos "Añadir configuración de Addon". En la nueva ventana, en nombre le ponemos por ejemplo `Orange TV`.
- En la nueva ventana que se abre seleccionamos en Ubicación "Local path".
- En "Ruta a la lista M3U" nos vamos a la carpeta que habíamos elegido para exportar los datos de Orange TV y seleccionamos el fichero `orange-channels.m3u8`
- Ahora vamos a la sección **EPG**, y en Ubicación seleccionamos "Local path".
- En "Ruta XMLTV" nos vamos a la carpeta que habíamos elegido para exportar los datos de Orange TV y seleccionamos el fichero `orange-epg.xml`
- (Opcionalmente) En la sección **Catchup** activamos la opción "Enable catchup". Esta opción nos permite ver programas ya emitidos.
- Aceptamos los cambios.
- (**Kodi 20**) Cuando vuelva a salir otra vez la ventana "Ajustes y configuraciones de Addon" pulsamos en Cancelar.
- Reiniciamos Kodi.

Si todo ha ido bien ahora en la sección TV de Kodi podrás acceder a los canales y a la guía de Orange TV.
