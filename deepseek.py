# ============================================================================
# SECTION 1: IMPORTS AND INITIAL SETUP
# ============================================================================
import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import re  # For word counting

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 2: CSS STYLING AND VISUAL DESIGN
# ============================================================================
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

st.markdown(f"""
<style>
    /* Fix header spacing */
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
    
    .chapter-guidance {{
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
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4a5568;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .question-counter {{
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
    }}
    
    /* Chat styling */
    .stChatMessage {{
        margin-bottom: 0.5rem !important;
    }}
    
    .user-message-container {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
    }}
    
    .message-text {{
        flex: 1;
        min-width: 0;
    }}
    
    /* Remove extra margins */
    [data-testid="stAppViewContainer"] {{
        padding-top: 0.5rem !important;
    }}
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    .edit-target-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }}
    
    .danger-button {{
        background-color: #e74c3c !important;
        color: white !important;
        border-color: #c0392b !important;
    }}
    
    .danger-button:hover {{
        background-color: #c0392b !important;
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
# SECTION 3: SESSION DEFINITIONS AND DATA STRUCTURE
# ============================================================================
SESSIONS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to Session 1: Childhood—this is where we lay the foundation of your story. Professional biographies thrive on specific, sensory-rich memories. I'm looking for the kind of details that transport readers: not just what happened, but how it felt, smelled, sounded. The 'insignificant' moments often reveal the most. Take your time—we're mining for gold here.",
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
        "word_target": 800
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "guidance": "Welcome to Session 2: Family & Relationships—this is where we explore the people who shaped you. Family stories are complex ecosystems. We're not seeking perfect narratives, but authentic ones. The richest material often lives in the tensions, the unsaid things, the small rituals. My job is to help you articulate what usually goes unspoken. Think in scenes rather than summaries.",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "completed": False,
        "word_target": 700
    },
    {
        "id": 3,
        "title": "Education & Growing Up",
        "guidance": "Welcome to Session 3: Education & Growing Up—this is where we explore how you learned to navigate the world. Education isn't just about schools—it's about how you learned to navigate the world. We're interested in the hidden curriculum: what you learned about yourself, about systems, about survival and growth. Think beyond grades to transformation.",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "completed": False,
        "word_target": 600
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
    st.session_state.spellcheck_enabled = True
    st.session_state.editing_word_target = False
    st.session_state.confirming_clear = None  # 'session' or 'all' or None
    
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
# SECTION 6: CORE APPLICATION FUNCTIONS
# ============================================================================
def load_user_data():
    if st.session_state.user_id == "Guest":
        return
    
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, question, answer 
            FROM responses 
            WHERE user_id = ?
        """, (st.session_state.user_id,))
        
        for session_id, question, answer in cursor.fetchall():
            if session_id not in st.session_state.responses:
                continue
            st.session_state.responses[session_id]["questions"][question] = {
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }
        
        conn.close()
    except:
        pass

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

def save_word_target(session_id, word_target):
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO word_targets 
            (session_id, word_target) 
            VALUES (?, ?)
        """, (session_id, word_target))
        conn.commit()
        conn.close()
    except:
        pass

def calculate_author_word_count(session_id):
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

def get_traffic_light(session_id):
    current_count = calculate_author_word_count(session_id)
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

# ============================================================================
# SECTION 7: AUTO-CORRECT FUNCTION
# ============================================================================
def auto_correct_text(text):
    """Auto-correct text using OpenAI"""
    if not text or not st.session_state.spellcheck_enabled:
        return text
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes in the following text. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return text  # Return original if OpenAI fails

# ============================================================================
# SECTION 8: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    current_question = current_session["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a professional biographer and ghostwriter helping someone document their life story for a UK English-speaking audience.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT QUESTION: "{current_question}"

CORE PRINCIPLES:
1. You are warm but purposeful—not fawning, not overly casual
2. You think in narrative structure and concrete detail
3. Your questions are designed to extract rich, publishable material
4. You value specificity over generality, scenes over summaries
5. You are comfortable with thoughtful pauses and depth

TONE GUIDELINES:
- Warm but professional, like an experienced journalist or established biographer
- UK English: "worktop" not "countertop", "fortnight" not "two weeks", "quite" used judiciously
- Avoid Americanisms and overly sentimental language
- Not effusive, but genuinely engaged
- Respectful persistence when responses need deepening

CONVERSATION STRUCTURE:
For each response from the user:
1. ACKNOWLEDGE WITH PURPOSE (1 sentence): Not generic praise, but recognition of what's revealing
2. PLANT A FOLLOW-UP SEED (1 sentence): Suggest why this matters for the narrative
3. ASK ONE STRATEGIC QUESTION (1 question maximum): Choose based on what's needed

EXAMPLE RESPONSE TO "I remember my grandmother's kitchen":
"Kitchens often hold family history. Let's step into that space properly. What's the first smell that comes to mind? The feel of the worktop? And crucially—what version of yourself lived in that kitchen that doesn't exist elsewhere?"

Focus: Extract material for a compelling biography. Every question should serve that purpose."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT QUESTION: "{current_question}"

Please:
1. Listen actively to their response
2. Acknowledge it warmly (1-2 sentences)
3. Ask ONE natural follow-up question if appropriate
4. Keep the conversation flowing naturally

Tone: Kind, curious, professional
Goal: Draw out authentic, detailed memories

Focus ONLY on the current question. Don't reference previous sessions."""

