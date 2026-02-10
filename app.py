import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime

# --- CONEXIÓN SEGURA ---
creds_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(creds_info)
service = build('calendar', 'v3', credentials=creds)
CALENDAR_ID = st.secrets["calendar_id"]

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pastoral Online", page_icon="None")
st.title("Agenda Pastoral Online")
st.write("Seleccione un espacio disponible para programar su cita. Se requiere su nombre y teléfono.")

# --- OBTENER ESPACIOS "AVAILABLE" O "DISPONIBLE" ---
def get_slots():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=now,
        singleEvents=True, orderBy='startTime').execute()
    # Busca eventos titulados "Available" o "Disponible"
    return [e for e in events_result.get('items', []) if e.get('summary') in ['Available', 'Disponible', 'disponible', 'available']]

slots = get_slots()

if not slots:
    st.info("No hay espacios disponibles en este momento. Por favor, intente más tarde.")
else:
    for event in slots:
        start_raw = event['start'].get('dateTime')
        start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
        
        # Formato de fecha: "10 de febrero, 03:00 PM"
        friendly_time = start_dt.strftime("%d de %B, %I:%M %p")

        with st.expander(f"Cita para el {friendly_time}"):
            name = st.text_input("Nombre Completo", key=f"n_{event['id']}")
            phone = st.text_input("Número de Teléfono", key=f"p_{event['id']}")
            
            if st.button("Confirmar Cita", key=f"b_{event['id']}"):
                if name and phone:
                    updated_event = {
                        'summary': f"Cita: {name}",
                        'description': f"Nombre: {name}\nTeléfono: {phone}",
                        'start': event['start'], 'end': event['end']
                    }
                    service.events().update(calendarId=CALENDAR_ID, eventId=event['id'], body=updated_event).execute()
                    st.success("¡Cita confirmada exitosamente!")
                    st.balloons()
                else:
                    st.error("Por favor, complete su nombre y teléfono para continuar.")
