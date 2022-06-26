# AplicacionDash

Esta es la primera versión de la aplicación de Dash.
Permite seleccionar una fecha de vencimiento y el tipo de 
opción, del día actual, deseada. 
Con ello obtiene los datos de la opcion elegida, calcula y representa
un gráfico del skew de volatilidad para cada fecha de
ejercicio y opciones Put y Call. Además, se incluyen
los datos de los futuros y de las opciones seleccionadas.
Se ha utilizado dockers para crer una imagen que con los comandos de
gcloud se ha subido a Google Cloud Run para el despliegue de la app.
