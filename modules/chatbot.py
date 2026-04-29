import streamlit as st
import nlp.intent_matcher as intent_matcher

def render_page():
    st.title("💬 AI Chat Assistant")
    st.write("Ask anything about placements, interviews, coding, or aptitude — powered by Gemini AI.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hey! I'm your CrackPlacement AI assistant. Ask me anything about placements, interviews, or coding! 🚀"})
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
