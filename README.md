# Encuesta Moros y Cristianos de Aspe 2026

Aplicación Streamlit con dos zonas:

- Encuesta pública anónima para festeros.
- Panel privado para la Junta Directiva con gráficos, filtros, comparativas, interpretación e informes.

## Publicación en Streamlit Community Cloud

1. Sube el contenido de esta carpeta al repositorio de GitHub.
2. En Streamlit Community Cloud selecciona el repositorio.
3. Rama: `main`.
4. Main file path: `app.py`.
5. Pulsa Deploy.

Esta versión ya está conectada a Supabase mediante una clave pública y no necesita configurar Secrets de Streamlit para funcionar.

## Seguridad

Las tablas de respuestas no tienen acceso público directo. La encuesta registra respuestas mediante una función controlada de Supabase y el panel consulta los datos mediante funciones que validan el acceso de Junta. La contraseña de Junta no está incluida en este repositorio.

## Funciones principales

- 8 comparsas con nombres completos.
- Valoración general y de 12 actos.
- Pregunta de ordenación de los 12 actos, de más a menos preferidos.
- Pulsera festera.
- Pasacalles festero día 7 / día 8.
- Media Fiesta 2027.
- Preguntas de texto opcionales.
- Panel con filtros por comparsa, edad, antigüedad y cargo.
- Resumen general, comparsas, actos, pulsera, pasacalles, Media Fiesta y comentarios.
- Informes totales o por comparsa en CSV, Excel y PDF.
- Apartado de ayuda para interpretar resultados.
- Protección de privacidad: no se muestran detalles con menos de 5 respuestas filtradas.
