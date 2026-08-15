import streamlit as st
from PIL import Image
import pandas as pd
from datetime import datetime

# Importar utilidades propias
from utils.ocr import process_meter_image, extract_total_amount_from_bill
from utils.calculations import calculate_bill, generate_report
from utils.storage import get_or_create_sheet, save_reading, get_last_readings, get_history

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="⚡ Gestión de Electricidad",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ESTILOS CSS PARA MÓVIL
# ============================================
st.markdown("""
<style>
    .main > div { padding: 0.5rem 1rem; }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 10px;
        background-color: #2E86AB;
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background-color: #1a6a8a;
    }
    .report-box {
        background-color: #f0f7fa;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #2E86AB;
        margin: 1rem 0;
        font-family: monospace;
        white-space: pre-wrap;
        font-size: 0.95rem;
    }
    @media (max-width: 600px) {
        .report-box { font-size: 0.8rem; padding: 1rem; }
        .stApp { padding: 0.2rem; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INICIALIZACIÓN DEL ESTADO DE SESIÓN
# ============================================
if 'readings' not in st.session_state:
    st.session_state.readings = {
        'f_previous': 0, 'f_current': None,
        'g_previous': 0, 'g_current': None,
        'general_previous': 0, 'general_current': None,
        'total_bill': None
    }
if 'result' not in st.session_state:
    st.session_state.result = None

# ============================================
# CONEXIÓN A GOOGLE SHEETS (cacheada)
# ============================================
@st.cache_resource
def init_gsheet():
    return get_or_create_sheet()

worksheet = init_gsheet()

# ============================================
# BARRA LATERAL DE NAVEGACIÓN
# ============================================
st.sidebar.title("⚡ Navegación")
page = st.sidebar.radio(
    "Ir a:",
    ["📝 Nueva Lectura", "📜 Historial", "⚙️ Configuración"]
)

# ============================================
# PÁGINA: NUEVA LECTURA
# ============================================
if page == "📝 Nueva Lectura":
    st.title("📝 Nueva Lectura de Medidores")
    st.markdown("Sube las fotos de los medidores y la boleta, o ingresa los valores manualmente.")
    
    # Cargar la última lectura desde Google Sheets
    if worksheet and st.session_state.readings['f_previous'] == 0:
        last = get_last_readings(worksheet)
        if last:
            st.session_state.readings['f_previous'] = last.get('f_current', 0)
            st.session_state.readings['g_previous'] = last.get('g_current', 0)
            st.session_state.readings['general_previous'] = last.get('general_current', 0)
            st.info(f"📌 Cargada lectura anterior: F={st.session_state.readings['f_previous']}, G={st.session_state.readings['g_previous']}")
    
    # --- DEPARTAMENTO F ---
    with st.expander("📸 Departamento F - Medidor", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Lectura anterior:**")
            f_prev = st.number_input(
                "F anterior",
                value=st.session_state.readings['f_previous'],
                step=1,
                key="f_prev_input",
                label_visibility="collapsed"
            )
            st.session_state.readings['f_previous'] = f_prev
            
            st.write("**📷 Sube foto del medidor F:**")
            f_image = st.file_uploader(
                "Foto medidor F",
                type=["jpg", "jpeg", "png"],
                key="f_image",
                label_visibility="collapsed"
            )
            f_current = None
            if f_image:
                try:
                    image = Image.open(f_image)
                    st.image(image, caption="Medidor F", use_container_width=True)
                    with st.spinner("🔍 Reconociendo lectura..."):
                        f_current = process_meter_image(f_image)
                    if f_current:
                        st.success(f"📊 Lectura detectada: **{f_current}**")
                    else:
                        st.warning("No se detectaron números. Ingresa manualmente.")
                except Exception as e:
                    st.error(f"Error al procesar la imagen: {e}")
        
        with col2:
            st.write("**Lectura actual (ingresa si OCR falla):**")
            f_current_manual = st.number_input(
                "F actual",
                value=f_current if f_current is not None else 0,
                step=1,
                key="f_current_input",
                label_visibility="collapsed"
            )
            if f_current is not None:
                st.session_state.readings['f_current'] = f_current_manual if f_current_manual > 0 else f_current
            else:
                st.session_state.readings['f_current'] = f_current_manual
    
    # --- DEPARTAMENTO G ---
    with st.expander("📸 Departamento G - Medidor", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Lectura anterior:**")
            g_prev = st.number_input(
                "G anterior",
                value=st.session_state.readings['g_previous'],
                step=1,
                key="g_prev_input",
                label_visibility="collapsed"
            )
            st.session_state.readings['g_previous'] = g_prev
            
            st.write("**📷 Sube foto del medidor G:**")
            g_image = st.file_uploader(
                "Foto medidor G",
                type=["jpg", "jpeg", "png"],
                key="g_image",
                label_visibility="collapsed"
            )
            g_current = None
            if g_image:
                try:
                    image = Image.open(g_image)
                    st.image(image, caption="Medidor G", use_container_width=True)
                    with st.spinner("🔍 Reconociendo lectura..."):
                        g_current = process_meter_image(g_image)
                    if g_current:
                        st.success(f"📊 Lectura detectada: **{g_current}**")
                    else:
                        st.warning("No se detectaron números. Ingresa manualmente.")
                except Exception as e:
                    st.error(f"Error al procesar la imagen: {e}")
        
        with col2:
            st.write("**Lectura actual (ingresa si OCR falla):**")
            g_current_manual = st.number_input(
                "G actual",
                value=g_current if g_current is not None else 0,
                step=1,
                key="g_current_input",
                label_visibility="collapsed"
            )
            if g_current is not None:
                st.session_state.readings['g_current'] = g_current_manual if g_current_manual > 0 else g_current
            else:
                st.session_state.readings['g_current'] = g_current_manual
    
    # --- MEDIDOR GENERAL Y BOLETA ---
    with st.expander("📄 Medidor General y Boleta", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Medidor general - anterior:**")
            gen_prev = st.number_input(
                "General anterior",
                value=st.session_state.readings['general_previous'],
                step=1,
                key="gen_prev_input",
                label_visibility="collapsed"
            )
            st.session_state.readings['general_previous'] = gen_prev
            
            st.write("**Medidor general - actual:**")
            gen_current = st.number_input(
                "General actual",
                value=st.session_state.readings['general_current'] or 0,
                step=1,
                key="gen_current_input",
                label_visibility="collapsed"
            )
            st.session_state.readings['general_current'] = gen_current
        
        with col2:
            st.write("**📄 Sube la boleta de electricidad (PDF o imagen):**")
            bill_file = st.file_uploader(
                "Boleta",
                type=["pdf", "jpg", "jpeg", "png"],
                key="bill_file",
                label_visibility="collapsed"
            )
            if bill_file:
                if bill_file.type == "application/pdf":
                    st.info("📄 PDF cargado. Para extraer el monto, usa la opción manual o convierte a imagen.")
                else:
                    try:
                        image = Image.open(bill_file)
                        st.image(image, caption="Boleta", use_container_width=True)
                        with st.spinner("🔍 Extrayendo monto total..."):
                            total = extract_total_amount_from_bill(bill_file)
                        if total:
                            st.success(f"💰 Monto detectado: **${total:,.2f}**")
                            st.session_state.readings['total_bill'] = total
                        else:
                            st.warning("No se detectó el monto. Ingresa manualmente.")
                    except Exception as e:
                        st.error(f"Error al procesar la boleta: {e}")
            
            st.write("**💰 Monto total de la boleta (ingresa si OCR falla):**")
            total_bill = st.number_input(
                "Total boleta $",
                value=st.session_state.readings['total_bill'] or 0.0,
                step=0.01,
                format="%.2f",
                key="total_bill_input",
                label_visibility="collapsed"
            )
            st.session_state.readings['total_bill'] = total_bill
    
    # --- BOTÓN CALCULAR ---
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        calculate_btn = st.button("🧮 Calcular y Generar Informe", use_container_width=True)
    
    if calculate_btn:
        f_cur = st.session_state.readings['f_current']
        g_cur = st.session_state.readings['g_current']
        gen_cur = st.session_state.readings['general_current']
        total = st.session_state.readings['total_bill']
        
        # Validaciones
        if f_cur is None or f_cur == 0:
            st.error("❌ Ingresa la lectura del medidor F (actual).")
        elif g_cur is None or g_cur == 0:
            st.error("❌ Ingresa la lectura del medidor G (actual).")
        elif gen_cur is None or gen_cur == 0:
            st.error("❌ Ingresa la lectura del medidor general (actual).")
        elif total is None or total == 0:
            st.error("❌ Ingresa el monto total de la boleta.")
        else:
            # Cálculo
            result = calculate_bill(
                previous_reading_f=st.session_state.readings['f_previous'],
                current_reading_f=f_cur,
                previous_reading_g=st.session_state.readings['g_previous'],
                current_reading_g=g_cur,
                previous_general=st.session_state.readings['general_previous'],
                current_general=gen_cur,
                total_bill_amount=total
            )
            st.session_state.result = result
            
            # Generar informe
            report = generate_report(result, {
                'f_previous': st.session_state.readings['f_previous'],
                'f_current': f_cur,
                'g_previous': st.session_state.readings['g_previous'],
                'g_current': g_cur,
                'general_previous': st.session_state.readings['general_previous'],
                'general_current': gen_cur,
            })
            
            st.markdown("---")
            st.subheader("📋 Resultado")
            st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
            
            # Guardar en Google Sheets (si está conectado)
            if worksheet:
                saved = save_reading(
                    worksheet,
                    st.session_state.readings['f_previous'], f_cur,
                    st.session_state.readings['g_previous'], g_cur,
                    st.session_state.readings['general_previous'], gen_cur,
                    result['consumption_f'], result['consumption_g'], result['total_consumption'],
                    result['cost_f'], result['cost_g'], total,
                    notes=""
                )
                if saved:
                    st.success("✅ Guardado en Google Sheets")
                    # Actualizar valores anteriores para la próxima lectura
                    st.session_state.readings['f_previous'] = f_cur
                    st.session_state.readings['g_previous'] = g_cur
                    st.session_state.readings['general_previous'] = gen_cur
                    # Limpiar campos actuales
                    st.session_state.readings['f_current'] = None
                    st.session_state.readings['g_current'] = None
                    st.session_state.readings['general_current'] = None
                    st.session_state.readings['total_bill'] = None
                    st.rerun()

# ============================================
# PÁGINA: HISTORIAL
# ============================================
elif page == "📜 Historial":
    st.title("📜 Historial de Lecturas")
    
    if worksheet:
        df = get_history(worksheet, limit=30)
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
            
            # Resumen estadístico
            st.subheader("📊 Resumen")
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_f = df["Consumo F (kWh)"].mean() if "Consumo F (kWh)" in df.columns else 0
                st.metric("Promedio Consumo F", f"{avg_f:.1f} kWh")
            with col2:
                avg_g = df["Consumo G (kWh)"].mean() if "Consumo G (kWh)" in df.columns else 0
                st.metric("Promedio Consumo G", f"{avg_g:.1f} kWh")
            with col3:
                total_f = df["Costo F ($)"].sum() if "Costo F ($)" in df.columns else 0
                total_g = df["Costo G ($)"].sum() if "Costo G ($)" in df.columns else 0
                st.metric("Total Pagado (F+G)", f"${(total_f + total_g):,.2f}")
            
            # Botón para descargar CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Historial (CSV)",
                data=csv,
                file_name="historial_electricidad.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay registros aún. Realiza tu primera lectura.")
    else:
        st.warning("⚠️ No se pudo conectar a Google Sheets. Los datos no se guardarán.")

# ============================================
# PÁGINA: CONFIGURACIÓN
# ============================================
else:
    st.title("⚙️ Configuración")
    st.markdown("### 📌 Instrucciones de configuración")
    st.markdown("""
    - **OCR**: Se usa EasyOCR (gratuito, sin API externa).  
    - **Almacenamiento**: Google Sheets (requiere credenciales en secrets).  
    - **Credenciales**: Agrega `GSHEET_CREDENTIALS` en los secrets de Streamlit con el JSON de tu cuenta de servicio.
    """)
    
    st.markdown("### 🔐 Secrets (ejemplo)")
    st.code("""
[GSHEET_CREDENTIALS]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "xxx"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "xxx@xxx.iam.gserviceaccount.com"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/xxx"
    """, language="toml")
    
    st.markdown("### 📡 Estado de conexiones")
    if worksheet:
        st.success("✅ Google Sheets: Conectado")
    else:
        st.error("❌ Google Sheets: No conectado (configura los secrets)")
