from __future__ import annotations

import base64
import hashlib
import hmac
import io
import secrets as pysecrets
from datetime import datetime
from typing import Any
from textwrap import wrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import Client, create_client
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

# =============================================================
# CONFIGURACIÓN GENERAL
# =============================================================

APP_TITLE = "Encuesta · Moros y Cristianos de Aspe 2026"
ORG_NAME = "Unión de Moros y Cristianos Virgen de las Nieves · Junta Central"
LOGO_PATH = "assets/escudo_union_moros_cristianos.jpg"
COMPARSAS_BG_PATH = "assets/comparsa_background.png"
SUPABASE_URL_PUBLIC = "https://ymssywbftlzdmbkcexee.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_-JwoX59ktysEKiQQ6BeYeg__f1PiPNU"

COMPARSAS = [
    "Moros Alcaná",
    "Moros Aljau",
    "Moros Fauquíes",
    "Moros Sulaymán",
    "Cristianos Contrabandistas de la Sierra Negra",
    "Cristianos Duque de Maqueda",
    "Cristianos Estudiantes",
    "Cristianos Lanceros de Uchel",
]

EDADES = [
    "Menos de 18 años",
    "18–30 años",
    "31–45 años",
    "46–60 años",
    "Más de 60 años",
]

ANTIGUEDADES = [
    "Es mi primer año",
    "2–5 años",
    "6–10 años",
    "11–20 años",
    "Más de 20 años",
]

CARGOS = [
    "No",
    "Sí, cargo festero",
    "Sí, responsabilidad en mi comparsa",
    "Sí, responsabilidad en Junta Central",
    "Otro",
    "Prefiero no indicarlo",
]

ACTOS = {
    "acto_presentacion": "Presentación de Cargos al Alcalde",
    "acto_pregon": "Proclamación de Cargos y Pregón",
    "acto_bandas": "Entrada de Bandas / Pasacalles Autoridades",
    "acto_retreta": "Retreta",
    "acto_pasacalles": "Pasacalles Festero",
    "acto_entrada_mora": "Entrada Mora",
    "acto_guerrilla": "Guerrilla",
    "acto_residencia": "Pasacalle y desfile en Residencia de Ancianos",
    "acto_misa": "Misa Festera",
    "acto_embajada": "Embajada",
    "acto_entrada_cristiana": "Entrada Cristiana",
    "acto_premios": "Fallo Premios Miguel Iborra y Entrega de Banderas",
}

ACTOS_PREGUNTAS = {
    "acto_presentacion": "Presentación de Cargos al Alcalde (día 4)",
    "acto_pregon": "Proclamación de Cargos y Pregón (día 4)",
    "acto_bandas": "Entrada de Bandas / Pasacalles Autoridades (día 7)",
    "acto_retreta": "Retreta (día 7)",
    "acto_pasacalles": "Pasacalles Festero (día 8)",
    "acto_entrada_mora": "Entrada Mora (día 8)",
    "acto_guerrilla": "Guerrilla (día 9)",
    "acto_residencia": "Pasacalle y desfile en Residencia de Ancianos (día 9)",
    "acto_misa": "Misa Festera (día 9)",
    "acto_embajada": "Embajada (día 9)",
    "acto_entrada_cristiana": "Entrada Cristiana (día 10)",
    "acto_premios": "Fallo Premios Miguel Iborra y Entrega de Banderas (día 10)",
}

ACTO_CHOICES = list(ACTOS.values()) + ["Ninguno en particular"]
RATING_OPTIONS = ["1 · Muy mal", "2 · Mal", "3 · Regular", "4 · Bien", "5 · Muy bien", "No asistí / No puedo valorarlo"]

TOTAL_STEPS = 13

st.set_page_config(page_title=APP_TITLE, page_icon="⚔️", layout="wide", initial_sidebar_state="expanded")

# =============================================================
# ESTILO
# =============================================================

