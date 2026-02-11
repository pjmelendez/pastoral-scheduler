import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime

# --- CONFIGURACIÓN DE SEGURIDAD VISUAL ---
# Esto oculta el menú de GitHub y los menús de Streamlit
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """

# --- CONEXIÓN SEGURA ---
creds_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(creds_info)
service = build('calendar', 'v3', credentials=creds)
CALENDAR_ID = st.secrets["calendar_id"]

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pastoral Online", page_icon="None")
st.markdown(hide_st_style, unsafe_allow_html=True) # Aplicar el estilo oculto
st.title("Agenda Pastoral Online")

if 'reserva_completada' not in st.session_state:
    st.session_state.reserva_completada = False

if st.session_state.reserva_completada:
    st.success("Su cita ha sido confirmada y registrada. Ya puede cerrar esta ventana.")
    if st.button("Volver al inicio"):
        st.session_state.reserva_completada = False
        st.rerun()
else:
    st.write("Seleccione un espacio disponible para su cita.")

    def get_slots():
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=CALENDAR_ID, timeMin=now,
            singleEvents=True, orderBy='startTime').execute()
        return [e for e in events_result.get('items', []) if e.get('summary', '').lower() in ['available', 'disponible']]

    slots = get_slots()

    if not slots:
        st.info("No hay espacios disponibles en este momento.")
    else:
        for event in slots:
            start_raw = event['start'].get('dateTime')
            start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            friendly_time = start_dt.strftime("%d de %B, %I:%M %p")

            with st.expander(f"Cita para el {friendly_time}"):
                name = st.text_input("Nombre Completo", key=f"n_{event['id']}")
                phone = st.text_input("Número de Teléfono", key=f"p_{event['id']}")
                
                if st.button("Confirmar Cita", key=f"b_{event['id']}"):
                    if name and phone:
                        event['summary'] = f"Cita Pastoral: {name}"
                        event['description'] = f"Persona: {name}\nTeléfono: {phone}"
                        
                        try:
                            service.events().update(calendarId=CALENDAR_ID, eventId=event['id'], body=event).execute()
                            st.session_state.reserva_completada = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
                    else:
                        st.error("Por favor, ingrese su nombre y teléfono.")