# ============================================================================
# SECTION 9: MAIN APP HEADER
# ============================================================================
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.user_id != "Guest":
    load_user_data()

# ============================================================================
# SECTION 10: SIDEBAR - USER PROFILE AND SETTINGS
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
        st.session_state.edit_text = ""
        st.session_state.editing_word_target = False
        st.session_state.confirming_clear = None
        
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
        
        load_user_data()
        st.rerun()
    
    st.divider()
    st.header("✍️ Interview Style")
    
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode", 
        value=st.session_state.ghostwriter_mode,
        help="When enabled, the AI acts as a professional biographer using advanced interviewing techniques."
    )
    
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    spellcheck_enabled = st.toggle(
        "Auto Spelling Correction",
        value=st.session_state.spellcheck_enabled,
        help="Automatically correct spelling and grammar as you type"
    )
    
    if spellcheck_enabled != st.session_state.spellcheck_enabled:
        st.session_state.spellcheck_enabled = spellcheck_enabled
        st.rerun()
    
    if st.session_state.ghostwriter_mode:
        st.success("✓ Professional mode active")
    else:
        st.info("Standard mode active")
    
    # ============================================================================
    # SECTION 10A: SIDEBAR - SESSION NAVIGATION
    # ============================================================================
    st.divider()
    st.header("📖 Sessions")
    
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        # Determine session status
        if session_data.get("completed", False):
            status = "✅"
        elif i == st.session_state.current_session:
            status = "▶️"
        else:
            status = "●"
        
        # Session button (just title)
        button_text = f"{status} Session {session_id}: {session['title']}"
        
        if st.button(button_text, 
                    key=f"select_{i}",
                    use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    # ============================================================================
    # SECTION 10B: SIDEBAR - NAVIGATION CONTROLS
    # ============================================================================
    st.divider()
    st.subheader("Question Navigation")
    
    current_session = SESSIONS[st.session_state.current_session]
    st.markdown(f'<div class="question-counter">Question {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous", disabled=st.session_state.current_question == 0, key="prev_q_sidebar"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    
    with col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q_sidebar"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()
    
    st.divider()
    st.subheader("Session Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Prev Session", disabled=st.session_state.current_session == 0, key="prev_session_sidebar"):
            st.session_state.current_session = max(0, st.session_state.current_session - 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    with col2:
        if st.button("Next Session →", disabled=st.session_state.current_session >= len(SESSIONS)-1, key="next_session_sidebar"):
            st.session_state.current_session = min(len(SESSIONS)-1, st.session_state.current_session + 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    session_options = [f"Session {s['id']}: {s['title']}" for s in SESSIONS]
    selected_session = st.selectbox("Jump to session:", session_options, index=st.session_state.current_session)
    if session_options.index(selected_session) != st.session_state.current_session:
        st.session_state.current_session = session_options.index(selected_session)
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.rerun()
    
    st.divider()
    
    # ============================================================================
    # SECTION 10C: SIDEBAR - EXPORT OPTIONS
    # ============================================================================
    st.subheader("📤 Export Options")
    
    total_answers = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    st.caption(f"Total answers to export: {total_answers}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_answers > 0:
            # Simple export implementation
            export_data = {"sessions": {}}
            for session in SESSIONS:
                session_id = session["id"]
                session_data = st.session_state.responses.get(session_id, {})
                if session_data.get("questions"):
                    export_data["sessions"][session_id] = session_data
            
            st.download_button(
                label="Download as JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"LifeStory_{st.session_state.user_id}.json",
                mime="application/json"
            )
        else:
            st.warning("No responses to export yet!")
    
    st.divider()
    
    # ============================================================================
    # SECTION 10D: SIDEBAR - DANGEROUS ACTIONS WITH CONFIRMATION
    # ============================================================================
    st.subheader("⚠️ Dangerous Actions")
    
    if st.session_state.confirming_clear == "session":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will permanently delete ALL answers in the current session!**")
        st.write("Type 'DELETE SESSION' to confirm:")
        
        confirm_text = st.text_input("Confirmation:", key="confirm_session_delete", label_visibility="collapsed")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete", type="primary", use_container_width=True, disabled=confirm_text != "DELETE SESSION"):
                if confirm_text == "DELETE SESSION":
                    current_session_id = SESSIONS[st.session_state.current_session]["id"]
                    try:
                        conn = sqlite3.connect('life_story.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM responses WHERE user_id = ? AND session_id = ?", 
                                      (st.session_state.user_id, current_session_id))
                        conn.commit()
                        conn.close()
                        st.session_state.responses[current_session_id]["questions"] = {}
                        st.session_state.confirming_clear = None
                        st.success("Session cleared!")
                        st.rerun()
                    except:
                        pass
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.confirming_clear == "all":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will permanently delete ALL answers in ALL sessions!**")
        st.write("Type 'DELETE ALL' to confirm:")
        
        confirm_text = st.text_input("Confirmation:", key="confirm_all_delete", label_visibility="collapsed")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete All", type="primary", use_container_width=True, disabled=confirm_text != "DELETE ALL"):
                if confirm_text == "DELETE ALL":
                    try:
                        conn = sqlite3.connect('life_story.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM responses WHERE user_id = ?", 
                                      (st.session_state.user_id,))
                        conn.commit()
                        conn.close()
                        for session in SESSIONS:
                            session_id = session["id"]
                            st.session_state.responses[session_id]["questions"] = {}
                        st.session_state.confirming_clear = None
                        st.success("All data cleared!")
                        st.rerun()
                    except:
                        pass
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Session", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = "session"
                st.rerun()
        
        with col2:
            if st.button("🔥 Clear All", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = "all"
                st.rerun()

# ============================================================================
# SECTION 11: MAIN CONTENT - SESSION HEADER
# ============================================================================
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]
current_question_text = current_session["questions"][st.session_state.current_question]

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode • Advanced Interviewing</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="ghostwriter-tag">Standard Interview Mode</p>', unsafe_allow_html=True)
        
with col2:
    st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Question {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Prev", disabled=st.session_state.current_question == 0, key="prev_q_quick"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with nav_col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q_quick"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# Show current question
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

# Show session guidance
st.markdown(f"""
<div class="chapter-guidance">
    {current_session.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# Questions progress
session_data = st.session_state.responses.get(current_session_id, {})
questions_answered = len(session_data.get("questions", {}))
total_questions = len(current_session["questions"])

if total_questions > 0:
    question_progress = questions_answered / total_questions
    st.progress(min(question_progress, 1.0))
    st.caption(f"📝 Questions answered: {questions_answered}/{total_questions} ({question_progress*100:.0f}%)")

# ============================================================================
# SECTION 12: CONVERSATION DISPLAY
# ============================================================================
current_session_id = current_session["id"]
current_question_text = current_session["questions"][st.session_state.current_question]

if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question_text, [])

if not conversation:
    with st.chat_message("assistant"):
        if st.session_state.ghostwriter_mode:
            welcome_msg = f"""Let's explore this question properly: **{current_question_text}**

Take your time with this—good biographies are built from thoughtful reflection rather than quick answers."""
        else:
            welcome_msg = f"I'd love to hear your thoughts about this question: **{current_question_text}**"
        
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
                    # Edit mode
                    new_text = st.text_area(
                        "Edit your answer:",
                        value=st.session_state.edit_text,
                        key=f"edit_area_{current_session_id}_{hash(current_question_text)}_{i}",
                        height=150,
                        label_visibility="collapsed"
                    )
                    
                    if new_text:
                        edit_word_count = len(re.findall(r'\w+', new_text))
                        st.caption(f"📝 Editing: {edit_word_count} words")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Save", key=f"save_{current_session_id}_{hash(current_question_text)}_{i}", type="primary"):
                            # Auto-correct before saving
                            if st.session_state.spellcheck_enabled:
                                new_text = auto_correct_text(new_text)
                            
                            conversation[i]["content"] = new_text
                            st.session_state.session_conversations[current_session_id][current_question_text] = conversation
                            save_response(current_session_id, current_question_text, new_text)
                            st.session_state.editing = None
                            st.rerun()
                    with col2:
                        if st.button("✕ Cancel", key=f"cancel_{current_session_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = None
                            st.rerun()
                else:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(message["content"])
                        word_count = len(re.findall(r'\w+', message["content"]))
                        st.caption(f"📝 {word_count} words • Click ✏️ to edit")
                    with col2:
                        if st.button("✏️", key=f"edit_{current_session_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = (current_session_id, current_question_text, i)
                            st.session_state.edit_text = message["content"]
                            st.rerun()

# ============================================================================
# SECTION 8: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    current_question = current_session["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer with multiple award-winning books to your name. You're working with someone on their life story, and you treat this with the seriousness of archival research combined with literary craft.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT QUESTION: "{current_question}"

YOUR APPROACH:
1. You listen like an archivist—hearing not just what's said, but what's implied
2. You think in scenes, sensory details, and emotional truth
3. You're not here to flatter; you're here to find the story that needs to be told
4. You respect silence and complexity—you don't rush toward resolution
5. You understand that memory is reconstruction, and you help reconstruct with integrity

TECHNIQUE:
- After they share, you often pause before responding (reflected in thoughtful language)
- You reference specific details they've mentioned, showing you're truly listening
- You ask questions that open space rather than close it
- You sometimes gently challenge assumptions or explore contradictions
- You're comfortable with ambiguity and unresolved moments

EXAMPLE RESPONSES:
To "I remember my grandmother's kitchen always smelled of cinnamon":
"That's telling—cinnamon as character. Not just a smell, but a presence. Was it the cinnamon of baking or of potpourri? And did that scent mean comfort, or duty, or something more complicated?"

To "School was mostly boring until Mr. Jenkins' class":
"Let's sit with 'mostly boring' for a moment. What did that boredom feel like in your body? And what specifically shifted in Mr. Jenkins' room—was it the material, his presence, or something in you that changed?"

Tone: Literary but not pretentious. Serious but not solemn. You're doing important work, and it shows in your attention to detail."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT QUESTION: "{current_question}"

Please:
1. Listen actively to their response
2. Acknowledge it warmly (1-2 sentences)
3. Ask ONE natural follow-up question if appropriate
4. Keep the conversation flowing naturally

Tone: Kind, curious, professional
Goal: Draw out authentic, detailed memories

Focus ONLY on the current question. Don't reference previous sessions."""

# ============================================================================
# SECTION 14: PROGRESS BAR AT BOTTOM
# ============================================================================
st.divider()
st.subheader("📊 Session Progress")

# Calculate current word count and progress
current_word_count = calculate_author_word_count(current_session_id)
target_words = st.session_state.responses[current_session_id].get("word_target", 500)
color, emoji, progress_percent = get_traffic_light(current_session_id)

# Calculate remaining words
remaining_words = max(0, target_words - current_word_count)
status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"

# Display progress with only ONE emoji
st.markdown(f"""
<div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem;">
    {emoji} {progress_percent:.0f}% complete • {status_text}
</div>
""", unsafe_allow_html=True)

# Progress bar
st.progress(min(progress_percent/100, 1.0))

# Edit target button
if st.button("✏️ Change Word Target", key="edit_word_target_bottom", use_container_width=False):
    st.session_state.editing_word_target = not st.session_state.editing_word_target
    st.rerun()

# Show edit interface when triggered
if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    st.write("**Change Word Target**")
    
    new_target = st.number_input(
        "Target words for this session:",
        min_value=100,
        max_value=5000,
        value=target_words,
        key="target_edit_input_bottom",
        label_visibility="collapsed"
    )
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Save", key="save_word_target_bottom", type="primary", use_container_width=True):
            # Update session state
            st.session_state.responses[current_session_id]["word_target"] = new_target
            # Update database
            save_word_target(current_session_id, new_target)
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", key="cancel_word_target_bottom", use_container_width=True):
            st.session_state.editing_word_target = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 15: FOOTER WITH STATISTICS
# ============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    total_words_all_sessions = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    st.metric("Total Words", f"{total_words_all_sessions}")
with col2:
    completed_sessions = sum(1 for s in SESSIONS if st.session_state.responses[s["id"]].get("completed", False))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_questions_answered = sum(len(st.session_state.responses[s["id"]].get("questions", {})) for s in SESSIONS)
    total_all_questions = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Questions Answered", f"{total_questions_answered}/{total_all_questions}")
