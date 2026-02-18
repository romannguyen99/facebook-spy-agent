import os
import streamlit as st
from dotenv import load_dotenv

# Load local .env file (for local development)
load_dotenv()

class Config:
    # Try to get keys from Streamlit Cloud Secrets first, then fallback to local .env
    
    # 1. APIFY TOKEN
    if "APIFY_API_TOKEN" in st.secrets:
        APIFY_TOKEN = st.secrets["APIFY_API_TOKEN"]
    else:
        APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")

    # 2. GOOGLE GEMINI KEY
    if "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # 3. ACTOR ID
    APIFY_ACTOR_ID = "KoJrdxJCTtpon81KY"

    @staticmethod
    def validate():
        missing = []
        if not Config.APIFY_TOKEN:
            missing.append("APIFY_API_TOKEN")
        if not Config.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        
        if missing:
            raise ValueError(f"Missing API Keys: {', '.join(missing)}")