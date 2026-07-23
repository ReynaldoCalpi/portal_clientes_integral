from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Portal de Gestión de Compras - Soportec",
    page_icon="📄",
    layout="wide",
)

# Directorio base para almacenamiento local organizado
BASE_DIR = Path("data_compras")
BASE_DIR.mkdir(exist_ok=True)

# Base de datos simulada de usuarios (Credenciales y Roles)
USERS = {
    "admin": {
        "password": "adminpassword123",
        "role": "admin",
        "name": "Administrador General",
    },
    "cliente1": {
        "password": "clientepass123",
        "role": "client",
        "name": "Comercial El Sol S.A.",
    },
    "cliente2": {
        "password": "clientepass123",
        "role": "client",
        "name": "Inversiones del Norte",
    },
}

# ==========================================
# GESTIÓN DE SESIÓN
# ==========================================
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "name" not in st.session_state:
        st.session_state.name = None

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None
    st.rerun()

# ==========================================
# VISTA DE LOGIN
# ==========================================
def login_form():
    st.markdown(
        """
        <div style="text-align: center; padding: 20px;">
            <h2>Portal de Gestión de Compras y Facturación</h2>
            <p style="color: gray;">Soportec Costa Rica - Plataforma Centralizada</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            username_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit_button = st.form_submit_button("Ingresar")

            if submit_button:
                if (
                    username_input in USERS
                    and USERS[username_input]["password"] == password_input
                ):
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.session_state.role = USERS[username_input]["role"]
                    st.session_state.name = USERS[username_input]["name"]
                    st.success("¡Bienvenido al sistema!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        st.info(
            "**Credenciales de prueba disponibles:**\n\n"
            "- **Admin:** `admin` / `adminpassword123`\n"
            "- **Cliente 1:** `cliente1` / `clientepass123`\n"
            "- **Cliente 2:** `cliente2` / `clientepass123`"
        )

# ==========================================
# VISTA DE CLIENTES
# ==========================================
def render_client_view():
    st.title(f"Panel de Cliente: {st.session_state.name}")
    st.markdown(
        "Suba sus comprobantes y archivos de compras (formatos **JSON** o **PDF**) de forma segura y centralizada."
    )

    # Crear carpeta específica del cliente si no existe
    client_dir = BASE_DIR / st.session_state.username
    client_dir.mkdir(exist_ok=True)

    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Seleccione o arrastre sus archivos de compras",
            type=["json", "pdf"],
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("Subir Archivos")

        if submitted:
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    if file_ext in ["json", "pdf"]:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"archivo_{timestamp}.{file_ext}"
                        file_path = client_dir / filename

                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        st.success(f"Archivo guardado exitosamente: {uploaded_file.name}")
                    else:
                        st.warning(f"Archivo rechazado por extensión no permitida: {uploaded_file.name}")
            else:
                st.warning("Por favor, seleccione al menos un archivo para subir.")

    st.markdown("---")
    st.subheader("Historial de Archivos Enviados")

    files = list(client_dir.glob("*.*"))
    if files:
        file_data = []
        for file in sorted(files, key=os.path.getmtime, reverse=True):
            file_stats = file.stat()
            file_data.append({
                "Nombre del Sistema": file.name,
                "Tipo": file.suffix.upper()[1:],
                "Fecha de Subida": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "Tamaño (KB)": round(file_stats.st_size / 1024, 2),
            })

        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no ha subido ningún archivo.")

# ==========================================
# VISTA DE ADMINISTRADOR
# ==========================================
def render_admin_view():
    st.title("Panel de Administración - Gestión Centralizada")
    st.markdown(
        "Supervise, filtre y descargue los comprobantes cargados por todos los clientes del sistema de manera organizada."
    )

    # Recopilar todos los archivos de todas las carpetas de clientes
    all_files = []
    client_dirs = [d for d in BASE_DIR.iterdir() if d.is_dir()]

    for client_dir in client_dirs:
        client_name = client_dir.name
        for file in client_dir.glob("*.*"):
            file_stats = file.stat()
            all_files.append({
                "Cliente": client_name,
                "Nombre de Archivo": file.name,
                "Tipo": file.suffix.upper()[1:],
                "Fecha de Subida": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "Tamaño (KB)": round(file_stats.st_size / 1024, 2),
                "Ruta Completa": file,
            })

    if not all_files:
        st.info("No hay archivos registrados en el sistema actualmente.")
        return

    df_all = pd.DataFrame(all_files)

    # Panel de métricas clave (KPIs)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Archivos", len(df_all))
    with col2:
        st.metric("Clientes Activos con Envíos", df_all["Cliente"].nunique())
    with col3:
        json_count = len(df_all[df_all["Tipo"] == "JSON"])
        pdf_count = len(df_all[df_all["Tipo"] == "PDF"])
        st.metric("JSONs / PDFs", f"{json_count} / {pdf_count}")

    st.markdown("---")
    st.subheader("Filtros y Búsqueda Avanzada")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_client = st.selectbox(
            "Filtrar por Cliente", ["Todos"] + list(df_all["Cliente"].unique())
        )
    with col_f2:
        selected_type = st.selectbox(
            "Filtrar por Tipo de Archivo", ["Todos", "JSON", "PDF"]
        )

    # Aplicar filtros
    df_filtered = df_all.copy()
    if selected_client != "Todos":
        df_filtered = df_filtered[df_filtered["Cliente"] == selected_client]
    if selected_type != "Todos":
        df_filtered = df_filtered[df_filtered["Tipo"] == selected_type]

    st.markdown(f"Mostrando **{len(df_filtered)}** registros encontrados.")

    # Tabla interactiva con opciones de gestión y descarga
    for idx, row in df_filtered.iterrows():
        with st.expander(
            f"📁 [{row['Tipo']}] Cliente: {row['Cliente']} | Archivo: {row['Nombre de Archivo']} ({row['Fecha de Subida']})"
        ):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**Ruta:** `{row['Ruta Completa']}`")
                st.write(f"**Tamaño:** {row['Tamaño (KB)']} KB")
                st.write(f"**Fecha y Hora:** {row['Fecha de Subida']}")
            with col_b:
                with open(row["Ruta Completa"], "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label="📥 Descargar Archivo",
                    data=file_bytes,
                    file_name=row["Nombre de Archivo"],
                    mime="application/json" if row["Tipo"] == "JSON" else "application/pdf",
                    key=f"download_{row['Cliente']}_{row['Nombre de Archivo']}_{idx}",
                )

# ==========================================
# CONTROLADOR PRINCIPAL
# ==========================================
def main():
    init_session_state()

    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown(f"### Sesión Activa")
            st.markdown(f"**{st.session_state.name}**")
            st.markdown(f"Rol: `{st.session_state.role.upper()}`")
            st.markdown("---")
            if st.button("Cerrar Sesión", type="primary"):
                logout()

        # Enrutar según el rol validado
        if st.session_state.role == "client":
            render_client_view()
        elif st.session_state.role == "admin":
            render_admin_view()
    else:
        login_form()

if __name__ == "__main__":
    main()