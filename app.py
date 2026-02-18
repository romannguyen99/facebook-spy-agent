import streamlit as st
import json
import os
from datetime import datetime
import time

try:
    from scraper import FacebookScraper
    from analyst import ContentAnalyzer
except ImportError:
    st.error("Error: scraper.py or analyst.py not found. Please make sure they are in the same folder.")
    st.stop()

history_file = "history.json"

st.set_page_config(
    page_title="FB post AI Spy",
    page_icon="🕵️",
    layout="wide"
)

# -- Add memory --
# Loads past reports from a local JSON file
def load_history():
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# Saves a new report to the history file, then returns the updated list
def save_to_history(url, competitor_name, report):

    history = load_history()
    
    # Create new entry
    new_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "url": url,
        "name": competitor_name,
        "report": report
    }
    
    # Add to beginning of list (newest first)
    history.insert(0, new_entry)
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
    
    return history

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "current_report" not in st.session_state:
    st.session_state.current_report = None

if "current_name" not in st.session_state:
    st.session_state.current_name = None

with st.sidebar:
    st.title("🗄️ Case Files")
    st.caption("Click to load past reports")
    st.markdown("---")
    
    # Refresh button in case file changed externally
    if st.button("🔄 Refresh History"):
        st.session_state.history = load_history()
        st.rerun()

    if not st.session_state.history:
        st.info("No past investigations.")
    else:
        for item in st.session_state.history:
            btn_label = f"{item['name']}\n{item['timestamp']}"
            if st.button(btn_label, key=item['id'], use_container_width=True):
                st.session_state.current_report = item['report']
                st.session_state.current_name = item['name']
                st.rerun()

# --- MAIN PAGE ---
st.title("🕵️ Competitor's posts AI analyst")
st.markdown("Enter a competitor's Facebook Page URL to generate a analysis:")

# Input Section
with st.form("analysis_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input("Competitor URL", placeholder="https://www.facebook.com/brandname")
    with col2:
        submitted = st.form_submit_button("🚀 Go!", type="primary", use_container_width=True, vertical_alignment="bottom")

# --- ANALYSIS LOGIC ---
if submitted and url_input:
    competitor_name = url_input.strip().split("/")[-1]
    
    # Use st.status for a nice progress log
    with st.status("🕵️ Agent Active!", expanded=True) as status:
        try:
            # STEP 1: SCRAPE
            st.write(f"1. 🔎 I am searching posts from {competitor_name}...")
            scraper = FacebookScraper()
            # Max posts = 5 for speed. Increase to 10-20 for production.
            posts = scraper.scrape(url_input, max_posts=5)
            
            if not posts:
                status.update(label="Error: No data found", state="error")
                st.error("😭 No posts found. The page might be private, empty, or blocking bots.")
                st.stop()
            
            st.write(f"😃☝️ À há! I have read {len(posts)} posts. Start organizing the content...")
            
            # STEP 2: ANALYZE
            st.write("2. 😋 Oke! Now Gemini 2.5 Flash is reading their content for analyzing...")
            analyzer = ContentAnalyzer()
            report = analyzer.analyze(posts, competitor_name)
            
            st.write("Great! The analysis complete.")
            status.update(label="Mission Complete", state="complete")
            
            # STEP 3: SAVE
            updated_history = save_to_history(url_input, competitor_name, report)
            st.session_state.history = updated_history
            
            # STEP 4: UPDATE DISPLAY
            st.session_state.current_report = report
            st.session_state.current_name = competitor_name
            st.rerun()

        except Exception as e:
            status.update(label="Error Occurred", state="error")
            st.error(f"System Failure: {str(e)}")

# --- REPORT DISPLAY ---
if st.session_state.current_report:
    st.markdown("---")
    st.header(f"📂 Report: {st.session_state.current_name}")
    
    # Display the markdown report
    st.markdown(st.session_state.current_report)
    
    # Download Button
    st.download_button(
        label="📥 Download Report",
        data=st.session_state.current_report,
        file_name=f"report_{st.session_state.current_name}.md",
        mime="text/markdown"
    )