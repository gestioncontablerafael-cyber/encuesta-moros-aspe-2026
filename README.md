# Encuesta Moros y Cristianos de Aspe 2026

Aplicación web en **Streamlit + Supabase** con dos zonas dentro de la misma web:

1. **Encuesta pública** para los festeros, optimizada para móvil.
2. **Panel privado de Junta Directiva** con filtros, métricas, gráficos, comentarios, participación por comparsa, exportación CSV y generación opcional de enlaces únicos.

La encuesta se ha diseñado como anónima: no pide nombre, apellidos, DNI, email ni teléfono.

## Qué incluye

- 8 comparsas: Moros Alcaná, Moros Aljau, Moros Fauquíes, Moros Sulaymán, Cristianos Contrabandistas de la Sierra Negra, Cristianos Duque de Maqueda, Cristianos Estudiantes y Cristianos Lanceros de Uchel.
- Perfil festero: comparsa, edad, antigüedad y cargo/responsabilidad.
- Escudo de la Unión de Moros y Cristianos visible en la encuesta y el acceso de Junta Directiva.
- Todas las respuestas de texto libre son opcionales y pueden dejarse en blanco.
- Valoración general 1–5.
- Valoración de 12 actos, con `No asistí / No puedo valorarlo` guardado como valor nulo y nunca como cero.
- Acto mejor valorado y acto a revisar.
- Pulsera festera con lógica condicional.
- Preferencia sobre mover el Pasacalles del día 8 al día 7.
- Propuesta de Media Fiesta 2027 en dos días.
- Recomendación 0–10 y cálculo NPS.
- Comentarios abiertos opcionales.
- Panel con filtros por comparsa, edad, antigüedad y cargo.
- Protección de privacidad: no muestra detalle con grupos menores de 5 respuestas (configurable).
- Exportación CSV.
- Generador de enlaces únicos de un solo uso sin almacenar identidad.

## 1. Probar la web sin instalar Supabase

La aplicación viene preparada en **modo demostración**.

1. Instala Python 3.12 o superior.
2. Abre una terminal dentro de esta carpeta.
3. Crea un entorno virtual si quieres.
4. Instala dependencias:

```bash
pip install -r requirements.txt
```

5. Copia:

```text
.streamlit/secrets.example.toml
```

como:

```text
.streamlit/secrets.toml
```

6. Ejecuta:

```bash
streamlit run app.py
```

En modo demo, el panel muestra datos ficticios para que puedas ver el aspecto de los gráficos.

Acceso demo a Junta Directiva:

- Usuario: `junta`
- Contraseña: `demo2026` si no has creado `secrets.toml`; si lo has creado, usa la contraseña que pongas allí.

## 2. Crear la base de datos en Supabase

1. Crea un proyecto nuevo en Supabase.
2. Entra en **SQL Editor**.
3. Copia todo el contenido de `supabase_schema.sql`.
4. Ejecuta el script.
5. En el panel de Supabase, abre **Connect / API Keys** y copia:
   - Project URL.
   - Secret key de servidor (`sb_secret_...`) o equivalente de servicio.

**Importante:** la secret key nunca debe ponerse en el código ni compartirse públicamente. Solo debe ir en los Secrets de Streamlit.

## 3. Configurar la aplicación para datos reales

En `.streamlit/secrets.toml` o en los Secrets de Streamlit Cloud:

```toml
DEMO_MODE = false
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_KEY = "sb_secret_..."
ADMIN_USER = "junta"
ADMIN_PASSWORD = "UNA-CONTRASENA-LARGA-Y-UNICA"
PUBLIC_APP_URL = "https://TU-APP.streamlit.app"
REQUIRE_INVITE_TOKEN = false
MIN_GROUP_SIZE = 5
```

## 4. Publicarla gratis en Streamlit Community Cloud

La forma más sencilla es subir esta carpeta a un repositorio privado o público de GitHub y crear una app en Streamlit Community Cloud apuntando a `app.py`.

Después, en **Settings > Secrets**, pega los valores de `secrets.toml`.

La URL pública quedará parecida a:

```text
https://encuesta-aspe-2026.streamlit.app
```

La zona de Junta Directiva se abre con:

```text
https://encuesta-aspe-2026.streamlit.app/?view=admin
```

## 5. Enlace normal o enlaces únicos

### Opción A · Enlace normal

Deja:

```toml
REQUIRE_INVITE_TOKEN = false
```

Envías a todos los festeros la misma URL. Es la opción más sencilla.

### Opción B · Enlaces únicos de un solo uso

Pon:

```toml
REQUIRE_INVITE_TOKEN = true
```

Entra en el panel privado > **Invitaciones** y genera enlaces por comparsa. Descargarás un CSV con URLs como:

```text
https://...streamlit.app/?t=TOKEN_UNICO
```

La base de datos no guarda el token original: guarda su hash. Tampoco guarda nombre, email o DNI. Cuando el enlace se usa, queda marcado como utilizado.

## 6. Participación real por comparsa

En el panel > **Comparsas**, introduce el número de festeros invitados de cada comparsa. Así el panel calcula:

```text
Participación = respuestas / invitados × 100
```

## 7. Seguridad y privacidad

- No se recogen datos identificativos directos en el formulario.
- La base de datos tiene RLS activado.
- No hay políticas públicas de lectura.
- El acceso a todos los datos se hace desde el servidor Streamlit con una secret key.
- El panel requiere usuario y contraseña.
- Con filtros que dejan menos de 5 respuestas, se ocultan gráficos detallados y comentarios.
- Los enlaces únicos no guardan la identidad del festero.

## 8. Archivos

- `app.py` — encuesta y panel.
- `supabase_schema.sql` — tablas, índices, RLS y función de guardado.
- `requirements.txt` — dependencias.
- `.streamlit/config.toml` — colores y tema.
- `.streamlit/secrets.example.toml` — ejemplo de configuración privada.

## Siguiente mejora recomendada

Cuando la versión básica esté publicada, las mejoras más útiles serían:

1. Añadir el logotipo oficial de la Unión.
2. Dominio propio, por ejemplo `encuesta.morosycristianosaspe.es`.
3. Envío de emails personalizados con los enlaces únicos.
4. Exportación Excel/PDF para Junta Directiva.
5. Resumen automático de comentarios abiertos por temas.
