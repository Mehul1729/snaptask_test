import streamlit as st
import google.generativeai as genai
import json
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from PIL import Image

# --- SETUP ---
# On Streamlit Cloud, we use st.secrets. 
# On local, you can just set these strings manually for testing.
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    TOKEN_INFO = json.loads(st.secrets["GOOGLE_TOKEN"]) # We paste the JSON here later
except:
    st.error("Secrets not found! Please set them up in Streamlit Cloud.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)

def get_calendar_service():
    # Load credentials directly from the secrets JSON we saved
    creds = Credentials.from_authorized_user_info(TOKEN_INFO, ['https://www.googleapis.com/auth/calendar'])
    return build('calendar', 'v3', credentials=creds)

def parse_schedule(image):
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = """
    Extract schedule from image. Return ONLY a JSON array.
    Format: [{"summary": "Task", "start_iso": "2025-12-29T09:00:00", "end_iso": "2025-12-29T12:00:00"}]
    Assume current year if missing. Use 24hr format.
    """
    response = model.generate_content([prompt, image])
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

# --- APP UI ---
st.set_page_config(page_title="Scheduler", page_icon="📅")
st.title("📅 Auto-Scheduler")

uploaded_file = st.file_uploader("Take a photo of your plan", type=["jpg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    # if st.button("Parse Schedule"):
    #     with st.spinner("Analyzing..."):
    #         try:
    #             st.session_state['tasks'] = parse_schedule(image)
    #         except:
    #             st.error("Could not read image. Try again.")


    if st.button("Parse Schedule"):
        with st.spinner("Analyzing..."):
            try:
                st.session_state['tasks'] = parse_schedule(image)
            except Exception as e:
                st.error(f"Detailed Error: {e}")




    
    if 'tasks' in st.session_state:
        # Simple list to review
        for t in st.session_state['tasks']:
            st.write(f"**{t['summary']}** | {t['start_iso'].split('T')[1]} - {t['end_iso'].split('T')[1]}")
        
        if st.button("Confirm & Add to Calendar"):
            service = get_calendar_service()
            for t in st.session_state['tasks']:
                event = {
                    'summary': t['summary'],
                    'start': {'dateTime': t['start_iso'], 'timeZone': 'Asia/Kolkata'},
                    'end': {'dateTime': t['end_iso'], 'timeZone': 'Asia/Kolkata'},
                }
                service.events().insert(calendarId='primary', body=event).execute()

            st.success("Done! Check your Google Calendar.")

