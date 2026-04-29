import streamlit as st
import json
import nlp.intent_matcher as intent_matcher

def ai_generate_questions(interview_type, role="Software Engineer"):
    """Use Gemini to generate interview questions."""
    if not intent_matcher.is_gemini_active():
        return None
    
    prompt = (
        f"Generate 5 {interview_type} interview questions for a fresher B.Tech student "
        f"applying for {role}. Return ONLY a JSON array of strings, no other text: "
        f'["question 1", "question 2", "question 3", "question 4", "question 5"]'
    )
    
    try:
        import re
        response = intent_matcher._ask_gemini_raw(prompt)
        if not response:
            return None
        response = response.replace("```json", "").replace("```", "").strip()
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            json_str = re.sub(r',\s*\]', ']', json_str)
            return json.loads(json_str)
    except Exception:
        pass
    return None

def ai_evaluate_response(question, answer):
    """Use Gemini to evaluate an interview response."""
    if not intent_matcher.is_gemini_active():
        return None
    
    prompt = (
        f"You are an experienced HR interviewer evaluating a B.Tech fresher's interview response.\n\n"
        f"**Question:** {question}\n"
        f"**Candidate's Answer:** {answer}\n\n"
        f"Evaluate the response and provide:\n"
        f"1. **Score:** X/10\n"
        f"2. **Strengths:** What was good about the answer\n"
        f"3. **Areas for Improvement:** What could be better\n"
        f"4. **Ideal Answer Tips:** Brief guidance on what a perfect answer looks like\n\n"
        f"Be encouraging but honest. Use markdown formatting."
    )
    
    return intent_matcher._ask_gemini(prompt)

def render_page():
    st.title("👔 Mock Interview Simulator")
    st.write("AI-powered interview practice with real-time feedback on your answers.")
    
    if not intent_matcher.is_gemini_active():
        st.warning("Please add your Gemini API key in the `.env` file to use the AI Mock Interview.")
        st.markdown("""
        ### How to enable:
        1. Open the file `.env` in your project folder
        2. Replace `PASTE_YOUR_KEY_HERE` with your Gemini API key
        3. Restart the app
        """)
        return
    
    # Initialize state
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
        st.session_state.current_q_index = 0
        st.session_state.responses = []
        st.session_state.interview_questions = []
        st.session_state.interview_feedback = []
        st.session_state.interview_type = ""
    
    # ---- Setup Screen ----
    if not st.session_state.interview_active and st.session_state.current_q_index == 0:
        st.subheader("Configure Your Interview")
        
        col1, col2 = st.columns(2)
        with col1:
            interview_type = st.selectbox(
                "Interview Type",
                ["HR", "Technical", "Behavioral", "Mixed (HR + Technical)"]
            )
        with col2:
            role = st.text_input("Target Role", value="Software Engineer",
                                placeholder="e.g., Data Analyst, Frontend Developer...")
        
        st.markdown("🤖 **Gemini AI** will generate fresh questions and evaluate your answers in real-time!")
        
        if st.button("🚀 Start Mock Interview", type="primary"):
            st.session_state.interview_type = interview_type
            
            with st.spinner(f"AI is preparing your {interview_type} interview for {role}..."):
                if interview_type == "Mixed (HR + Technical)":
                    hr_qs = ai_generate_questions("HR", role) or []
                    tech_qs = ai_generate_questions("Technical", role) or []
                    questions = hr_qs[:3] + tech_qs[:2]
                else:
                    base_type = interview_type.split(" ")[0]
                    questions = ai_generate_questions(base_type, role)
            
            if questions:
                st.session_state.interview_questions = questions
                st.session_state.interview_active = True
                st.session_state.current_q_index = 0
                st.session_state.responses = []
                st.session_state.interview_feedback = []
                st.rerun()
            else:
                st.error("Could not generate questions. Please check your API key and try again.")
    
    # ---- Active Interview ----
    if st.session_state.interview_active:
        questions = st.session_state.interview_questions
        total = len(questions)
        current = st.session_state.current_q_index
        
        if current < total:
            st.progress((current) / total, text=f"Question {current + 1} of {total}")
            
            st.subheader(f"Q{current + 1}: {questions[current]}")
            
            response = st.text_area(
                "Your response:", 
                key=f"resp_{current}",
                height=150,
                placeholder="Type your answer here... Be detailed and use specific examples."
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Submit Response", type="primary"):
                    if len(response.strip()) < 10:
                        st.warning("Please provide a more detailed response (at least 10 characters).")
                    else:
                        st.session_state.responses.append(response)
                        
                        with st.spinner("AI is evaluating your answer..."):
                            feedback = ai_evaluate_response(questions[current], response)
                        if not feedback:
                            feedback = "Could not evaluate. Please try again."
                        
                        st.session_state.interview_feedback.append(feedback)
                        st.session_state.current_q_index += 1
                        st.rerun()
            with col2:
                if st.button("Skip Question"):
                    st.session_state.responses.append("[Skipped]")
                    st.session_state.interview_feedback.append("You skipped this question. Try to attempt all questions in a real interview.")
                    st.session_state.current_q_index += 1
                    st.rerun()
        else:
            st.session_state.interview_active = False
            st.rerun()
    
    # ---- Results Screen ----
    if not st.session_state.interview_active and st.session_state.current_q_index > 0:
        questions = st.session_state.interview_questions
        
        st.header("📊 Interview Results")
        st.markdown("*Evaluated by Gemini AI*")
        st.markdown("---")
        
        for i, q in enumerate(questions):
            if i < len(st.session_state.responses):
                st.markdown(f"### Q{i+1}: {q}")
                
                if st.session_state.responses[i] == "[Skipped]":
                    st.warning("You skipped this question.")
                else:
                    st.info(f"**Your Answer:** {st.session_state.responses[i]}")
                
                if i < len(st.session_state.interview_feedback):
                    st.markdown(st.session_state.interview_feedback[i])
                
                st.markdown("---")
        
        # Overall AI Assessment
        with st.expander("🤖 Overall AI Assessment", expanded=True):
            if st.button("Generate Overall Assessment", type="primary"):
                all_qa = ""
                for i, q in enumerate(questions):
                    if i < len(st.session_state.responses):
                        all_qa += f"Q: {q}\nA: {st.session_state.responses[i]}\n\n"
                
                prompt = (
                    f"You evaluated a B.Tech fresher's mock {st.session_state.interview_type} interview. "
                    f"Here are all their Q&As:\n\n{all_qa}\n\n"
                    f"Provide:\n"
                    f"1. **Overall Score:** X/10\n"
                    f"2. **Top 3 Strengths**\n"
                    f"3. **Top 3 Areas to Improve**\n"
                    f"4. **Final Verdict:** Ready for interview? (Yes/Almost/Not yet)\n"
                    f"5. **One-week Action Plan** to improve\n\n"
                    f"Be encouraging but honest."
                )
                with st.spinner("Generating overall assessment..."):
                    overall = intent_matcher._ask_gemini(prompt)
                if overall:
                    st.markdown(overall)
        
        if st.button("🔄 Start New Interview", type="primary"):
            st.session_state.interview_active = False
            st.session_state.current_q_index = 0
            st.session_state.responses = []
            st.session_state.interview_questions = []
            st.session_state.interview_feedback = []
            st.rerun()
