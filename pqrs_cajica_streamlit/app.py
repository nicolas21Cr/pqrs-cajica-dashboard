import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# =============================
# CONFIGURACIÓN GENERAL
# =============================
APP_TITLE = "Dashboard PQRS - Alcaldía de Cajicá"
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "base_pqrs_cajica_prueba_streamlit.xlsx"
DB_FILE = BASE_DIR / "data" / "pqrs_cajica.sqlite"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# ESTILOS
# =============================
st.markdown(
    """
    <style>
    .main {background-color: #F7FAF7;}
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {
        background: linear-gradient(135deg, #0B3D2E 0%, #2E7D32 55%, #8BC34A 100%);
        color: white;
        padding: 1.7rem 2rem;
        border-radius: 22px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    .hero h1 {margin: 0; font-size: 2.1rem;}
    .hero p {font-size: 1.05rem; margin-top: .5rem; opacity: .95;}
    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 5px 18px rgba(0,0,0,0.08);
        border-left: 7px solid #2E7D32;
        min-height: 112px;
    }
    .metric-card.red {border-left-color: #C62828;}
    .metric-card.orange {border-left-color: #EF6C00;}
    .metric-card.blue {border-left-color: #1565C0;}
    .metric-card.gray {border-left-color: #546E7A;}
    .metric-label {font-size: .92rem; color: #4b5563; margin-bottom: .3rem;}
    .metric-value {font-size: 2rem; font-weight: 800; color: #111827;}
    .metric-help {font-size: .83rem; color: #6b7280; margin-top: .2rem;}
    .info-box {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stDataFrame"] {background: white; border-radius: 16px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# USUARIOS DE PRUEBA
# =============================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

USERS = {
    "admin@cajica.gov.co": {
        "password": hash_password("Admin123*"),
        "name": "Administrador General",
        "role": "ADMIN",
        "secretaria": "TODAS",
    },
    "gobierno@cajica.gov.co": {
        "password": hash_password("Gobierno123*"),
        "name": "Secretaría de Gobierno",
        "role": "SECRETARIA",
        "secretaria": "SECRETARÍA DE GOBIERNO",
    },
    "hacienda@cajica.gov.co": {
        "password": hash_password("Hacienda123*"),
        "name": "Secretaría de Hacienda",
        "role": "SECRETARIA",
        "secretaria": "SECRETARÍA DE HACIENDA",
    },
    "planeacion@cajica.gov.co": {
        "password": hash_password("Planeacion123*"),
        "name": "Secretaría de Planeación",
        "role": "SECRETARIA",
        "secretaria": "SECRETARÍA DE PLANEACIÓN",
    },
    "infraestructura@cajica.gov.co": {
        "password": hash_password("Infra123*"),
        "name": "Secretaría de Infraestructura",
        "role": "SECRETARIA",
        "secretaria": "SECRETARÍA DE INFRAESTRUCTURA",
    },
    "juridica@cajica.gov.co": {
        "password": hash_password("Juridica123*"),
        "name": "Secretaría Jurídica",
        "role": "SECRETARIA",
        "secretaria": "SECRETARÍA JURÍDICA",
    },
}

# =============================
# BASE DE DATOS
# =============================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper().replace(" ", "_") for c in df.columns]
    rename_map = {
        "TIPO_DE_PQRS": "TIPO_PQRS",
        "FECHA": "FECHA_ENVIO",
        "SEC.": "SECRETARIA",
        "CONCEPTO_DE_VERIFICACION": "CONCEPTO_VERIFICACION",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if "TIPO_DE_PQRS" in df.columns:
        df = df.rename(columns={"TIPO_DE_PQRS": "TIPO_PQRS"})
    if "TIPO_PQRS" not in df.columns and "TIPO_DE_PQRS" in df.columns:
        df["TIPO_PQRS"] = df["TIPO_DE_PQRS"]
    if "RADICADO" not in df.columns:
        df["RADICADO"] = "CAJ-PQRS-" + df.index.astype(str).str.zfill(5)
    if "OBSERVACION" not in df.columns:
        df["OBSERVACION"] = ""
    if "ESTADO" not in df.columns:
        df["ESTADO"] = df["NIVEL_CUMPLIMIENTO"].apply(lambda x: "Respondido" if str(x).upper() == "CUMPLIMIENTO" else "Pendiente")
    if "FECHA_LIMITE" not in df.columns:
        if "FECHA_ENVIO" in df.columns:
            df["FECHA_LIMITE"] = pd.to_datetime(df["FECHA_ENVIO"], errors="coerce") + pd.to_timedelta(15, unit="D")
        else:
            df["FECHA_LIMITE"] = pd.NaT
    return df


def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pqrs (
            RADICADO TEXT PRIMARY KEY,
            CODIGO TEXT,
            FECHA_ENVIO TEXT,
            FECHA_PUBLICACION TEXT,
            FECHA_LIMITE TEXT,
            CANAL TEXT,
            TIPO_PQRS TEXT,
            SECRETARIA TEXT,
            CONCEPTO_VERIFICACION TEXT,
            NIVEL_CUMPLIMIENTO TEXT,
            MES TEXT,
            DIAS_GESTION REAL,
            RESPONSABLE TEXT,
            TEMA TEXT,
            PRIORIDAD TEXT,
            ESTADO TEXT,
            OBSERVACION TEXT
        )
        """
    )
    existing = cur.execute("SELECT COUNT(*) FROM pqrs").fetchone()[0]
    if existing == 0:
        df = pd.read_excel(DATA_FILE, sheet_name=0)
        df = normalize_columns(df)
        required = [
            "RADICADO", "CODIGO", "FECHA_ENVIO", "FECHA_PUBLICACION", "FECHA_LIMITE", "CANAL",
            "TIPO_PQRS", "SECRETARIA", "CONCEPTO_VERIFICACION", "NIVEL_CUMPLIMIENTO", "MES",
            "DIAS_GESTION", "RESPONSABLE", "TEMA", "PRIORIDAD", "ESTADO", "OBSERVACION"
        ]
        for col in required:
            if col not in df.columns:
                df[col] = None
        df = df[required]
        for col in ["FECHA_ENVIO", "FECHA_PUBLICACION", "FECHA_LIMITE"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
df = df.where(pd.notnull(df), None)

cur.executemany(
    """
    INSERT OR REPLACE INTO pqrs (
        RADICADO, CODIGO, FECHA_ENVIO, FECHA_PUBLICACION, FECHA_LIMITE,
        CANAL, TIPO_PQRS, SECRETARIA, CONCEPTO_VERIFICACION,
        NIVEL_CUMPLIMIENTO, MES, DIAS_GESTION, RESPONSABLE, TEMA,
        PRIORIDAD, ESTADO, OBSERVACION
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    df.values.tolist()
)

conn.commit()
   
conn.close()


def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM pqrs", conn)
    conn.close()
    for col in ["FECHA_ENVIO", "FECHA_PUBLICACION", "FECHA_LIMITE"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def update_observations(rows: pd.DataFrame):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for _, row in rows.iterrows():
        cur.execute(
            "UPDATE pqrs SET OBSERVACION = ? WHERE RADICADO = ?",
            (str(row.get("OBSERVACION", "")), str(row["RADICADO"])),
        )
    conn.commit()
    conn.close()

# =============================
# AUTENTICACIÓN
# =============================
def login_page():
    st.markdown(
        """
        <div class="hero">
            <h1>🏛️ Dashboard PQRS - Alcaldía de Cajicá</h1>
            <p>Ingrese con su usuario institucional para consultar únicamente la información autorizada.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.subheader("Inicio de sesión")
        email = st.text_input("Correo institucional", placeholder="usuario@cajica.gov.co")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", use_container_width=True):
            user = USERS.get(email.lower().strip())
            if user and user["password"] == hash_password(password):
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                st.session_state["email"] = email.lower().strip()
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        with st.expander("Usuarios de prueba"):
            st.write("Admin: admin@cajica.gov.co / Admin123*")
            st.write("Planeación: planeacion@cajica.gov.co / Planeacion123*")
            st.write("Gobierno: gobierno@cajica.gov.co / Gobierno123*")


def require_login():
    if not st.session_state.get("authenticated"):
        login_page()
        st.stop()

# =============================
# COMPONENTES VISUALES
# =============================
def metric_card(label, value, help_text, css_class=""):
    st.markdown(
        f"""
        <div class="metric-card {css_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_filtered_by_user(df: pd.DataFrame) -> pd.DataFrame:
    user = st.session_state["user"]
    if user["role"] == "ADMIN":
        return df.copy()
    return df[df["SECRETARIA"].astype(str).str.upper() == user["secretaria"].upper()].copy()


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")
    user = st.session_state["user"]
    st.sidebar.info(f"Acceso: {user['name']}\n\nRol: {user['role']}")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    filtered = df.copy()
    if user["role"] == "ADMIN":
        secretarias = sorted(filtered["SECRETARIA"].dropna().unique())
        selected_secretaria = st.sidebar.multiselect("Secretaría", secretarias, default=secretarias)
        filtered = filtered[filtered["SECRETARIA"].isin(selected_secretaria)]
    else:
        st.sidebar.success(f"Filtro automático: {user['secretaria']}")

    estados = sorted(filtered["ESTADO"].dropna().unique())
    selected_estados = st.sidebar.multiselect("Estado", estados, default=estados)
    if selected_estados:
        filtered = filtered[filtered["ESTADO"].isin(selected_estados)]

    tipos = sorted(filtered["TIPO_PQRS"].dropna().unique())
    selected_tipos = st.sidebar.multiselect("Tipo de PQRS", tipos, default=tipos)
    if selected_tipos:
        filtered = filtered[filtered["TIPO_PQRS"].isin(selected_tipos)]

    prioridades = sorted(filtered["PRIORIDAD"].dropna().unique())
    selected_prioridades = st.sidebar.multiselect("Prioridad", prioridades, default=prioridades)
    if selected_prioridades:
        filtered = filtered[filtered["PRIORIDAD"].isin(selected_prioridades)]

    return filtered

# =============================
# APP PRINCIPAL
# =============================
init_db()
require_login()

all_data = load_data()
user_data = get_filtered_by_user(all_data)
df = apply_sidebar_filters(user_data)

st.markdown(
    """
    <div class="hero">
        <h1>🏛️ Control y seguimiento de PQRS</h1>
        <p>Panel institucional para identificar vencimientos, pendientes, cumplimiento y observaciones por secretaría.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Cálculos
today = pd.Timestamp(datetime.today().date())
df["DIAS_PARA_VENCER"] = (df["FECHA_LIMITE"] - today).dt.days
vencidas = df[(df["DIAS_PARA_VENCER"] < 0) & (~df["ESTADO"].str.upper().isin(["RESPONDIDO", "CERRADO"]))].shape[0]
pendientes = df[df["ESTADO"].str.upper().isin(["PENDIENTE", "EN TRÁMITE", "EN TRAMITE"])].shape[0]
respondidas = df[df["ESTADO"].str.upper().isin(["RESPONDIDO", "CERRADO"])].shape[0]
proximas = df[(df["DIAS_PARA_VENCER"] >= 0) & (df["DIAS_PARA_VENCER"] <= 5) & (~df["ESTADO"].str.upper().isin(["RESPONDIDO", "CERRADO"]))].shape[0]
total = len(df)
cumplimiento = round((respondidas / total) * 100, 1) if total else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    metric_card("PQRS vencidas", vencidas, "Requieren atención inmediata", "red")
with c2:
    metric_card("PQRS pendientes", pendientes, "Casos sin cierre definitivo", "orange")
with c3:
    metric_card("Próximas a vencer", proximas, "Vencen en 5 días o menos", "blue")
with c4:
    metric_card("Respondidas", respondidas, "Casos gestionados", "")
with c5:
    metric_card("Cumplimiento", f"{cumplimiento}%", "Según PQRS respondidas", "gray")

st.markdown("---")
st.markdown("### Resumen visual")

col_a, col_b = st.columns(2)
with col_a:
    if not df.empty:
        estado_df = df.groupby("ESTADO", dropna=False).size().reset_index(name="Cantidad")
        fig = px.bar(estado_df, x="ESTADO", y="Cantidad", text="Cantidad", title="PQRS por estado")
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)
with col_b:
    if not df.empty:
        tipo_df = df.groupby("TIPO_PQRS", dropna=False).size().reset_index(name="Cantidad")
        fig = px.pie(tipo_df, names="TIPO_PQRS", values="Cantidad", title="Distribución por tipo de PQRS", hole=.45)
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

if st.session_state["user"]["role"] == "ADMIN":
    st.markdown("### Comparativo por secretaría")
    sec_df = df.groupby(["SECRETARIA", "ESTADO"], dropna=False).size().reset_index(name="Cantidad")
    fig = px.bar(sec_df, x="SECRETARIA", y="Cantidad", color="ESTADO", title="PQRS por secretaría y estado")
    fig.update_layout(height=440, xaxis_tickangle=-35, margin=dict(l=20, r=20, t=60, b=120))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### Detalle de PQRS")
st.markdown(
    """
    <div class="info-box">
    Consulte los registros filtrados. La columna <b>OBSERVACION</b> puede editarse para registrar novedades como: falta documento soporte, pendiente respuesta jurídica, en revisión del área encargada, etc.
    </div>
    """,
    unsafe_allow_html=True,
)

search = st.text_input("Buscar por radicado, responsable, tema u observación")
view_df = df.copy()
if search:
    s = search.upper()
    mask = (
        view_df["RADICADO"].astype(str).str.upper().str.contains(s, na=False)
        | view_df["RESPONSABLE"].astype(str).str.upper().str.contains(s, na=False)
        | view_df["TEMA"].astype(str).str.upper().str.contains(s, na=False)
        | view_df["OBSERVACION"].astype(str).str.upper().str.contains(s, na=False)
    )
    view_df = view_df[mask]

cols_to_show = [
    "RADICADO", "FECHA_ENVIO", "FECHA_PUBLICACION", "FECHA_LIMITE", "SECRETARIA",
    "TIPO_PQRS", "CANAL", "ESTADO", "NIVEL_CUMPLIMIENTO", "PRIORIDAD",
    "RESPONSABLE", "TEMA", "DIAS_PARA_VENCER", "OBSERVACION"
]
view_df = view_df[[c for c in cols_to_show if c in view_df.columns]].sort_values("FECHA_ENVIO", ascending=False)

edited_df = st.data_editor(
    view_df,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    disabled=[c for c in view_df.columns if c != "OBSERVACION"],
    column_config={
        "OBSERVACION": st.column_config.TextColumn("Observación", width="large"),
        "DIAS_PARA_VENCER": st.column_config.NumberColumn("Días para vencer", format="%d"),
    },
)

col_save, col_download = st.columns([1, 1])
with col_save:
    if st.button("Guardar observaciones", type="primary", use_container_width=True):
        update_observations(edited_df[["RADICADO", "OBSERVACION"]])
        st.success("Observaciones guardadas correctamente.")
        st.cache_data.clear()
with col_download:
    export_df = edited_df.copy()
    csv = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar reporte filtrado CSV",
        data=csv,
        file_name="reporte_pqrs_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption("Versión de prueba. Para producción se recomienda autenticación institucional y base de datos PostgreSQL/Cloud SQL.")
