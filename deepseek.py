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
import tempfile

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
    
    /* Compact progress styling */
    .progress-compact {{
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
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
    
    /* Audio input styling */
    .audio-recording {{
        background-color: #e8f5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #4caf50;
    }}
    
    .speech-confirmation {{
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
    }}
    
    .warning-box {{
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
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
    st.session_state.show_speech = True
    st.session_state.pending_transcription = None
    st.session_state.audio_transcribed = False
    st.session_state.show_transcription = False
    st.session_state.auto_submit_text = None
    st.session_state.spellcheck_enabled = True
    st.session_state.editing_word_target = False
    st.session_state.confirming_clear = None
    
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
# SECTION 7: SIMPLIFIED SPEECH-TO-TEXT
# ============================================================================
def transcribe_audio_simple(audio_file):
    """Simplified transcription"""
    try:
        audio_bytes = audio_file.read()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Try transcription
        with open(tmp_path, "rb") as audio_file_obj:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_obj,
                language="en"
            )
        
        os.unlink(tmp_path)
        return transcript.text if transcript.text else "[Could not transcribe. Please type your answer.]"
        
    except Exception as e:
        return "[Speech recorded but transcription failed. Please type your answer.]"

# ============================================================================
# SECTION 8: APP HEADER
# ============================================================================
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 9: SIDEBAR
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
# SECTION 10: MAIN CONTENT - SESSION HEADER
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
# SECTION 11: COMPACT PROGRESS INDICATOR
# ============================================================================
current_word_count = calculate_session_word_count(current_session_id)
target_words = st.session_state.responses[current_session_id].get("word_target", 500)
color, emoji, progress_percent = get_traffic_light(current_session_id)

remaining_words = max(0, target_words - current_word_count)
status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"

st.markdown(f"""
<div class="progress-compact">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <div>
            <span class="traffic-light" style="background-color: {color};"></span>
            <span style="font-size: 0.9rem; font-weight: 500;">{emoji} {progress_percent:.0f}% complete • {status_text}</span>
        </div>
        <div>
            <button onclick="document.getElementById('edit-target-btn').click()" style="
                background: none;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 0.75rem;
                cursor: pointer;
                color: #666;
            ">Change Target</button>
        </div>
    </div>
    <div style="height: 6px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
        <div style="height: 100%; width: {min(progress_percent, 100)}%; background-color: {color}; border-radius: 3px;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Edit target button
if st.button("Change Target", key="edit-target-btn", type="secondary"):
    st.session_state.editing_word_target = not st.session_state.editing_word_target
    st.rerun()

if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    new_target = st.number_input("Target words:", min_value=100, max_value=5000, value=target_words, key="target_edit")
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save", key="save_target", type="primary"):
            st.session_state.responses[current_session_id]["word_target"] = new_target
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_target"):
            st.session_state.editing_word_target = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 12: QUESTION AND GUIDANCE (AS YOU REQUESTED)
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
# SECTION 13: CONVERSATION DISPLAY
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
                    new_text = st.text_area("Edit:", value=st.session_state.edit_text, height=100, key=f"edit_{i}", label_visibility="collapsed")
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
# SECTION 14: SPEECH INPUT (OPTIONAL - SIMPLIFIED)
# ============================================================================
if st.session_state.show_speech and st.checkbox("🎤 Use voice input", key="show_speech_toggle"):
    st.markdown("""
    <div class="audio-recording">
        <strong>Voice Input:</strong><br>
        1. Click microphone below<br>
        2. Speak your answer<br>
        3. Click stop button<br>
        4. Review & confirm
    </div>
    """, unsafe_allow_html=True)
    
    audio_bytes = st.audio_input("Click to record", key=f"audio_{current_session_id}")
    
    if audio_bytes and not st.session_state.audio_transcribed:
        with st.spinner("Transcribing..."):
            transcribed_text = transcribe_audio_simple(audio_bytes)
            if transcribed_text:
                st.session_state.pending_transcription = transcribed_text
                st.session_state.audio_transcribed = True
                st.rerun()
    
    if st.session_state.audio_transcribed and st.session_state.pending_transcription:
        st.markdown('<div class="speech-confirmation">', unsafe_allow_html=True)
        st.write("**Your transcribed answer:**")
        st.write(st.session_state.pending_transcription)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use This", key="use_transcript", type="primary"):
                st.session_state.auto_submit_text = st.session_state.pending_transcription
                st.session_state.pending_transcription = None
                st.session_state.audio_transcribed = False
                st.rerun()
        with col2:
            if st.button("Discard", key="discard_transcript"):
                st.session_state.pending_transcription = None
                st.session_state.audio_transcribed = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 15: TEXT INPUT
# ============================================================================
if st.session_state.editing is None:
    user_input = None
    
    if st.session_state.auto_submit_text:
        user_input = st.session_state.auto_submit_text
        st.session_state.auto_submit_text = None
    else:
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
                    progress = (updated_count / target * 100) if target > 0 else 0
                    
                    if progress < 50:
                        ai_response += f"\n\n*You're building good material here. Your words: {updated_count}/{target}.*"
                    elif progress < 100:
                        ai_response += f"\n\n*Good progress. Your words: {updated_count}/{target}.*"
                    else:
                        ai_response += f"\n\n*Excellent! Your words: {updated_count}/{target}.*"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = "Thank you for sharing that."
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        save_response(current_session_id, current_question_text, user_input)
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
        st.rerun()
