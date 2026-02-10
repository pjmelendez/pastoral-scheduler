import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime

# --- SECURE CONNECTION ---
creds_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(creds_info)
service = build('calendar', 'v3', credentials=creds)
CALENDAR_ID = st.secrets["calendar_id"]

st.set_page_config(page_title="Pastoral Scheduler", page_icon="📅")
st.title("📅 Pastoral Meeting Scheduler")
st.write("Select an available slot below. Name and Phone are required.")

# --- FETCH "AVAILABLE" SLOTS ---
def get_slots():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=now,
        singleEvents=True, orderBy='startTime').execute()
    return [e for e in events_result.get('items', []) if e.get('summary') == 'Available']

slots = get_slots()

if not slots:
    st.info("No available slots right now. Check back soon!")
else:
    for event in slots:
        start_raw = event['start'].get('dateTime')
        start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
        friendly_time = start_dt.strftime("%B %d, %I:%M %p")

        with st.expander(f"Slot: {friendly_time}"):
            name = st.text_input("Your Name", key=f"n_{event['id']}")
            phone = st.text_input("Phone Number", key=f"p_{event['id']}")
            
            if st.button("Confirm Booking", key=f"b_{event['id']}"):
                if name and phone:
                    updated_event = {
                        'summary': f"Pastoral Meeting: {name}",
                        'description': f"Guest: {name}\nPhone: {phone}",
                        'start': event['start'], 'end': event['end']
                    }
                    service.events().update(calendarId=CALENDAR_ID, eventId=event['id'], body=updated_event).execute()
                    st.success("Success! Added to calendar.")
                    st.balloons()
                else:
                    st.error("Please enter Name and Phone.")
