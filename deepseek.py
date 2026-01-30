# ============================================================================
# SECTION 1: IMPORTS AND INITIAL SETUP
# ============================================================================
import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 2: CSS STYLING AND VISUAL DESIGN
# ============================================================================
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

st.markdown(f"""
<style>
    .main-header {{
        text-align: center;
        padding-top: 0.5rem;
        margin-top: -1rem;
        margin-bottom: 0.5rem;
    }}
    
    .logo-img {{
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 0.25rem auto;
        display: block;
    }}
    
    .session-guidance {{
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .question-box {{
        background-color: #f8f9fa;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #4a5568;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        font-weight: 500;
    }}
    
    .question-counter {{
        font-size: 1rem;
        font-weight: bold;
        color: #2c3e50;
    }}
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    /* Compact progress styling - CLEANED UP */
    .progress-compact {{
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }}
    
    .progress-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }}
    
    .progress-status {{
        font-size: 0.9rem;
        font-weight: 500;
    }}
    
    .traffic-light {{
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }}
    
    .traffic-green {{ background-color: #2ecc71; }}
    .traffic-yellow {{ background-color: #f39c12; }}
    .traffic-red {{ background-color: #e74c3c; }}
    
    /* Remove all audio/speech related styles */
    .edit-target-box {{
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Ensure sidebar is visible */
    .css-1d391kg {{
        padding-top: 1rem;
    }}
    
    /* Chat message styling */
    .stChatMessage {{
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: SESSION DEFINITIONS
# ============================================================================
SESSIONS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to the Childhood session—this is where we lay the foundation of your story. Professional biographies thrive on specific, sensory-rich memories. I'm looking for the kind of details that transport readers: not just what happened, but how it felt, smelled, sounded. The 'insignificant' moments often reveal the most. Take your time—we're mining for gold here.",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ],
        "completed": False,
        "word_target": 600
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "guidance": "Family stories are complex ecosystems. We're not seeking perfect narratives, but authentic ones. The richest material often lives in the tensions, the unsaid things, the small rituals. My job is to help you articulate what usually goes unspoken. Think in scenes rather than summaries.",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "completed": False,
        "word_target": 500
    },
    {
        "id": 3,
        "title": "Education & Growing Up",
        "guidance": "Education isn't just about schools—it's about how you learned to navigate the world. We're interested in the hidden curriculum: what you learned about yourself, about systems, about survival and growth. Think beyond grades to transformation.",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "completed": False,
        "word_target": 500
    }
]

# ============================================================================
# SECTION 4: DATABASE FUNCTIONS
# ============================================================================
def init_db():
    conn = sqlite3.connect('life_story.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            user_id TEXT,
            session_id INTEGER,
            question TEXT,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_targets (
            session_id INTEGER PRIMARY KEY,
            word_target INTEGER DEFAULT 500
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================================================
# SECTION 5: SESSION STATE INITIALIZATION
# ============================================================================
if "responses" not in st.session_state:
    st.session_state.current_session = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.session_conversations = {}
    st.session_state.editing = None
    st.session_state.edit_text = ""
    st.session_state.ghostwriter_mode = True
    st.session_state.show_speech = False  # Voice input disabled by default
    st.session_state.editing_word_target = False
    
    # Initialize for each session
    for session in SESSIONS:
        session_id = session["id"]
        st.session_state.responses[session_id] = {
            "title": session["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": session.get("word_target", 500)
        }
        st.session_state.session_conversations[session_id] = {}
    
    # Load word targets from database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, word_target FROM word_targets")
        for session_id, word_target in cursor.fetchall():
            if session_id in st.session_state.responses:
                st.session_state.responses[session_id]["word_target"] = word_target
        conn.close()
    except:
        pass

# ============================================================================
# SECTION 6: CORE FUNCTIONS
# ============================================================================
def calculate_session_word_count(session_id):
    """Calculate ONLY the user's words"""
    total_words = 0
    conversations = st.session_state.session_conversations.get(session_id, {})
    
    for question_text, conv in conversations.items():
        for msg in conv:
            if msg["role"] == "user":
                total_words += len(re.findall(r'\w+', msg["content"]))
    
    session_data = st.session_state.responses.get(session_id, {})
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

def get_traffic_light(session_id):
    current_count = calculate_session_word_count(session_id)
    target = st.session_state.responses[session_id].get("word_target", 500)
    
    if target == 0:
        return "#2ecc71", "🟢", 100
    
    progress = (current_count / target) * 100 if target > 0 else 100
    
    if progress >= 100:
        return "#2ecc71", "🟢", progress
    elif progress >= 70:
        return "#f39c12", "🟡", progress
    else:
        return "#e74c3c", "🔴", progress

def save_response(session_id, question, answer):
    user_id = st.session_state.user_id
    
    if session_id not in st.session_state.responses:
        st.session_state.responses[session_id] = {
            "title": SESSIONS[session_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": SESSIONS[session_id-1].get("word_target", 500)
        }
    
    st.session_state.responses[session_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO responses 
            (user_id, session_id, question, answer) 
            VALUES (?, ?, ?, ?)
        """, (user_id, session_id, question, answer))
        conn.commit()
        conn.close()
    except:
        pass

# ============================================================================
# SECTION 7: APP HEADER
# ============================================================================
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 8: SIDEBAR (FIXED TO BE VISIBLE)
# ============================================================================
with st.sidebar:
    st.header("👤 Your Profile")
    new_user_id = st.text_input("Your Name:", value=st.session_state.user_id)
    
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        st.session_state.responses = {}
        st.session_state.session_conversations = {}
        st.session_state.current_session = 0
        st.session_state.current_question = 0
        st.session_state.editing = None
        
        for session in SESSIONS:
            session_id = session["id"]
            st.session_state.responses[session_id] = {
                "title": session["title"],
                "questions": {},
                "summary": "",
                "completed": False,
                "word_target": session.get("word_target", 500)
            }
            st.session_state.session_conversations[session_id] = {}
        st.rerun()
    
    st.divider()
    st.header("📝 Sessions")
    
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        status = "✅" if session_data.get("completed", False) else "●"
        if i == st.session_state.current_session:
            status = "▶️"
        
        if st.button(f"{status} Session {session['id']}: {session['title']}", 
                    key=f"select_{i}", use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    st.divider()
    
    # Session navigation
    current_session = SESSIONS[st.session_state.current_session]
    st.markdown(f'<div class="question-counter">Question {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous", disabled=st.session_state.current_question == 0, key="prev_q"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# ============================================================================
# SECTION 9: MAIN CONTENT - SESSION HEADER
# ============================================================================
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]
current_question_text = current_session["questions"][st.session_state.current_question]

# Session header
st.subheader(f"Session {current_session['id']}: {current_session['title']}")

if st.session_state.ghostwriter_mode:
    st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode</p>', unsafe_allow_html=True)

# Question counter
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f'<div class="question-counter">Question {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
with col2:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Prev", disabled=st.session_state.current_question == 0, key="prev_quick"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with nav_col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_quick"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# ============================================================================
# SECTION 10: CLEAN PROGRESS INDICATOR (NO EDIT BUTTON)
# ============================================================================
current_word_count = calculate_session_word_count(current_session_id)
target_words = st.session_state.responses[current_session_id].get("word_target", 500)
color, emoji, progress_percent = get_traffic_light(current_session_id)

remaining_words = max(0, target_words - current_word_count)
status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"

st.markdown(f"""
<div class="progress-compact">
    <div class="progress-header">
        <div class="progress-status">
            <span class="traffic-light" style="background-color: {color};"></span>
            <span>{emoji} {progress_percent:.0f}% complete • {status_text}</span>
        </div>
    </div>
    <div style="height: 6px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
        <div style="height: 100%; width: {min(progress_percent, 100)}%; background-color: {color}; border-radius: 3px;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Simple target edit button - NO redundant edit button
if st.button("✏️ Change word target", key="edit-target-btn"):
    st.session_state.editing_word_target = not st.session_state.editing_word_target

if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    new_target = st.number_input("Target words for this session:", 
                                 min_value=100, max_value=5000, 
                                 value=target_words, key="target_edit")
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save", key="save_target", type="primary"):
            st.session_state.responses[current_session_id]["word_target"] = new_target
            # Save to database
            try:
                conn = sqlite3.connect('life_story.db')
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO word_targets (session_id, word_target)
                    VALUES (?, ?)
                """, (current_session_id, new_target))
                conn.commit()
                conn.close()
            except:
                pass
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_target"):
            st.session_state.editing_word_target = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 11: QUESTION AND GUIDANCE
# ============================================================================
# Question
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

# Session guidance
st.markdown(f"""
<div class="session-guidance">
    {current_session.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 12: CONVERSATION DISPLAY
# ============================================================================
if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question_text, [])

if not conversation:
    with st.chat_message("assistant"):
        welcome_msg = f"Let's explore this question properly: **{current_question_text}**"
        st.markdown(welcome_msg)
        conversation.append({"role": "assistant", "content": welcome_msg})
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
else:
    for i, message in enumerate(conversation):
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        elif message["role"] == "user":
            is_editing = (st.session_state.editing == (current_session_id, current_question_text, i))
            with st.chat_message("user"):
                if is_editing:
                    new_text = st.text_area("Edit your answer:", 
                                          value=st.session_state.edit_text, 
                                          height=100, 
                                          key=f"edit_{i}", 
                                          label_visibility="collapsed")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_{i}", type="primary"):
                            conversation[i]["content"] = new_text
                            save_response(current_session_id, current_question_text, new_text)
                            st.session_state.editing = None
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_{i}"):
                            st.session_state.editing = None
                            st.rerun()
                else:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(message["content"])
                        word_count = len(re.findall(r'\w+', message["content"]))
                        st.caption(f"{word_count} words")
                    with col2:
                        if st.button("Edit", key=f"edit_btn_{i}"):
                            st.session_state.editing = (current_session_id, current_question_text, i)
                            st.session_state.edit_text = message["content"]
                            st.rerun()

# ============================================================================
# SECTION 13: TEXT INPUT ONLY (VOICE INPUT COMPLETELY REMOVED)
# ============================================================================
if st.session_state.editing is None:
    user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        if current_session_id not in st.session_state.session_conversations:
            st.session_state.session_conversations[current_session_id] = {}
        
        if current_question_text not in st.session_state.session_conversations[current_session_id]:
            st.session_state.session_conversations[current_session_id][current_question_text] = []
        
        conversation = st.session_state.session_conversations[current_session_id][current_question_text]
        conversation.append({"role": "user", "content": user_input})
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": "You are a professional biographer helping document a life story. Be warm, professional, and ask thoughtful follow-up questions."},
                            *conversation[-3:]
                        ],
                        temperature=0.7,
                        max_tokens=300
                    )
                    ai_response = response.choices[0].message.content
                    
                    # Add word count update
                    updated_count = calculate_session_word_count(current_session_id)
                    target = st.session_state.responses[current_session_id].get("word_target", 500)
                    
                    if target > 0:
                        progress = (updated_count / target * 100)
                        if progress < 50:
                            ai_response += f"\n\n*You're building good material here. Your words: {updated_count}/{target}.*"
                        elif progress < 100:
                            ai_response += f"\n\n*Good progress. Your words: {updated_count}/{target}.*"
                        else:
                            ai_response += f"\n\n*Excellent! Target achieved! Your words: {updated_count}/{target}.*"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = "Thank you for sharing that. I appreciate your thoughtful answer."
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        save_response(current_session_id, current_question_text, user_input)
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
        st.rerun()

# ============================================================================
# SECTION 14: BOTTOM NAVIGATION
# ============================================================================
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Previous Question", disabled=st.session_state.current_question == 0):
        st.session_state.current_question = max(0, st.session_state.current_question - 1)
        st.session_state.editing = None
        st.rerun()
with col3:
    if st.button("Next Question →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1):
        st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
        st.session_state.editing = None
        st.rerun()


