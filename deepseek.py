# Replace the database functions with these:

def load_user_data():
    """Load user data from session state only"""
    pass  # Session state already has everything

def save_response(chapter_id, question, answer):
    """Save response to session state only"""
    user_id = st.session_state.user_id
    
    if chapter_id not in st.session_state.responses:
        st.session_state.responses[chapter_id] = {
            "title": CHAPTERS[chapter_id-1]["title"],
            "questions": {},
            "answered_count": 0
        }
    
    is_new = question not in st.session_state.responses[chapter_id]["questions"]
    st.session_state.responses[chapter_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
    if is_new:
        st.session_state.responses[chapter_id]["answered_count"] += 1
    
    # Save message to session
    st.session_state.messages.append({"role": "user", "content": answer})
