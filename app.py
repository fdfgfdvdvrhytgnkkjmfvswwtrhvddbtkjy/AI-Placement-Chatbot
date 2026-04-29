import streamlit as st
import os
import modules.chatbot as chatbot
import modules.aptitude as aptitude
import modules.study_materials as study_materials
import modules.mock_interview as mock_interview
import nlp.intent_matcher as intent_matcher

# Auto-load API key from .env file
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

_load_env()

st.set_page_config(
    page_title="CrackPlacement",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS for premium branding
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

/* Brand Header */
.brand-header {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    padding: 20px 30px;
    border-radius: 12px;
    margin-bottom: 20px;
    text-align: center;
}
.brand-header h1 {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 2.2rem;
    background: linear-gradient(90deg, #00d2ff, #3a7bd5, #00d2ff);
    background-size: 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s ease infinite;
    margin: 0;
}
.brand-header p {
    color: #a0aec0;
    font-size: 0.95rem;
    margin: 5px 0 0 0;
}
@keyframes shimmer {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Buttons */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    transition: all 0.3s ease;
}
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #3a7bd5 0%, #00d2ff 100%);
    box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    transform: translateY(-2px);
}

/* Metrics */
.stMetric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 15px;
    border-radius: 10px;
    color: white;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hey! I'm your CrackPlacement AI assistant. Ask me anything about placements, interviews, or coding! 🚀"})

    # Auto-connect Gemini from .env or Streamlit Cloud secrets
    if not intent_matcher.is_gemini_active():
        env_key = ""
        try:
            env_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
        if not env_key:
            env_key = os.environ.get("GEMINI_API_KEY", "")
        if env_key and env_key != "PASTE_YOUR_KEY_HERE":
            intent_matcher.configure_gemini(env_key)

    # ---- Sidebar ----
    st.sidebar.markdown("""
    <div style="text-align:center; padding: 10px 0;">
        <span style="font-size: 2rem;">🚀</span><br>
        <span style="font-size: 1.4rem; font-weight: 800; 
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        CrackPlacement</span>
    </div>
    """, unsafe_allow_html=True)
    
    pages = {
        "💬 AI Chat": chatbot.render_page,
        "🧠 Aptitude": aptitude.render_page,
        "📚 Study Materials": study_materials.render_page,
        "👔 Mock Interview": mock_interview.render_page
    }
    
    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    
    st.sidebar.markdown("---")
    
    if intent_matcher.is_gemini_active():
        st.sidebar.markdown("🟢 **AI: Gemini Active**")
    else:
        st.sidebar.markdown("🔴 **AI: Offline**")
    
    st.sidebar.caption("Built for B.Tech Students 🎓")
    
    # ---- Brand Header ----
    st.markdown("""
    <div class="brand-header">
        <h1>🚀 CrackPlacement</h1>
        <p>AI-Powered Placement Preparation Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ---- Render selected page ----
    pages[selection]()

    st.markdown("---")
    
    if selection != "💬 AI Chat":
        with st.expander("💬 Quick Chat History", expanded=False):
            for msg in st.session_state.messages[-3:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
    # Global Chat Strip
    if prompt := st.chat_input("Ask CrackPlacement AI anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        response = intent_matcher.get_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    main()
