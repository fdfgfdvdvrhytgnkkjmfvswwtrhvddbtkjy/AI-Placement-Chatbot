import streamlit as st
import json
import nlp.intent_matcher as intent_matcher

def generate_ai_questions(topic, num_questions=5):
    """Use Gemini AI to generate aptitude questions on a given topic."""
    if not intent_matcher.is_gemini_active():
        st.error("Gemini AI is not active. Check your API key.")
        return None
    
    prompt = (
        f"Generate {num_questions} MCQ questions on '{topic}'. "
        f"Reply with ONLY JSON, no other text. Format: "
        f'{{"questions":[{{"question":"text","options":["A) a","B) b","C) c","D) d"],"answer":"A) a","explanation":"why"}}]}}'
    )
    
    try:
        response = intent_matcher._ask_gemini_raw(prompt)
        if not response:
            st.error("Gemini returned empty response. Try again.")
            return None
        
        # Clean up response
        import re
        response = response.replace("```json", "").replace("```", "").strip()
        
        # Remove any text before first { and after last }
        start = response.find("{")
        end = response.rfind("}") + 1
        if start < 0 or end <= start:
            st.error(f"No JSON found in response. Raw: {response[:200]}")
            return None
        
        json_str = response[start:end]
        
        # Fix common JSON issues
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        try:
            data = json.loads(json_str)
            questions = data.get("questions", [])
            if questions:
                return questions
            else:
                st.error("JSON parsed but no questions found.")
                return None
        except json.JSONDecodeError as je:
            # Fallback: extract individual question objects
            pattern = r'\{[^{}]*"question"\s*:\s*"[^"]*"[^{}]*\}'
            matches = re.findall(pattern, json_str, re.DOTALL)
            if matches:
                questions = []
                for m in matches:
                    try:
                        q = json.loads(m)
                        if "question" in q and "options" in q:
                            if "answer" not in q:
                                q["answer"] = q["options"][0]
                            if "explanation" not in q:
                                q["explanation"] = "No explanation available."
                            questions.append(q)
                    except Exception:
                        continue
                if questions:
                    return questions
            st.error(f"JSON parse error: {str(je)[:150]}")
            st.code(json_str[:300], language="json")
            return None
    except Exception as e:
        st.error(f"AI error: {str(e)}")
    
    return None

def render_page():
    st.title("🧠 Aptitude Practice")
    st.write("Generate fresh aptitude questions on any topic using AI!")
    
    if not intent_matcher.is_gemini_active():
        st.warning("Please add your Gemini API key in the `.env` file to use AI-generated questions.")
        st.markdown("""
        ### How to enable:
        1. Open the file `.env` in your project folder
        2. Replace `PASTE_YOUR_KEY_HERE` with your Gemini API key
        3. Restart the app
        """)
        return
    
    st.subheader("🤖 AI-Powered Question Generator")
    
    # Quick topic buttons
    st.markdown("**Quick Topics:**")
    quick_topics = ["Percentages", "Time & Work", "Probability", "Profit & Loss", 
                    "Blood Relations", "Coding-Decoding", "Syllogisms", "Number Series"]
    
    cols = st.columns(4)
    selected_quick = None
    for i, topic in enumerate(quick_topics):
        with cols[i % 4]:
            if st.button(topic, key=f"quick_{topic}"):
                selected_quick = topic
    
    st.markdown("---")
    
    # Custom topic input
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "Or enter a custom topic",
            value=selected_quick if selected_quick else "",
            placeholder="e.g., Permutations, Data Interpretation, Averages..."
        )
    with col2:
        num_q = st.selectbox("Questions", [3, 5, 8, 10], index=1)
    
    if st.button("🚀 Generate Questions", type="primary") or selected_quick:
        actual_topic = selected_quick if selected_quick else topic
        if not actual_topic:
            st.warning("Please enter a topic or click a quick topic button!")
        else:
            with st.spinner(f"AI is generating {num_q} questions on '{actual_topic}'..."):
                questions = generate_ai_questions(actual_topic, num_q)
            
            if questions:
                st.session_state.ai_questions = questions
                st.session_state.ai_topic = actual_topic
                st.session_state.ai_score = 0
                st.session_state.ai_answered = {}
                st.rerun()
            else:
                st.error("Could not generate questions. Try a different topic.")
    
    # Display generated questions
    if "ai_questions" in st.session_state and st.session_state.ai_questions:
        st.markdown(f"### Topic: {st.session_state.ai_topic}")
        st.markdown(f"*{len(st.session_state.ai_questions)} questions generated by Gemini AI*")
        st.markdown("---")
        
        for i, q in enumerate(st.session_state.ai_questions):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            
            user_choice = st.radio(
                "Select your answer:",
                q["options"],
                key=f"ai_q_{i}",
                index=None
            )
            
            if st.button("Check Answer", key=f"ai_btn_{i}"):
                if i not in st.session_state.ai_answered:
                    if user_choice == q["answer"]:
                        st.success("Correct! 🎉")
                        st.session_state.ai_score += 1
                    else:
                        st.error(f"Incorrect. The correct answer is **{q['answer']}**")
                    st.info(f"**Explanation:** {q['explanation']}")
                    st.session_state.ai_answered[i] = True
                else:
                    if user_choice == q["answer"]:
                        st.success("Correct! 🎉")
                    else:
                        st.error(f"Incorrect. The correct answer is **{q['answer']}**")
                    st.info(f"**Explanation:** {q['explanation']}")
            
            st.markdown("---")
        
        # Score summary
        answered = len(st.session_state.ai_answered)
        total = len(st.session_state.ai_questions)
        if answered > 0:
            score = st.session_state.ai_score
            percentage = (score / answered) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{score}/{answered}")
            with col2:
                st.metric("Percentage", f"{percentage:.0f}%")
            with col3:
                st.metric("Remaining", f"{total - answered}")
        
        if st.button("🔄 Generate New Questions", type="primary"):
            del st.session_state.ai_questions
            del st.session_state.ai_topic
            del st.session_state.ai_score
            del st.session_state.ai_answered
            st.rerun()
