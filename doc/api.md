La API de peticiones de ALAC:

<https://alac.funde.org/api/v1/requests>

Los párametros para usar la API son los siguientes:

- `startdate` : Fecha de inicio en formato YYYY-MM-DD
- `enddate`: Fecha de finalización del período en formato YYYY-MM-DD
- `page`: Número de página, empezando de cero (0 por defecto)
- `limit`: Máximo de elementos a ser obtenidos (10 por defecto)

**Ejemplo:**

Se desean obtener las peticiones de información realizadas por ALAC durante el año 2018:

- startdate = 2018-01-01
- enddate = 2018-12-31
- page = 0 (valor por defecto)
- limit = 25 (las primeras 25)

El URL quedaría así:

<https://alac.funde.org/api/v1/requests?startdate=2018-01-01&enddate=2018-12-31&page=0&limit=25>

Para ver las siguientes 25, solo hay que cambiar page=1, etc.

La estructura de cada registro es la siguiente (los principales campos):

- \_id: Código de identificación único
- date: Fecha de elaboración de la petición
- overview: resumen de la petición
- detail: detalle de la petición
- start: Fecha de inicio del trámite
- end: Fecha de finalización del trámite
- status: Estado de la petición (en trámite o cerrada)
- result: Resultado del trámite
- comment: Comentarios
- office: Nombre de la oficina
- updates: Anotaciones de actualización del trámite (bitácora)
- documents: Documentos asociados a la petición