def image_data_uri(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    mime = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(file_path.read_bytes()).decode("utf-8")


def build_css() -> str:
    comparsa_bg = image_data_uri(COMPARSAS_BG_PATH)
    return f"""
<style>
:root {{
    --wine: #641f2a;
    --wine-dark: #43121a;
    --gold: #c5a15a;
    --cream: #fbf8f2;
    --ink: #24201d;
    --muted: #6f685f;
    --line: #e8dfd2;
}}
.stApp {{
    background:
        linear-gradient(rgba(252,250,247,.94), rgba(247,241,231,.96)),
        url('{comparsa_bg}');
    background-size: cover;
    background-position: center top;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: var(--ink);
}}
.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}}
.survey-shell {{
    max-width: 780px;
    margin: 0 auto;
    backdrop-filter: blur(1px);
}}
.hero {{
    background: linear-gradient(135deg, var(--wine-dark), var(--wine));
    color: white;
    border-radius: 24px;
    padding: 30px 30px 26px 30px;
    box-shadow: 0 18px 42px rgba(67,18,26,.18);
    border: 1px solid rgba(197,161,90,.45);
    margin-bottom: 22px;
}}
.hero .eyebrow {{
    font-size: .78rem;
    letter-spacing: .15em;
    font-weight: 700;
    color: #ead7ab;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
.hero h1 {{
    color: white;
    margin: 0 0 6px 0;
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    line-height: 1.02;
}}
.hero p {{
    color: #f7efe5;
    margin: 8px 0 0 0;
    line-height: 1.55;
}}
.card {{
    background: rgba(255,255,255,.94);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 8px 30px rgba(65,49,34,.08);
    margin-bottom: 16px;
}}
.section-kicker {{
    color: var(--wine);
    font-weight: 800;
    letter-spacing: .08em;
    text-transform: uppercase;
    font-size: .77rem;
}}
.small-muted {{ color: var(--muted); font-size: .92rem; }}
.privacy-note {{
    background: #f8f2e8;
    border-left: 4px solid var(--gold);
    border-radius: 12px;
    padding: 12px 14px;
    color: #53493f;
    margin: 10px 0 16px 0;
}}
.thanks {{
    text-align: center;
    background: rgba(255,255,255,.96);
    border-radius: 24px;
    padding: 44px 30px;
    border: 1px solid var(--line);
    box-shadow: 0 14px 40px rgba(65,49,34,.08);
}}
.thanks .big {{ font-size: 3rem; }}
.metric-card {{
    border: 1px solid var(--line);
    background: white;
    border-radius: 18px;
    padding: 16px;
    min-height: 110px;
}}
div[data-testid="stMetric"] {{
    background: white;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 6px 22px rgba(65,49,34,.04);
}}
.stButton > button, .stDownloadButton > button {{
    border-radius: 12px !important;
    font-weight: 700 !important;
}}
.stButton > button[kind="primary"] {{
    background: var(--wine) !important;
    border-color: var(--wine) !important;
}}
hr {{ border-color: var(--line) !important; }}

.admin-kpi {{background:#fff;border:1px solid #e7eaf0;border-radius:16px;padding:18px 16px;box-shadow:0 5px 18px rgba(15,30,50,.06);min-height:120px;}}
.admin-kpi .label{{font-size:.78rem;font-weight:800;letter-spacing:.03em;color:#273142;text-transform:uppercase;}}
.admin-kpi .value{{font-size:2rem;font-weight:800;color:#111827;margin-top:6px;}}
.admin-kpi .sub{{font-size:.78rem;color:#667085;margin-top:3px;}}
.dashboard-title{{font-size:2rem;font-weight:900;color:#7c1824;letter-spacing:.02em;margin-bottom:0;}}
.dashboard-sub{{color:#b66a00;font-weight:700;margin-top:-4px;}}
div[data-testid="stSidebar"] {{background:linear-gradient(180deg,#0c2032,#08263d 72%,#0a1d2c);}}
div[data-testid="stSidebar"] * {{color:white;}}
div[data-testid="stSidebar"] div[role="radiogroup"] label {{padding:8px 10px;border-radius:10px;}}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{background:rgba(255,255,255,.08);}}
@media (max-width: 700px) {{
    .stApp {{
        background:
            linear-gradient(rgba(252,250,247,.97), rgba(247,241,231,.98)),
            url('{comparsa_bg}');
        background-size: cover;
        background-position: center top;
        background-attachment: scroll;
    }}
    .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: .8rem; }}
    .hero {{ padding: 24px 20px; border-radius: 18px; }}
    .card {{ padding: 18px 16px; border-radius: 16px; background: rgba(255,255,255,.97); }}
}}
</style>
"""

st.markdown(build_css(), unsafe_allow_html=True)


# =============================================================
# UTILIDADES DE CONFIGURACIÓN / DB
# =============================================================

def secret_value(name: str, default: Any = None) -> Any:
    try:
        return st.secrets[name]
    except Exception:
        return default


@st.cache_resource
def get_supabase() -> Client | None:
    url = secret_value("SUPABASE_URL", SUPABASE_URL_PUBLIC)
    key = secret_value("SUPABASE_PUBLISHABLE_KEY", SUPABASE_PUBLISHABLE_KEY)
    if not url or not key:
        return None
    return create_client(url, key)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_rating(value: str | None) -> int | None:
    if not value or value.startswith("No asistí"):
        return None
    try:
        return int(value.split("·", 1)[0].strip())
    except Exception:
        return None


def validate_invite(raw_token: str | None) -> tuple[bool, str | None, str | None]:
    """Devuelve (válido, comparsa_prefijada, mensaje_error)."""
    require_token = bool(secret_value("REQUIRE_INVITE_TOKEN", False))
    if not require_token:
        return True, None, None
    if not raw_token:
        return False, None, "Este enlace no contiene una invitación válida."
    sb = get_supabase()
    if sb is None:
        return False, None, "La base de datos todavía no está configurada."
    try:
        res = sb.rpc("validate_invitation", {"p_token_hash": hash_token(raw_token)}).execute()
        if not res.data:
            return False, None, "La invitación no es válida."
        row = res.data[0]
        if row.get("used_at"):
            return False, row.get("comparsa"), "Esta invitación ya ha sido utilizada."
        return True, row.get("comparsa"), None
    except Exception:
        return False, None, "No se ha podido comprobar la invitación."


def submit_response(answers: dict[str, Any], raw_token: str | None) -> tuple[bool, str]:
    sb = get_supabase()
    if sb is None:
        return False, "Supabase no está configurado."
    required = ["comparsa", "edad", "antiguedad", "cargo"]
    missing = [key for key in required if not answers.get(key)]
    if missing:
        return False, "No se ha podido enviar porque faltan datos generales de la encuesta. Vuelve al primer paso y comprueba comparsa, edad, antigüedad y cargo."
    try:
        token_hash = hash_token(raw_token) if raw_token else None
        result = sb.rpc(
            "submit_survey",
            {"p_answers": answers, "p_token_hash": token_hash},
        ).execute()
        if result.data:
            return True, "Respuesta registrada correctamente."
        return True, "Respuesta registrada correctamente."
    except Exception as exc:
        text = str(exc)
        if "INVALID_OR_USED_TOKEN" in text:
            return False, "La invitación ya se ha utilizado o no es válida."
        if "MISSING_REQUIRED_SEGMENTATION" in text:
            return False, "Faltan los datos generales (comparsa, edad, antigüedad o cargo). Vuelve al primer paso y complétalos."
        return False, "No se ha podido guardar la respuesta en la base de datos. Inténtalo de nuevo."


def fetch_all_responses() -> pd.DataFrame:
    sb = get_supabase()
    if sb is None:
        return pd.DataFrame()
    user = st.session_state.get("admin_user", "")
    password = st.session_state.get("admin_password", "")
    try:
        res = sb.rpc("admin_get_responses", {"p_username": user, "p_password": password}).execute()
        return flatten_rows(res.data or [])
    except Exception:
        return pd.DataFrame()


def flatten_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    flat: list[dict[str, Any]] = []
    for row in rows:
        ans = row.get("answers") or {}
        record = {
            "id": row.get("id"),
            "created_at": row.get("created_at"),
            **ans,
        }
        for key in ["comparsa", "edad", "antiguedad", "cargo"]:
            if not record.get(key):
                record[key] = row.get(key)
        flat.append(record)
    return pd.DataFrame(flat)


def get_invited_counts() -> dict[str, int]:
    sb = get_supabase()
    if sb is None:
        return {c: 0 for c in COMPARSAS}
    try:
        res = sb.rpc("admin_get_comparsa_config", {"p_username": st.session_state.get("admin_user", ""), "p_password": st.session_state.get("admin_password", "")}).execute()
        counts = {c: 0 for c in COMPARSAS}
        for row in res.data or []:
            if row.get("comparsa") in counts:
                counts[row["comparsa"]] = int(row.get("invited_count") or 0)
        return counts
    except Exception:
        return {c: 0 for c in COMPARSAS}


def save_invited_counts(counts: dict[str, int]) -> tuple[bool, str]:
    sb = get_supabase()
    if sb is None:
        return False, "Supabase no está configurado."
    try:
        payload = [{"comparsa": c, "invited_count": int(counts.get(c, 0))} for c in COMPARSAS]
        sb.rpc("admin_save_comparsa_config", {"p_username": st.session_state.get("admin_user", ""), "p_password": st.session_state.get("admin_password", ""), "p_items": payload}).execute()
        return True, "Número de festeros invitados actualizado."
    except Exception:
        return False, "No se ha podido guardar la configuración."


def create_invite_links(comparsa: str, quantity: int, base_url: str) -> tuple[bool, pd.DataFrame | None, str]:
    if quantity <= 0:
        return False, None, "Indica un número de enlaces mayor que cero."
    sb = get_supabase()
    if sb is None:
        return False, None, "Supabase no está configurado."
    try:
        raw_tokens = [pysecrets.token_urlsafe(24) for _ in range(quantity)]
        payload = [{"token_hash": hash_token(t), "comparsa": comparsa} for t in raw_tokens]
        sb.rpc("admin_insert_invitations", {
            "p_username": st.session_state.get("admin_user", ""),
            "p_password": st.session_state.get("admin_password", ""),
            "p_items": payload,
        }).execute()
        links = [{"comparsa": comparsa, "enlace": f"{base_url.rstrip('/')}?t={t}"} for t in raw_tokens]
        return True, pd.DataFrame(links), "Enlaces únicos creados correctamente."
    except Exception:
        return False, None, "No se han podido crear los enlaces."

def delete_responses(response_ids: list[str]) -> tuple[bool, str]:
    if not response_ids:
        return False, "Selecciona al menos una encuesta."
    sb = get_supabase()
    if sb is None:
        return False, "Supabase no está configurado."
    try:
        res = sb.rpc("admin_delete_responses", {
            "p_username": st.session_state.get("admin_user", ""),
            "p_password": st.session_state.get("admin_password", ""),
            "p_ids": response_ids,
        }).execute()
        deleted = int(res.data or 0)
        return True, f"Se han borrado {deleted} encuesta(s)."
    except Exception:
        return False, "No se han podido borrar las encuestas seleccionadas."


def delete_all_responses() -> tuple[bool, str]:
    sb = get_supabase()
    if sb is None:
        return False, "Supabase no está configurado."
    try:
        res = sb.rpc("admin_delete_all_responses", {
            "p_username": st.session_state.get("admin_user", ""),
            "p_password": st.session_state.get("admin_password", ""),
        }).execute()
        deleted = int(res.data or 0)
        return True, f"Se han borrado todas las respuestas ({deleted})."
    except Exception:
        return False, "No se han podido borrar todas las respuestas."


# =============================================================
# ENCUESTA PÚBLICA
# =============================================================

def survey_header(step: int | None = None) -> None:
    st.markdown('<div class="survey-shell">', unsafe_allow_html=True)
    logo_left, logo_center, logo_right = st.columns([1.6, 1, 1.6])
    with logo_center:
        st.image(LOGO_PATH, width=185)
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Encuesta de satisfacción</div>
            <h1>Fiestas de Moros y Cristianos de Aspe 2026</h1>
            <p>{ORG_NAME}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if step is not None and step > 0:
        st.progress(step / TOTAL_STEPS, text=f"Paso {step} de {TOTAL_STEPS}")


def survey_footer() -> None:
    st.markdown("---")
    st.markdown(
        '<div class="small-muted" style="text-align:center;line-height:1.5">Encuesta anónima · Responsable: Unión de Moros y Cristianos Virgen de las Nieves de Aspe. Finalidad: conocer la opinión de los festeros y mejorar la organización de las fiestas. No se solicitan datos identificativos directos. Los resultados se tratarán de forma agregada y exclusivamente para fines organizativos y estadísticos internos, conforme al RGPD (UE) 2016/679 y la LOPDGDD 3/2018. Para ejercer los derechos que correspondan en materia de protección de datos, puede dirigirse a la entidad organizadora a través de sus canales oficiales.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="text-align:center;margin-top:10px"><a href="?view=admin">Acceso Junta Directiva</a></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def init_survey_state() -> None:
    st.session_state.setdefault("survey_step", 0)
    st.session_state.setdefault("survey_done", False)
    st.session_state.setdefault("survey_answers", {})


def persist_answers(*keys: str) -> None:
    """Guarda respuestas fuera del ciclo de vida de los widgets de Streamlit."""
    store = st.session_state.setdefault("survey_answers", {})
    for key in keys:
        if key in st.session_state:
            store[key] = st.session_state.get(key)


def saved_answer(key: str, default: Any = None) -> Any:
    if key in st.session_state:
        return st.session_state.get(key)
    return st.session_state.get("survey_answers", {}).get(key, default)


def nav_buttons(previous: bool = True, next_label: str = "Siguiente", disabled: bool = False) -> tuple[bool, bool]:
    col1, col2 = st.columns([1, 1])
    back_clicked = False
    next_clicked = False
    with col1:
        if previous:
            back_clicked = st.button("← Anterior", use_container_width=True)
    with col2:
        next_clicked = st.button(next_label, type="primary", use_container_width=True, disabled=disabled)
    return back_clicked, next_clicked


def render_survey() -> None:
    init_survey_state()
    raw_token = st.query_params.get("t")
    valid, locked_comparsa, token_error = validate_invite(raw_token)

    if not valid:
        survey_header()
        st.error(token_error or "Invitación no válida.")
        st.info("Si has recibido este enlace por email, comprueba que lo has abierto completo. Si el problema continúa, solicita un nuevo enlace a la organización.")
        survey_footer()
        return

    if st.session_state.survey_done:
        survey_header()
        st.markdown(
            f"""
            <div class="thanks">
                <div class="big">✓</div>
                <h2>¡Muchas gracias por tu participación!</h2>
                <p>Tu respuesta ha quedado registrada.</p>
                <p>Gracias por dedicar unos minutos a ayudarnos a seguir mejorando las Fiestas de Moros y Cristianos de Aspe.</p>
                <p><strong>{ORG_NAME}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        survey_footer()
        return

    step = int(st.session_state.survey_step)
    survey_header(step if step else None)

    if step == 0:
        st.markdown(
            """
            <div class="card">
                <div class="section-kicker">Bienvenida</div>
                <h2>Tu opinión nos ayuda a mejorar</h2>
                <p>Queremos conocer tu valoración sobre los actos celebrados en 2026 y tu opinión sobre posibles cambios de cara a 2027.</p>
                <div class="privacy-note"><strong>La encuesta es anónima.</strong> No se solicita nombre, email, DNI ni teléfono. <strong>Todas las respuestas que requieren escribir texto son opcionales:</strong> puedes dejarlas en blanco y continuar.</div>
                <p class="small-muted">Duración aproximada: 5–7 minutos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("COMENZAR ENCUESTA", type="primary", use_container_width=True):
            st.session_state.survey_step = 1
            st.rerun()

    elif step == 1:
        st.markdown('<div class="section-kicker">1 · Datos generales</div><h2>Perfil festero</h2>', unsafe_allow_html=True)
        if locked_comparsa and locked_comparsa in COMPARSAS:
            st.session_state["comparsa"] = locked_comparsa
            st.info(f"Comparsa de la invitación: **{locked_comparsa}**")
        else:
            st.selectbox("¿A qué comparsa perteneces? *", COMPARSAS, key="comparsa", index=None, placeholder="Selecciona tu comparsa")
        st.selectbox("¿Cuál es tu rango de edad? *", EDADES, key="edad", index=None, placeholder="Selecciona una opción")
        st.selectbox("¿Cuántos años llevas participando en las Fiestas? *", ANTIGUEDADES, key="antiguedad", index=None, placeholder="Selecciona una opción")
        st.selectbox("¿Has desempeñado algún cargo o responsabilidad festera durante las Fiestas 2026? *", CARGOS, key="cargo", index=None, placeholder="Selecciona una opción")
        if st.session_state.get("cargo") == "Otro":
            st.text_input("Si quieres, indica cuál (opcional)", key="cargo_otro")
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 0
            st.rerun()
        if nxt:
            required = [st.session_state.get("comparsa"), st.session_state.get("edad"), st.session_state.get("antiguedad"), st.session_state.get("cargo")]
            if not all(required):
                st.error("Completa las preguntas obligatorias para continuar.")
            else:
                persist_answers("comparsa", "edad", "antiguedad", "cargo", "cargo_otro")
                st.session_state.survey_step = 2
                st.rerun()

    elif step == 2:
        st.markdown('<div class="section-kicker">2 · Valoración general</div><h2>¿Cómo han sido las Fiestas 2026?</h2>', unsafe_allow_html=True)
        st.radio(
            "En una escala del 1 al 5, ¿cómo valorarías el desarrollo general de las Fiestas 2026? *",
            [1, 2, 3, 4, 5],
            horizontal=True,
            key="valoracion_general",
            index=None,
            captions=["Muy mal", "Mal", "Regular", "Bien", "Muy bien"],
        )
        st.selectbox(
            "Pensando en años anteriores, ¿cómo consideras que han evolucionado las Fiestas? *",
            ["Han mejorado mucho", "Han mejorado", "Se mantienen aproximadamente igual", "Han empeorado", "Han empeorado mucho", "No puedo valorarlo"],
            key="evolucion",
            index=None,
            placeholder="Selecciona una opción",
        )
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 1
            st.rerun()
        if nxt:
            if st.session_state.get("valoracion_general") is None or not st.session_state.get("evolucion"):
                st.error("Completa las dos preguntas para continuar.")
            else:
                persist_answers("valoracion_general", "evolucion")
                st.session_state.survey_step = 3
                st.rerun()

    elif step in [3, 4, 5, 6]:
        groups = {
            3: ["acto_presentacion", "acto_pregon", "acto_bandas"],
            4: ["acto_retreta", "acto_pasacalles", "acto_entrada_mora"],
            5: ["acto_guerrilla", "acto_residencia", "acto_misa"],
            6: ["acto_embajada", "acto_entrada_cristiana", "acto_premios"],
        }
        st.markdown(f'<div class="section-kicker">3 · Valoración de los actos</div><h2>Actos · {step-2}/4</h2>', unsafe_allow_html=True)
        st.caption("Valora del 1 al 5. Si no asististe o no puedes valorarlo, elige la última opción. Esa respuesta no se contará como cero.")
        for key in groups[step]:
            st.selectbox(ACTOS_PREGUNTAS[key] + " *", RATING_OPTIONS, key=key + "_ui", index=None, placeholder="Selecciona tu valoración")
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = step - 1
            st.rerun()
        if nxt:
            if any(st.session_state.get(k + "_ui") is None for k in groups[step]):
                st.error("Valora los tres actos para continuar.")
            else:
                for k in groups[step]:
                    st.session_state[k] = normalize_rating(st.session_state.get(k + "_ui"))
                persist_answers(*groups[step])
                st.session_state.survey_step = step + 1
                st.rerun()

    elif step == 7:
        st.markdown('<div class="section-kicker">4 · Ranking de actos</div><h2>Ordena los actos de más a menos</h2>', unsafe_allow_html=True)
        st.caption("Selecciona los 12 actos en el orden que prefieras: primero el que más te ha gustado y último el que menos. Debes incluirlos todos.")
        ranking = st.multiselect(
            "Tu orden de preferencia *",
            list(ACTOS.values()),
            default=st.session_state.get("ranking_actos", []),
            max_selections=len(ACTOS),
            key="ranking_actos_ui",
            placeholder="Ve seleccionando los actos de mejor a peor",
        )
        if ranking:
            st.markdown("**Orden actual:**")
            for i, acto in enumerate(ranking, 1):
                st.write(f"{i}. {acto}")
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 6
            st.rerun()
        if nxt:
            if len(ranking) != len(ACTOS):
                st.error("Para continuar, ordena los 12 actos.")
            else:
                st.session_state["ranking_actos"] = ranking
                persist_answers("ranking_actos")
                st.session_state.survey_step = 8
                st.rerun()

    elif step == 8:
        st.markdown('<div class="section-kicker">5 · Conclusiones sobre los actos</div><h2>¿Qué destacarías y qué revisarías?</h2>', unsafe_allow_html=True)
        st.selectbox("¿Qué acto destacarías especialmente de forma positiva? *", ACTO_CHOICES, key="acto_destaca", index=None, placeholder="Selecciona una opción")
        st.text_area("Si quieres, cuéntanos brevemente por qué (opcional)", key="acto_destaca_por_que", height=100)
        st.selectbox("¿Qué acto consideras que debería revisarse o mejorarse especialmente? *", ACTO_CHOICES, key="acto_mejorar", index=None, placeholder="Selecciona una opción")
        st.text_area("Si quieres, dinos qué cambiarías (opcional)", key="acto_mejorar_que_cambiarias", height=100)
        st.selectbox(
            "Pensando en el conjunto de las Fiestas, ¿qué opinas de la cantidad de actos? *",
            ["Hay demasiados actos", "La cantidad de actos es adecuada", "Se podrían añadir más actos", "No tengo una opinión clara"],
            key="cantidad_actos",
            index=None,
            placeholder="Selecciona una opción",
        )
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 7
            st.rerun()
        if nxt:
            if not st.session_state.get("acto_destaca") or not st.session_state.get("acto_mejorar") or not st.session_state.get("cantidad_actos"):
                st.error("Completa las preguntas obligatorias para continuar.")
            else:
                persist_answers("acto_destaca", "acto_destaca_por_que", "acto_mejorar", "acto_mejorar_que_cambiarias", "cantidad_actos")
                st.session_state.survey_step = 9
                st.rerun()

    elif step == 9:
        st.markdown('<div class="section-kicker">6 · Pulsera festera</div><h2>Uso y valoración de la pulsera</h2>', unsafe_allow_html=True)
        st.radio("¿Utilizaste la pulsera festera durante las Fiestas 2026? *", ["Sí", "No"], horizontal=True, key="pulsera_usada_ui", index=None)
        if st.session_state.get("pulsera_usada_ui") == "Sí":
            st.selectbox(
                "¿Te resultó útil y práctica para el control de accesos, identificación, etc.? *",
                ["Sí, totalmente", "En parte", "No, me generó problemas o inconvenientes"],
                key="pulsera_utilidad",
                index=None,
                placeholder="Selecciona una opción",
            )
            st.radio("En una escala del 1 al 5, ¿cómo valorarías la pulsera festera en general? *", [1,2,3,4,5], horizontal=True, key="pulsera_valoracion", index=None)
            st.text_area("¿Qué mejorarías de la pulsera festera? (opcional)", key="pulsera_mejoras", help="Puedes dejar esta respuesta en blanco y continuar.", height=100)
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 8
            st.rerun()
        if nxt:
            used_ui = st.session_state.get("pulsera_usada_ui")
            if used_ui is None:
                st.error("Indica si utilizaste la pulsera.")
            elif used_ui == "Sí" and (not st.session_state.get("pulsera_utilidad") or st.session_state.get("pulsera_valoracion") is None):
                st.error("Completa la valoración de la pulsera para continuar.")
            else:
                st.session_state["pulsera_usada"] = used_ui == "Sí"
                if used_ui == "No":
                    st.session_state["pulsera_utilidad"] = None
                    st.session_state["pulsera_valoracion"] = None
                    st.session_state["pulsera_mejoras"] = ""
                persist_answers("pulsera_usada", "pulsera_utilidad", "pulsera_valoracion", "pulsera_mejoras")
                st.session_state.survey_step = 10
                st.rerun()

    elif step == 10:
        st.markdown('<div class="section-kicker">7 · Pasacalles Festero</div><h2>Posible cambio de día</h2>', unsafe_allow_html=True)
        st.info("Actualmente el Pasacalles Festero se celebra el día 8 de agosto. Se plantea la posibilidad de trasladarlo al día 7 de agosto.")
        st.radio(
            "¿Qué opción prefieres? *",
            ["Prefiero que pase a celebrarse el día 7", "Prefiero que se mantenga el día 8", "Me resulta indiferente"],
            key="pasacalles_preferencia",
            index=None,
        )
        st.text_area("Si quieres, explica brevemente el motivo de tu respuesta (opcional)", key="pasacalles_motivo", height=110)
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 9
            st.rerun()
        if nxt:
            if not st.session_state.get("pasacalles_preferencia"):
                st.error("Selecciona una opción para continuar.")
            else:
                persist_answers("pasacalles_preferencia", "pasacalles_motivo")
                st.session_state.survey_step = 11
                st.rerun()

    elif step == 11:
        st.markdown('<div class="section-kicker">8 · Media Fiesta 2027</div><h2>Propuesta de dos días</h2>', unsafe_allow_html=True)
        st.info("Se está valorando organizar la Media Fiesta 2027 así: Día 1 por la noche, Retreta. Día 2, Pasacalles y Entrada de Bandas.")
        st.radio(
            "¿Te gustaría que la Media Fiesta 2027 se organizara de este modo, en dos días? *",
            ["Sí, me parece una buena propuesta", "No, prefiero que se mantenga el formato actual", "Me resulta indiferente"],
            key="media_fiesta_preferencia",
            index=None,
        )
        st.text_area("Sugerencias o comentarios sobre la Media Fiesta 2027 (opcional)", key="media_fiesta_comentarios", height=110)
        back, nxt = nav_buttons()
        if back:
            st.session_state.survey_step = 10
            st.rerun()
        if nxt:
            if not st.session_state.get("media_fiesta_preferencia"):
                st.error("Selecciona una opción para continuar.")
            else:
                persist_answers("media_fiesta_preferencia", "media_fiesta_comentarios")
                st.session_state.survey_step = 12
                st.rerun()

    elif step == 12:
        st.markdown('<div class="section-kicker">9 · Mirando al futuro</div><h2>Valoración final</h2>', unsafe_allow_html=True)
        st.slider(
            "De 0 a 10, ¿hasta qué punto recomendarías a otro festero participar activamente en las Fiestas de Moros y Cristianos de Aspe? *",
            0, 10, key="recomendacion",
        )
        st.text_area(
            "¿Qué mejorarías de cara a las Fiestas 2027? (opcional)",
            key="mejoras_2027",
            help="Puedes hablarnos de actos, horarios, organización, desfiles, pulsera, convivencia, servicios o cualquier otro aspecto que consideres importante.",
            height=125,
        )
        st.text_area("¿Hay alguna propuesta o comentario que no te hayamos preguntado y quieras trasladar a la Junta Central? (opcional)", key="comentario_final", height=125)
        back, nxt = nav_buttons(next_label="ENVIAR ENCUESTA")
        if back:
            st.session_state.survey_step = 11
            st.rerun()
        if nxt:
            answers = collect_answers()
            ok, msg = submit_response(answers, raw_token)
            if ok:
                st.session_state.survey_done = True
                st.session_state.survey_step = TOTAL_STEPS
                st.rerun()
            else:
                st.error(msg)

    survey_footer()


def collect_answers() -> dict[str, Any]:
    keys = [
        "comparsa", "edad", "antiguedad", "cargo", "cargo_otro",
        "valoracion_general", "evolucion",
        *ACTOS.keys(), "ranking_actos",
        "acto_destaca", "acto_destaca_por_que", "acto_mejorar", "acto_mejorar_que_cambiarias", "cantidad_actos",
        "pulsera_usada", "pulsera_utilidad", "pulsera_valoracion", "pulsera_mejoras",
        "pasacalles_preferencia", "pasacalles_motivo",
        "media_fiesta_preferencia", "media_fiesta_comentarios",
        "recomendacion", "mejoras_2027", "comentario_final",
    ]
    persist_answers("recomendacion", "mejoras_2027", "comentario_final")
    return {k: saved_answer(k) for k in keys}

# =============================================================
# ADMIN / PANEL
# =============================================================

def admin_authenticated() -> bool:
    return bool(st.session_state.get("admin_authenticated"))


def render_admin_login() -> bool:
    admin_logo_left, admin_logo_center, admin_logo_right = st.columns([2, 1, 2])
    with admin_logo_center:
        st.image(LOGO_PATH, width=150)
    st.markdown("## Acceso Junta Directiva")
    st.caption("Área privada de resultados y gestión de la encuesta.")
    with st.form("admin_login"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if submitted:
        sb = get_supabase()
        ok = False
        try:
            result = sb.rpc("admin_login", {"p_username": user, "p_password": password}).execute() if sb else None
            ok = bool(result and result.data is True)
        except Exception:
            ok = False
        if ok:
            st.session_state.admin_authenticated = True
            st.session_state.admin_user = user
            st.session_state.admin_password = password
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    return False


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    st.sidebar.markdown("### Filtros")
    selected = {}
    for label, col, options in [
        ("Comparsa", "comparsa", COMPARSAS),
        ("Edad", "edad", EDADES),
        ("Antigüedad", "antiguedad", ANTIGUEDADES),
        ("Cargo / responsabilidad", "cargo", CARGOS),
    ]:
        value = st.sidebar.selectbox(label, ["TODAS"] + options, key=f"f_{col}")
        selected[col] = value
    out = df.copy()
    for col, value in selected.items():
        if value != "TODAS" and col in out.columns:
            out = out[out[col] == value]
    return out, selected


def safe_pct(series: pd.Series, predicate=None) -> float:
    s = series.dropna()
    if len(s) == 0:
        return 0.0
    if predicate is None:
        return float(s.mean() * 100)
    return float(predicate(s).mean() * 100)


def nps_score(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return 0.0
    promoters = (s >= 9).mean() * 100
    detractors = (s <= 6).mean() * 100
    return float(promoters - detractors)


def donut_chart(df: pd.DataFrame, col: str, title: str):
    counts = df[col].fillna("Sin respuesta").value_counts().reset_index()
    counts.columns = ["Respuesta", "Respuestas"]
    fig = px.pie(counts, names="Respuesta", values="Respuestas", hole=.55, title=title)
    fig.update_layout(margin=dict(t=55, b=15, l=15, r=15), legend_title_text="")
    return fig


def ranking_summary(df: pd.DataFrame) -> pd.DataFrame:
    scores = {name: [] for name in ACTOS.values()}
    if "ranking_actos" not in df.columns:
        return pd.DataFrame(columns=["Acto", "Puntuación ranking", "Posición media"])
    for value in df["ranking_actos"].dropna():
        ranking = value if isinstance(value, list) else []
        if len(ranking) != len(ACTOS):
            continue
        for pos, name in enumerate(ranking, 1):
            if name in scores:
                scores[name].append(pos)
    rows = []
    for name, positions in scores.items():
        if positions:
            avg_pos = float(np.mean(positions))
            points = len(ACTOS) + 1 - avg_pos
            rows.append({"Acto": name, "Puntuación ranking": round(points, 2), "Posición media": round(avg_pos, 2)})
    return pd.DataFrame(rows).sort_values("Posición media") if rows else pd.DataFrame(columns=["Acto", "Puntuación ranking", "Posición media"])


def acts_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, name in ACTOS.items():
        vals = pd.to_numeric(df.get(key, pd.Series(dtype=float)), errors="coerce").dropna()
        rows.append({
            "Acto": name,
            "Valoración media": round(float(vals.mean()), 2) if len(vals) else np.nan,
            "Respuestas que valoran": int(len(vals)),
            "Valoraciones 4-5 %": round(float((vals >= 4).mean() * 100), 1) if len(vals) else np.nan,
        })
    return pd.DataFrame(rows)


def interpretation_points(df: pd.DataFrame, invited: dict[str, int] | None = None) -> list[str]:
    if df.empty:
        return ["Todavía no hay respuestas suficientes para interpretar los resultados."]
    pts = []
    avg = pd.to_numeric(df.get("valoracion_general"), errors="coerce").mean()
    if not pd.isna(avg):
        level = "muy positiva" if avg >= 4.25 else "positiva" if avg >= 3.75 else "intermedia" if avg >= 3 else "mejorable"
        pts.append(f"La valoración general es {level}: {avg:.2f} sobre 5.")
    rec = pd.to_numeric(df.get("recomendacion"), errors="coerce").mean()
    if not pd.isna(rec):
        pts.append(f"La recomendación media es {rec:.1f} sobre 10; el NPS es {nps_score(df.get('recomendacion', pd.Series(dtype=float))):+.0f}.")
    acts = acts_summary(df).dropna(subset=["Valoración media"]).sort_values("Valoración media", ascending=False)
    if not acts.empty:
        pts.append(f"El acto mejor valorado es {acts.iloc[0]['Acto']} ({acts.iloc[0]['Valoración media']:.2f}/5).")
        pts.append(f"El acto con menor valoración media es {acts.iloc[-1]['Acto']} ({acts.iloc[-1]['Valoración media']:.2f}/5), por lo que conviene revisarlo junto con los comentarios abiertos.")
    if "pulsera_usada" in df:
        usage = safe_pct(df["pulsera_usada"])
        pts.append(f"El {usage:.1f}% declara haber utilizado la pulsera festera.")
    if "pasacalles_preferencia" in df:
        p7 = (df["pasacalles_preferencia"] == "Prefiero que pase a celebrarse el día 7").mean() * 100
        p8 = (df["pasacalles_preferencia"] == "Prefiero que se mantenga el día 8").mean() * 100
        pts.append(f"Sobre el Pasacalles: {p7:.1f}% prefiere el día 7 y {p8:.1f}% mantener el día 8.")
    if "media_fiesta_preferencia" in df:
        yes = (df["media_fiesta_preferencia"] == "Sí, me parece una buena propuesta").mean() * 100
        pts.append(f"El {yes:.1f}% apoya la propuesta de Media Fiesta 2027 en dos días.")
    rank = ranking_summary(df)
    if not rank.empty:
        pts.append(f"En la ordenación global, el acto que aparece más arriba es {rank.iloc[0]['Acto']} (posición media {rank.iloc[0]['Posición media']:.2f}).")
    return pts


def report_pdf_bytes(df: pd.DataFrame, scope_name: str, invited: dict[str, int]) -> bytes:
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=landscape(A4), rightMargin=14*mm, leftMargin=14*mm, topMargin=13*mm, bottomMargin=13*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title2", parent=styles["Title"], textColor=colors.HexColor("#7c1824"), alignment=TA_CENTER, fontSize=20, leading=24)
    story = [Paragraph("Informe de resultados · Encuesta Fiestas de Moros y Cristianos de Aspe 2026", title), Spacer(1, 5*mm), Paragraph(f"Ámbito: <b>{scope_name}</b> · Respuestas analizadas: <b>{len(df)}</b>", styles["Normal"]), Spacer(1, 4*mm)]
    for pt in interpretation_points(df, invited):
        story.append(Paragraph("• " + pt, styles["BodyText"]))
        story.append(Spacer(1, 1.5*mm))
    story.append(Spacer(1, 4*mm))
    acts = acts_summary(df).sort_values("Valoración media", ascending=False)
    data = [["Acto", "Media", "N", "% 4-5"]] + [[r["Acto"], "—" if pd.isna(r["Valoración media"]) else f"{r['Valoración media']:.2f}", str(r["Respuestas que valoran"]), "—" if pd.isna(r["Valoraciones 4-5 %"]) else f"{r['Valoraciones 4-5 %']:.1f}%"] for _, r in acts.iterrows()]
    t = Table(data, colWidths=[125*mm, 25*mm, 20*mm, 25*mm])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0c2032')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#d8dde6')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f8fa')])]))
    story += [Paragraph("Valoración de actos", styles["Heading2"]), t, Spacer(1, 4*mm), Paragraph("Nota de privacidad: el informe presenta resultados agregados y no contiene nombre, DNI, email ni teléfono.", styles["Italic"])]
    doc.build(story)
    return out.getvalue()


def report_excel_bytes(df: pd.DataFrame, invited: dict[str, int]) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        export_df = df.drop(columns=["id"], errors="ignore").copy()
        export_df.to_excel(writer, sheet_name="Respuestas", index=False)
        acts_summary(df).to_excel(writer, sheet_name="Actos", index=False)
        ranking_summary(df).to_excel(writer, sheet_name="Ranking actos", index=False)
        pd.DataFrame({"Interpretación": interpretation_points(df, invited)}).to_excel(writer, sheet_name="Interpretacion", index=False)
    return out.getvalue()


def top_filters(df: pd.DataFrame) -> pd.DataFrame:
    cols = st.columns([1.35,1.35,1.35,1.6])
    selections = {}
    with cols[0]: selections["comparsa"] = st.selectbox("COMPARSA", ["Todas"] + COMPARSAS, key="top_comparsa")
    with cols[1]: selections["edad"] = st.selectbox("EDAD", ["Todas"] + EDADES, key="top_edad")
    with cols[2]: selections["antiguedad"] = st.selectbox("ANTIGÜEDAD FESTERA", ["Todas"] + ANTIGUEDADES, key="top_antiguedad")
    with cols[3]: selections["cargo"] = st.selectbox("CARGO / RESPONSABILIDAD", ["Todos"] + CARGOS, key="top_cargo")
    out = df.copy()
    for col, val in selections.items():
        if val not in ["Todas", "Todos"]:
            out = out[out[col] == val]
    return out


def render_admin() -> None:
    if not admin_authenticated():
        render_admin_login()
        return

    with st.sidebar:
        st.image(LOGO_PATH, width=120)
        st.markdown("### UNIÓN DE MOROS Y CRISTIANOS\n**VIRGEN DE LAS NIEVES · ASPE**")
        section = st.radio("", ["Resumen general", "Comparsas", "Actos", "Pulsera festera", "Pasacalles festero", "Media Fiesta 2027", "Comentarios y sugerencias", "Informes", "Gestionar encuestas", "Cómo interpretar"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("Cerrar sesión", use_container_width=True):
            for k in ["admin_authenticated","admin_user","admin_password"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.caption("Encuesta Fiestas de Moros y Cristianos de Aspe 2026")

    df = fetch_all_responses()
    st.markdown(f'<div class="dashboard-title">{section.upper()}</div><div class="dashboard-sub">Encuesta Fiestas de Moros y Cristianos de Aspe 2026</div>', unsafe_allow_html=True)
    if df.empty:
        if section == "Gestionar encuestas":
            st.success("La base de datos está limpia: actualmente hay 0 encuestas registradas.")
            st.caption("Cuando empiecen a llegar respuestas, aquí podrás seleccionar y borrar encuestas concretas o vaciar todas las respuestas.")
        else:
            st.warning("Todavía no hay respuestas registradas. Todos los datos están vacíos y el panel se completará automáticamente cuando comiencen a responder los festeros.")
        return

    st.caption(f"Datos en tiempo real · Última actualización: {datetime.now():%d/%m/%Y %H:%M}")
    filtered = top_filters(df)
    min_group = 5
    if len(filtered) < min_group:
        st.warning(f"Por privacidad, no se muestran detalles cuando el filtro deja menos de {min_group} respuestas.")
        return

    invited = get_invited_counts()
    total_invited = sum(invited.values())
    n = len(filtered)
    avg = pd.to_numeric(filtered.get("valoracion_general"), errors="coerce").mean()
    rec = pd.to_numeric(filtered.get("recomendacion"), errors="coerce").mean()
    usage = safe_pct(filtered.get("pulsera_usada", pd.Series(dtype=float)))
    p7 = (filtered.get("pasacalles_preferencia", pd.Series(dtype=str)) == "Prefiero que pase a celebrarse el día 7").mean()*100 if n else 0
    mf = (filtered.get("media_fiesta_preferencia", pd.Series(dtype=str)) == "Sí, me parece una buena propuesta").mean()*100 if n else 0
    participation = (len(df)/total_invited*100) if total_invited else 0

    if section == "Resumen general":
        cards = st.columns(5)
        vals = [("RESPUESTAS RECIBIDAS",f"{n}","Total de respuestas filtradas"),("PARTICIPACIÓN",f"{participation:.1f}%" if total_invited else "—","Sobre el total configurado"),("VALORACIÓN GENERAL",f"{avg:.2f} / 5" if not pd.isna(avg) else "—","Media de satisfacción"),("RECOMENDACIÓN",f"{rec:.1f} / 10" if not pd.isna(rec) else "—","Media 0-10"),("COMPARSAS ACTIVAS",f"{filtered['comparsa'].nunique()} / 8","Con respuestas")]
        for c,(lab,val,sub) in zip(cards,vals):
            c.markdown(f'<div class="admin-kpi"><div class="label">{lab}</div><div class="value">{val}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)
        st.write("")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Uso de pulsera", f"{usage:.0f}%")
        m2.metric("Apoyo Pasacalles día 7", f"{p7:.0f}%")
        m3.metric("Apoyo Media Fiesta 2 días", f"{mf:.0f}%")
        m4.metric("NPS", f"{nps_score(filtered.get('recomendacion',pd.Series(dtype=float))):+.0f}")
        c1,c2 = st.columns([1.1,1])
        with c1:
            counts=filtered['comparsa'].value_counts().reindex(COMPARSAS,fill_value=0).reset_index(); counts.columns=['Comparsa','Respuestas']
            fig=px.bar(counts,x='Respuestas',y='Comparsa',orientation='h',title='Participación por comparsa'); fig.update_layout(height=420,margin=dict(t=55,b=20,l=20,r=20)); st.plotly_chart(fig,use_container_width=True)
        with c2:
            acts=acts_summary(filtered).sort_values('Valoración media',ascending=False).head(12)
            fig=px.bar(acts,x='Acto',y='Valoración media',range_y=[0,5],title='Valoración media por acto'); fig.update_layout(height=420,xaxis_tickangle=-35,margin=dict(t=55,b=120,l=20,r=20)); st.plotly_chart(fig,use_container_width=True)
        c3,c4,c5 = st.columns(3)
        with c3: st.plotly_chart(donut_chart(filtered,'pulsera_usada','Pulsera festera'),use_container_width=True)
        with c4: st.plotly_chart(donut_chart(filtered,'pasacalles_preferencia','Pasacalles festero'),use_container_width=True)
        with c5: st.plotly_chart(donut_chart(filtered,'media_fiesta_preferencia','Media Fiesta 2027'),use_container_width=True)
        st.markdown("### Lectura rápida")
        for pt in interpretation_points(filtered, invited): st.markdown(f"- {pt}")

    elif section == "Comparsas":
        rows=[]
        for comp in COMPARSAS:
            sub=df[df['comparsa']==comp]
            inv=int(invited.get(comp,0)); resp=len(sub)
            avgv=pd.to_numeric(sub.get('valoracion_general'),errors='coerce').mean() if resp else np.nan
            recv=pd.to_numeric(sub.get('recomendacion'),errors='coerce').mean() if resp else np.nan
            rows.append({'Comparsa':comp,'Respuestas':resp,'% Participación':resp/inv*100 if inv else np.nan,'Valoración general':avgv,'Recomendación':recv,'Uso pulsera %':safe_pct(sub.get('pulsera_usada',pd.Series(dtype=float))) if resp else np.nan,'Apoyo día 7 %':(sub.get('pasacalles_preferencia',pd.Series(dtype=str))=='Prefiero que pase a celebrarse el día 7').mean()*100 if resp else np.nan,'Media Fiesta 2 días %':(sub.get('media_fiesta_preferencia',pd.Series(dtype=str))=='Sí, me parece una buena propuesta').mean()*100 if resp else np.nan})
        compdf=pd.DataFrame(rows)
        st.dataframe(compdf.round(2),use_container_width=True,hide_index=True)
        a,b=st.columns(2)
        with a: st.plotly_chart(px.bar(compdf,x='Comparsa',y='Valoración general',range_y=[0,5],title='Valoración general por comparsa'),use_container_width=True)
        with b: st.plotly_chart(px.bar(compdf,x='Comparsa',y='% Participación',range_y=[0,100],title='Participación por comparsa (%)'),use_container_width=True)
        with st.expander("Configurar número de festeros invitados por comparsa"):
            new_counts={}; cols=st.columns(2)
            for i,c in enumerate(COMPARSAS):
                with cols[i%2]: new_counts[c]=st.number_input(c,min_value=0,max_value=10000,value=int(invited.get(c,0)),step=1,key=f'inv_{i}')
            if st.button("Guardar configuración",type="primary"):
                ok,msg=save_invited_counts(new_counts); (st.success if ok else st.error)(msg)

    elif section == "Actos":
        acts=acts_summary(filtered).sort_values('Valoración media',ascending=False)
        rank=ranking_summary(filtered)
        a,b=st.columns(2)
        with a:
            fig=px.bar(acts.sort_values('Valoración media'),x='Valoración media',y='Acto',orientation='h',range_x=[0,5],title='Ranking por valoración media'); fig.update_layout(height=560); st.plotly_chart(fig,use_container_width=True)
        with b:
            if not rank.empty:
                fig=px.bar(rank.sort_values('Posición media',ascending=False),x='Posición media',y='Acto',orientation='h',title='Ordenación de preferencia (menor posición = mejor)'); fig.update_layout(height=560); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(acts,use_container_width=True,hide_index=True)
        if not rank.empty:
            st.markdown("### Resultado de la pregunta de ordenación")
            st.dataframe(rank,use_container_width=True,hide_index=True)

    elif section == "Pulsera festera":
        a,b=st.columns(2)
        with a: st.plotly_chart(donut_chart(filtered,'pulsera_usada','¿Utilizó la pulsera?'),use_container_width=True)
        used=filtered[filtered.get('pulsera_usada',False)==True]
        with b:
            if not used.empty and 'pulsera_utilidad' in used: st.plotly_chart(donut_chart(used,'pulsera_utilidad','Utilidad percibida'),use_container_width=True)
        val=pd.to_numeric(used.get('pulsera_valoracion'),errors='coerce').mean() if not used.empty else np.nan
        st.metric("Valoración media de la pulsera", "—" if pd.isna(val) else f"{val:.2f} / 5")

    elif section == "Pasacalles festero":
        st.plotly_chart(donut_chart(filtered,'pasacalles_preferencia','Preferencia sobre el día del Pasacalles Festero'),use_container_width=True)
        vals=filtered.get('pasacalles_motivo',pd.Series(dtype=str)).fillna('').astype(str).str.strip(); vals=vals[vals!='']
        st.markdown(f"### Motivos escritos ({len(vals)})")
        for text in vals.head(200): st.markdown(f"- {text}")

    elif section == "Media Fiesta 2027":
        st.plotly_chart(donut_chart(filtered,'media_fiesta_preferencia','Media Fiesta 2027 en dos días'),use_container_width=True)
        vals=filtered.get('media_fiesta_comentarios',pd.Series(dtype=str)).fillna('').astype(str).str.strip(); vals=vals[vals!='']
        st.markdown(f"### Comentarios ({len(vals)})")
        for text in vals.head(200): st.markdown(f"- {text}")

    elif section == "Comentarios y sugerencias":
        fields={'acto_destaca_por_que':'Por qué destacan un acto','acto_mejorar_que_cambiarias':'Qué cambiarían de los actos','pulsera_mejoras':'Mejoras de la pulsera','pasacalles_motivo':'Motivos sobre el Pasacalles','media_fiesta_comentarios':'Media Fiesta 2027','mejoras_2027':'Mejoras para 2027','comentario_final':'Otros comentarios'}
        for field,title in fields.items():
            vals=filtered.get(field,pd.Series(dtype=str)).fillna('').astype(str).str.strip(); vals=vals[vals!='']
            with st.expander(f"{title} · {len(vals)}"):
                for text in vals.head(300): st.markdown(f"- {text}")

    elif section == "Informes":
        st.markdown("### Generar informes para la Junta Directiva")
        scope=st.selectbox("Ámbito del informe",["TOTAL"]+COMPARSAS)
        report_df=df if scope=="TOTAL" else df[df['comparsa']==scope]
        if len(report_df)<min_group:
            st.warning("No se genera un informe detallado con menos de 5 respuestas, para proteger la privacidad.")
        else:
            for pt in interpretation_points(report_df,invited): st.markdown(f"- {pt}")
            csv=report_df.drop(columns=['id'],errors='ignore').to_csv(index=False).encode('utf-8-sig')
            excel=report_excel_bytes(report_df,invited)
            pdf=report_pdf_bytes(report_df,"Todas las comparsas" if scope=='TOTAL' else scope,invited)
            d1,d2,d3=st.columns(3)
            d1.download_button("Descargar CSV",csv,file_name=f"resultados_{scope.lower().replace(' ','_')}.csv",mime='text/csv',use_container_width=True)
            d2.download_button("Descargar Excel",excel,file_name=f"informe_{scope.lower().replace(' ','_')}.xlsx",mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
            d3.download_button("Descargar PDF",pdf,file_name=f"informe_{scope.lower().replace(' ','_')}.pdf",mime='application/pdf',use_container_width=True)
            st.caption("Los informes no incluyen nombre, DNI, email ni teléfono porque la encuesta no solicita esos datos.")

    elif section == "Gestionar encuestas":
        st.markdown("### Borrar encuestas registradas")
        st.warning("El borrado es permanente. Utiliza esta sección solo para eliminar respuestas duplicadas, pruebas o encuestas que deban excluirse.")
        manage = df.copy()
        manage["created_at"] = pd.to_datetime(manage.get("created_at"), errors="coerce")
        manage["Fecha"] = manage["created_at"].dt.strftime("%d/%m/%Y %H:%M").fillna("")
        manage["Etiqueta"] = manage.apply(lambda r: f"{r['Fecha']} · {r.get('comparsa','')} · {r.get('edad','')} · ID {str(r.get('id',''))[:8]}", axis=1)
        labels = manage["Etiqueta"].tolist()
        selected_labels = st.multiselect("Selecciona las encuestas que quieres borrar", labels, placeholder="Puedes seleccionar una o varias")
        selected_ids = manage.loc[manage["Etiqueta"].isin(selected_labels), "id"].astype(str).tolist()
        st.dataframe(manage[["Fecha","comparsa","edad","antiguedad","cargo"]].rename(columns={"comparsa":"Comparsa","edad":"Edad","antiguedad":"Antigüedad","cargo":"Cargo"}), use_container_width=True, hide_index=True)
        col_del, col_all = st.columns(2)
        with col_del:
            if st.button("Borrar seleccionadas", type="primary", use_container_width=True, disabled=not selected_ids):
                ok, msg = delete_responses(selected_ids)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        with col_all:
            st.markdown("**Vaciar todas las respuestas**")
            confirmation = st.text_input('Para borrar todas, escribe exactamente: BORRAR TODAS', key='delete_all_confirmation')
            if st.button("Borrar TODAS las encuestas", use_container_width=True, disabled=confirmation != "BORRAR TODAS"):
                ok, msg = delete_all_responses()
                (st.success if ok else st.error)(msg)
                if ok:
                    st.session_state.pop('delete_all_confirmation', None)
                    st.rerun()

    elif section == "Cómo interpretar":
        st.markdown("### Guía para interpretar correctamente la encuesta")
        st.info("Este apartado sirve como ayuda a la Junta Directiva. Los resultados deben leerse en conjunto y no basarse en un único gráfico.")
        st.markdown("**Valoración general (1–5).** Una media superior a 4 indica una percepción claramente positiva. Entre 3 y 4 hay satisfacción moderada con margen de mejora. Por debajo de 3 conviene revisar el área en detalle.")
        st.markdown("**Recomendación y NPS.** Las puntuaciones 9–10 son promotores, 7–8 pasivos y 0–6 detractores. El NPS se obtiene restando el porcentaje de detractores al de promotores.")
        st.markdown("**Actos.** Conviene cruzar tres datos: valoración media, número de personas que lo han valorado y su posición en la pregunta de ordenación. Un acto con alta nota pero poca participación debe interpretarse con cautela.")
        st.markdown("**Comparsas.** Las diferencias entre comparsas pueden revelar necesidades distintas. No deben utilizarse para establecer juicios sobre una comparsa, sino para detectar patrones y adaptar decisiones.")
        st.markdown("**Comentarios abiertos.** Sirven para explicar el porqué de los porcentajes. Busca temas repetidos, no comentarios aislados.")
        st.markdown("**Privacidad.** El panel oculta el detalle cuando un filtro deja menos de 5 respuestas. Los informes son agregados y no incluyen datos identificativos directos.")
        st.markdown("### Lectura automática de los datos actuales")
        for pt in interpretation_points(filtered,invited): st.markdown(f"- {pt}")

# =============================================================
# ROUTER
# =============================================================

view = st.query_params.get("view", "encuesta")
if view == "admin":
    render_admin()
else:
    render_survey()
