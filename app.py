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
    page_title="AI Placement Prep",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for colorful buttons and polished UI
st.markdown("""
<style>
div.stButton > button:first-child {
    background: linear-gradient(90deg, #1CB5E0 0%, #000851 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: 0.3s;
}
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #000851 0%, #1CB5E0 100%);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transform: translateY(-1px);
}
.stMetric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 15px;
    border-radius: 10px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your AI Placement Assistant. How can I help you today?"})

    # Auto-connect Gemini from .env if not already connected
    if not intent_matcher.is_gemini_active():
        env_key = os.environ.get("GEMINI_API_KEY", "")
        if env_key and env_key != "PASTE_YOUR_KEY_HERE":
            intent_matcher.configure_gemini(env_key)

    # ---- Sidebar ----
    st.sidebar.title("🎓 Navigation")
    pages = {
        "💬 Chatbot & Q&A": chatbot.render_page,
        "🧠 Aptitude Practice": aptitude.render_page,
        "📚 Study Materials": study_materials.render_page,
        "👔 Mock Interview": mock_interview.render_page
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    st.sidebar.markdown("---")
    
    # Small AI status indicator only
    if intent_matcher.is_gemini_active():
        st.sidebar.markdown("🟢 **AI: Gemini Active**")
    else:
        st.sidebar.markdown("🔴 **AI: Offline**")
    
    st.sidebar.info("AI Preparation Tool for B.Tech Students")
    
    # ---- Render selected page ----
    pages[selection]()

    st.markdown("---")
    
    # If not on Chatbot page, show chat history expander
    if selection != "💬 Chatbot & Q&A":
        with st.expander("💬 Quick Assistant Chat History", expanded=False):
            for msg in st.session_state.messages[-3:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
    # Global Chat Strip
    if prompt := st.chat_input("Ask your AI Placement Assistant any question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        response = intent_matcher.get_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    main()
