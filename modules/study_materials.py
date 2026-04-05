import streamlit as st
import json
import os
import base64

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

import nlp.intent_matcher as intent_matcher

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'study_notes.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}

def display_pdf(uploaded_file):
    base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    uploaded_file.seek(0)

def extract_pdf_text(uploaded_file):
    if not PYPDF2_AVAILABLE:
        return ""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        uploaded_file.seek(0)
        return text
    except Exception:
        return ""

def ai_summarize_topic(topic, subject):
    """Use Gemini to generate detailed notes on a topic."""
    if not intent_matcher.is_gemini_active():
        return None
    prompt = (
        f"You are a computer science professor. Generate comprehensive study notes on the topic "
        f"'{topic}' under the subject '{subject}' for B.Tech final year students preparing for placements.\n\n"
        f"Include:\n"
        f"- Clear definition and explanation\n"
        f"- Key concepts with examples\n"
        f"- Common interview questions on this topic\n"
        f"- Important formulas or rules (if any)\n"
        f"- Tips to remember\n\n"
        f"Use markdown formatting with headers, bullet points, and bold text."
    )
    return intent_matcher._ask_gemini(prompt)

def ai_summarize_pdf(pdf_text):
    """Use Gemini to summarize a PDF document."""
    if not intent_matcher.is_gemini_active():
        return None
    # Limit text to avoid token limits
    truncated = pdf_text[:8000]
    prompt = (
        f"Summarize the following study material in a structured format. "
        f"Include key topics, important definitions, formulas, and potential interview questions.\n\n"
        f"Document content:\n{truncated}"
    )
    return intent_matcher._ask_gemini(prompt)

def render_page():
    st.title("📚 Study Materials")
    st.write("Access comprehensive notes for core engineering subjects or upload your own PDFs.")
    
    if intent_matcher.is_gemini_active():
        tab1, tab2, tab3 = st.tabs(["📖 Pre-loaded Subjects", "📄 Upload & Analyze PDFs", "🤖 AI Study Notes Generator"])
    else:
        tab1, tab2 = st.tabs(["📖 Pre-loaded Subjects", "📄 Upload & Analyze PDFs"])
        tab3 = None
    
    # ---- Tab 1: Pre-loaded ----
    with tab1:
        data = load_data()
        if not data:
            st.error("Could not load study materials data.")
            return
            
        subject = st.selectbox("Select Subject", list(data.keys()))
        st.subheader(f"{subject} Concepts")
        notes = data.get(subject, {})
        
        for topic, content in notes.items():
            with st.expander(topic):
                st.write(content)
                
                # AI explain button
                if intent_matcher.is_gemini_active():
                    if st.button(f"🤖 Explain '{topic}' in detail with AI", key=f"ai_explain_{subject}_{topic}"):
                        with st.spinner("AI is generating detailed notes..."):
                            detailed = ai_summarize_topic(topic, subject)
                        if detailed:
                            st.markdown("---")
                            st.markdown(detailed)
                
    # ---- Tab 2: PDF Upload ----
    with tab2:
        st.subheader("📄 AI-Powered PDF Analyzer")
        st.write("Upload **multiple PDFs** and the AI will analyze all of them. "
                 "You can then ask questions using the chat bar!")
        
        if "uploaded_pdf_names" not in st.session_state:
            st.session_state.uploaded_pdf_names = []
        
        uploaded_files = st.file_uploader(
            "Upload study documents (PDF)", 
            type=["pdf"],
            accept_multiple_files=True,
            help="You can select multiple PDF files at once."
        )
        
        if uploaded_files:
            new_files = []
            current_names = [f.name for f in uploaded_files]
            
            for old_name in list(st.session_state.uploaded_pdf_names):
                if old_name not in current_names:
                    intent_matcher.doc_store.remove_document(old_name)
            
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.uploaded_pdf_names:
                    new_files.append(uploaded_file)
            
            if new_files:
                progress_bar = st.progress(0, text="Analyzing documents...")
                for i, uploaded_file in enumerate(new_files):
                    progress_bar.progress(
                        (i + 1) / len(new_files), 
                        text=f"Analyzing: {uploaded_file.name}..."
                    )
                    pdf_text = extract_pdf_text(uploaded_file)
                    if pdf_text:
                        intent_matcher.doc_store.add_document(uploaded_file.name, pdf_text)
                
                progress_bar.progress(1.0, text="Building AI search index...")
                intent_matcher.doc_store.build_index()
                progress_bar.empty()
            
            st.session_state.uploaded_pdf_names = current_names
            
            doc_count = intent_matcher.doc_store.get_document_count()
            total_words = intent_matcher.doc_store.get_total_words()
            total_chunks = len(intent_matcher.doc_store.chunks)
            
            st.success(f"**{doc_count} document(s)** loaded and indexed!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Documents", doc_count)
            with col2:
                st.metric("Total Words", f"{total_words:,}")
            with col3:
                st.metric("AI Chunks", total_chunks)
            
            st.info("Ask any question in the chat bar at the bottom!")
            
            # AI Summarize button for each PDF
            if intent_matcher.is_gemini_active():
                for uploaded_file in uploaded_files:
                    with st.expander(f"📖 {uploaded_file.name}", expanded=False):
                        col_a, col_b = st.columns([1, 1])
                        with col_a:
                            if st.button(f"🤖 AI Summary", key=f"sum_{uploaded_file.name}"):
                                text = intent_matcher.doc_store.documents.get(uploaded_file.name, "")
                                if text:
                                    with st.spinner("Generating AI summary..."):
                                        summary = ai_summarize_pdf(text)
                                    if summary:
                                        st.markdown(summary)
                        with col_b:
                            if st.button(f"📄 Preview PDF", key=f"prev_{uploaded_file.name}"):
                                display_pdf(uploaded_file)
            else:
                for uploaded_file in uploaded_files:
                    with st.expander(f"📖 Preview: {uploaded_file.name}", expanded=False):
                        display_pdf(uploaded_file)
        else:
            if st.session_state.uploaded_pdf_names:
                intent_matcher.doc_store.clear()
                st.session_state.uploaded_pdf_names = []
            
            st.markdown("""
            ### How it works:
            1. Upload one or more PDF documents above
            2. AI analyzes the content automatically
            3. Ask questions in the chat bar
            4. Get answers with relevance scores and source references
            """)
    
    # ---- Tab 3: AI Study Notes Generator ----
    if tab3 is not None:
        with tab3:
            st.subheader("🤖 AI Study Notes Generator")
            st.write("Enter any topic and the AI will generate comprehensive study notes for you!")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                topic_input = st.text_input(
                    "Enter a topic",
                    placeholder="e.g., Binary Search Trees, TCP/IP, Normalization, Deadlocks..."
                )
            with col2:
                subject_input = st.selectbox(
                    "Subject Area",
                    ["Data Structures", "DBMS", "Operating Systems", "Computer Networks",
                     "OOP", "Python", "Java", "Software Engineering", "Other"]
                )
            
            if st.button("📝 Generate Study Notes", type="primary"):
                if not topic_input:
                    st.warning("Please enter a topic!")
                else:
                    with st.spinner(f"AI is generating notes on '{topic_input}'..."):
                        notes = ai_summarize_topic(topic_input, subject_input)
                    if notes:
                        st.markdown("---")
                        st.markdown(notes)
                    else:
                        st.error("Could not generate notes. Try again.")
