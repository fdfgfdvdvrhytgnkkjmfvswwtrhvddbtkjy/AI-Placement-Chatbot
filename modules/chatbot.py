import streamlit as st
import nlp.intent_matcher as intent_matcher

def render_page():
    st.title("💬 HR & Technical Chatbot")
    st.write("Ask your interview and placement questions here. The chatbot will use NLP to assist you.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add greeting
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your AI Placement Assistant. How can I help you today?"})
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
