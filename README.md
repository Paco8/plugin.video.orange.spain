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

También puedes instalarlo más fácilmente usando [este repositorio](https://github.com/Paco8/kodi-repo/raw/master/mini-repo/repository.spain/repository.spain-1.0.0.zip).

## Inicio de sesión
Tras la instalación, la primera vez que entres en el addon tienes que ir a la opción `Cuentas` y añadir una cuenta nueva (te pedirá tu nombre de usuario y clave de Orange TV). Después vuelve al menú principal, y si las credenciales son correctas ya podrás empezar a disfrutar Orange TV en Kodi.

## Dispositivos
Orange TV solo permite 5 dispositivos. Como ese límite me parece excesivamente bajo, el addon puede funcionar usando el identificador de otro dispositivo existente, de modo que puedes tener el addon instalado en diferentes dispositivos y solo contará como uno (o ninguno). En la opción `Gestionar dispositivos` puedes elegir qué dispositivo usar para el addon. Hay que tener en cuenta que solo unos cuantos permiten HD (SmartTV, FireTV y Chromecast). Por defecto el addon usará uno de esos dispositivos si ya tienes uno. Si no es así y hay menos de 5 dispositivos, el addon creará automáticamente y usará un dispositivo SmartTV. Si ya había 5 entonces el addon usará el primer dispositivo que encuentre.

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

