import streamlit as st
import google.generativeai as genai
import json
import random
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from PIL import Image

# --- CONFIG ---
MODEL_NAME = 'gemini-flash-latest' # We define this here to print it later

# --- SETUP ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    TOKEN_INFO = json.loads(st.secrets["GOOGLE_TOKEN"])
except:
    st.error("Secrets not found! Please set them up in Streamlit Cloud.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)

def get_calendar_service():
    creds = Credentials.from_authorized_user_info(TOKEN_INFO, ['https://www.googleapis.com/auth/calendar'])
    return build('calendar', 'v3', credentials=creds)

def parse_schedule(image):
    model = genai.GenerativeModel(MODEL_NAME)
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
st.caption(f"🚀 Powered by: **{MODEL_NAME}**")

uploaded_file = st.file_uploader("Take a photo of your plan", type=["jpg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    # ONE CLICK ACTION
    if st.button("⚡ Parse & Sync to Calendar"):
        with st.spinner("Reading handwriting & Syncing..."):
            try:
                # 1. Parse
                tasks = parse_schedule(image)
                
                # 2. Sync immediately (No confirm step)
                service = get_calendar_service()
                progress = st.progress(0)
                total = len(tasks)
                
                # Google Calendar Color IDs (1-11 are valid colors)
                # 1:Lavender, 2:Sage, 3:Grape, 4:Flamingo, 5:Banana, 6:Tangerine, etc.
                available_colors = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
                
                for i, t in enumerate(tasks):
                    # Pick a random color for each task
                    color_id = random.choice(available_colors)
                    
                    event = {
                        'summary': t['summary'],
                        'start': {'dateTime': t['start_iso'], 'timeZone': 'Asia/Kolkata'},
                        'end': {'dateTime': t['end_iso'], 'timeZone': 'Asia/Kolkata'},
                        'colorId': color_id 
                    }
                    service.events().insert(calendarId='primary', body=event).execute()
                    progress.progress((i + 1) / total)
                
                st.success(f"✅ Success! Added {total} tasks to your Calendar.")
                
            except Exception as e:
                st.error(f"Detailed Error: {e}")
